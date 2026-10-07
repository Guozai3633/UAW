"""Explicit fixed-model diagnostic using protected development settings; no automatic Agent loop."""

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from uaw.composition import compose
from uaw.context.seed import StoredModelInputs
from uaw.infrastructure.db.transactions import reference
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.model.gateway import request_meta
from uaw.shared.contracts import Principal, Ref, Scope, TrustedExecutionContext
from uaw.shared.errors import DomainError
from uaw.shared.settings import ConfigurationError, Settings

ROOT = Path(__file__).resolve().parents[1]


async def probe(args: argparse.Namespace) -> int:
    settings = Settings.from_file(args.config)
    if not settings.development_user_token:
        raise ConfigurationError("A protected development user identity is required")
    container = compose(settings)
    try:
        await container.start()
        if not (
            container.run_service
            and container.configuration
            and container.records
            and container.blobs
            and container.model_service
        ):
            raise ConfigurationError("Database and model protocol runtime are required")
        actor = Principal(
            id=settings.development_principal_id, kind="user", auth_session_id="local-model-probe"
        )
        run = container.run_service
        with args.text_file.open("rb") as stream:
            original_bytes = stream.read(65537)
        if len(original_bytes) > 65536:
            raise ConfigurationError("Prompt exceeds the diagnostic input limit")
        text = original_bytes.decode("utf-8")  # Preserve original CRLF and whitespace.
        if args.conversation_id:
            conversation_id = args.conversation_id
        else:
            conversation = await run.create_conversation(
                actor,
                {
                    "title": "Model connection check",
                    "model_choice": {"mode": "explicit", "model_id": args.model_id},
                    "memory_policy": {
                        "revision": 0,
                        "read_enabled": False,
                        "contribute_enabled": False,
                        "scope": {"resource_refs": []},
                    },
                },
                request_meta("probe-conversation", args.request_id),
            )
            conversation_id = conversation["id"]
        record = await run.submit(
            actor,
            {"conversation_id": conversation_id, "text": text, "attachment_refs": []},
            request_meta("probe-submit", args.request_id),
        )
        await run.advance(
            actor,
            record["id"],
            "preparing",
            request_meta("probe-prepare", args.request_id).model_copy(
                update={"expected_revision": 1}
            ),
        )
        binding = (await container.records.get(actor, "run.bindings", record["id"])).payload
        config = await container.configuration.snapshot(binding["configuration_ref"])
        entry = await container.configuration.require_model(args.model_id, config)
        identity = hashlib.sha256(f"{record['id']}:{args.request_id}".encode()).hexdigest()
        provider_ref = entry["provider_ref"]
        provider = (
            await container.records.get(
                container.configuration.platform,
                "provider.configs",
                provider_ref["id"],
                revision=int(provider_ref["version"]),
            )
        ).payload
        policy_id = "probe-policy-" + identity
        await container.records.put(
            actor,
            "execution.policies",
            policy_id,
            "CapabilityPolicy",
            {
                "id": policy_id,
                "revision": 1,
                "allowed_capabilities": ["model.generate"],
                "denied_capabilities": [],
                "resource_scope": {"conversation_id": conversation_id},
                "network_allowlist": [urlsplit(provider["endpoint"]).hostname],
                "feature_flag_refs": [],
            },
            expected_revision=0,
            request_id="diagnostic-policy",
        )
        ctx = TrustedExecutionContext(
            principal=actor,
            scope=Scope(
                principal_id=actor.id,
                conversation_id=conversation_id,
                capabilities=("model.generate",),
            ),
            run_id=record["id"],
            conversation_id=conversation_id,
            operation_id="probe-operation-" + identity,
            trace_id="probe-trace-" + identity,
            attempt_id="probe-attempt-" + identity,
            deadline=record["budget"]["deadline"],
            capability_policy_ref=Ref.model_validate(reference("policy", policy_id)),
            model_policy_ref=Ref.model_validate(binding["model_policy_ref"]),
        )
        inputs = StoredModelInputs(container.records, container.blobs)
        snapshot = await inputs.seed(ctx, args.max_output_tokens)
        result = await container.model_service.generate(
            {
                "context_snapshot_ref": snapshot,
                "model_config": {
                    "model_id": args.model_id,
                    "catalog_revision": entry["revision"],
                    "provider_ref": entry["provider_ref"],
                    "policy_ref": binding["model_policy_ref"],
                    "max_output_tokens": args.max_output_tokens,
                },
                "output_protocol": "text",
                "attempt_id": ctx.attempt_id,
            },
            ctx,
        )
        print(
            json.dumps(
                {"conversation_id": conversation_id, "run_id": record["id"], "result": result},
                ensure_ascii=False,
            )
        )
        if result["kind"] != "ok":
            return 1
        output = result["payload"]
        assert isinstance(output, dict)
        content = output["content_ref"]
        assert isinstance(content, dict)
        receipt = {
            "date": datetime.now(UTC).isoformat(),
            "scope": "explicit_model_protocol_probe",
            "conversation_id": conversation_id,
            "run_id": record["id"],
            "actual_config": output["actual_config"],
            "attempt_id": output["attempt_id"],
            "usage": output["usage"],
            "output_content_hash": content["content_hash"],
            "finish_reason": output["finish_reason"],
            "task_semantic_completion": False,
        }
        # Private metadata only; no headers/credential or full prompt/output in this receipt.
        target = ROOT / ".data" / "model-probes" / f"{identity}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Protected probe metadata: {target}")
        return 0
    finally:
        await container.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "ops/database-development.toml")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--text-file", type=Path, required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--conversation-id")
    parser.add_argument("--max-output-tokens", type=int, default=512)
    args = parser.parse_args()
    try:
        return asyncio.run(probe(args), loop_factory=control_plane_loop)
    except DomainError as exc:
        print(
            json.dumps({"error": exc.failure.code, "message": exc.failure.message}), file=sys.stderr
        )
    except ConfigurationError, OSError:
        print(
            "Model probe configuration/input is unavailable; inspect local setup.", file=sys.stderr
        )
    except Exception as exc:
        print(
            f"Model probe could not finish ({type(exc).__name__}); inspect protected receipts.",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
