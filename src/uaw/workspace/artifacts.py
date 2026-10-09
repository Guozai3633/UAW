"""Register text from a real complete model output; model assertions cannot self-register."""

import hashlib

from uaw.agent.contracts import identifier, validate_decision
from uaw.agent.ports import AgentSourcePort
from uaw.agent.sources import check_pin
from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.db.transactions import timestamp
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import reject
from uaw.workspace.artifact_repository import ArtifactRepository


class TextArtifacts:
    def __init__(self, repository: ArtifactRepository, sources: AgentSourcePort) -> None:
        self.repository, self.sources = repository, sources

    async def from_model(
        self,
        output_ref: Ref,
        observations: tuple[Ref, ...],
        ctx: TrustedExecutionContext,
        *,
        format_kind: str = "markdown",
    ) -> Ref:
        view = await self.sources.current(ctx)
        row = await self.repository.records.get(ctx.principal, "model.outputs", output_ref.id)
        check_pin(output_ref, "content", row.resource_id, row.revision, row.payload)
        model = row.payload
        if (
            row.schema_name != "ModelOutput"
            or model["finish_reason"] != "stop"
            or not model["text_complete"]
            or model["tool_calls"]
        ):
            raise reject(
                "artifact_model_incomplete", "Artifact requires a complete actual model output", 412
            )
        attempt = await self.repository.records.get(
            ctx.principal, "model.attempts", model["attempt_id"]
        )
        invocation = await self.repository.records.get(
            ctx.principal, "model.invocations", attempt.payload["invocation_id"]
        )
        if ctx.model_policy_ref is None:
            raise reject("artifact_model_unowned", "Fixed model policy is required", 403)
        if (
            invocation.payload["run_id"] != ctx.run_id
            or invocation.payload["state"] != "finished"
            or invocation.payload.get("result", {}).get("payload") != model
            or model["actual_config"]["policy_ref"] != ctx.model_policy_ref.wire()
        ):
            raise reject(
                "artifact_model_unowned", "Output is not a finished invocation of this Run", 403
            )
        decision = validate_decision(model["structured_data"])
        if (
            decision["action"] not in ("respond", "propose_completion")
            or not decision["text"].strip()
        ):
            raise reject("artifact_text_missing", "No final text in the actual model output", 412)
        if format_kind not in ("text", "markdown"):
            raise reject("artifact_format_unavailable", "Only text/Markdown is supported", 422)
        raw = decision["text"].encode("utf-8")
        if len(raw) > 65536:
            raise reject("artifact_too_large", "Artifact exceeds 64 KiB", 413)
        content_hash = await self.repository.blobs.put(ctx.principal, raw)
        if content_hash != hashlib.sha256(raw).hexdigest():
            raise reject("artifact_content_invalid", "Blob store returned an invalid digest", 412)
        key = identifier(
            "artifact-", {"run": ctx.run_id, "output": output_ref.wire(), "format": format_kind}
        )
        frame = Ref(
            kind="task_frame",
            id=view.frame["task_id"],
            version=str(view.frame["revision"]),
            content_hash=parameter_hash(view.frame),
        )
        value = {
            "id": key,
            "version": "1",
            "title": "Task result",
            "format_kind": format_kind,
            "media_type": "text/markdown; charset=utf-8"
            if format_kind == "markdown"
            else "text/plain; charset=utf-8",
            "content_ref": {
                "kind": "blob",
                "id": content_hash,
                "version": "1",
                "content_hash": content_hash,
            },
            "size_bytes": len(raw),
            "content_hash": content_hash,
            "provenance_refs": [output_ref.wire(), *[o.wire() for o in observations]],
            "verification_refs": [],
            "created_at": timestamp(),
        }
        # Timestamp is part of immutable data; recovery uses the original record.
        from uaw.shared.stores import StoreMissing

        try:
            previous = await self.repository.records.get(ctx.principal, "workspace.artifacts", key)
        except StoreMissing:
            previous = None
        if previous is not None:
            value["created_at"] = previous.payload["created_at"]
        if (await self.sources.current(ctx)).frame != view.frame:
            raise reject("artifact_frame_changed", "Task changed during artifact registration", 412)
        pin = await self.repository.register(
            value,
            {
                "context": ctx.wire(),
                "frame_ref": frame.wire(),
                "model_output_ref": output_ref.wire(),
                "observation_refs": [o.wire() for o in observations],
            },
            ctx,
        )
        await self.repository.read(pin, ctx)
        if (await self.sources.current(ctx)).frame != view.frame:
            raise reject("artifact_frame_changed", "Task changed before artifact publication", 412)
        return pin
