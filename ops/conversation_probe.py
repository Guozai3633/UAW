"""Bounded actual-provider probe of the same background path used by the web app."""

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

from sqlalchemy import select

from uaw.composition import compose
from uaw.infrastructure.db.models import RecordRow
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.background import BackgroundAgent
from uaw.run.jobs import JOBS
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.settings import Settings


async def probe(args):
    settings = Settings.from_file(args.config).model_copy(
        update={
            "agent_execution_enabled": False,
            "installed_state_directory": None,
            "installed_workspace_id": None,
        }
    )
    if not settings.development_user_token:
        raise ValueError("Protected development user required")
    actor = Principal(
        id=settings.development_principal_id,
        kind="user",
        auth_session_id="session-"
        + hashlib.sha256(settings.development_user_token.get_secret_value().encode()).hexdigest()[
            :24
        ],
    )
    control = compose(settings)
    target = args.report
    target.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "status": "started",
        "phases": [],
        "attempts": [],
        "source_hashes": {},
    }
    for name in (
        "src/uaw/agent/conversation.py",
        "src/uaw/agent/conversation_context.py",
        "src/uaw/run/conversation_entry.py",
        "src/uaw/run/background.py",
        "src/uaw/resources/prompts/conversation-v1.txt",
    ):
        report["source_hashes"][name] = hashlib.sha256(
            await asyncio.to_thread(Path(name).read_bytes)
        ).hexdigest()
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream)

    def save():
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def meta(name):
        return RequestMeta(request_id=name + "-" + uuid4().hex, schema_version="0.1")

    run = None
    started = monotonic()
    try:
        await control.start()
        driver = BackgroundAgent(control)
        queue = await driver.prepare()
        assert control.records and control.run_service
        records, runs = control.records, control.run_service
        async with records.database.sessions() as sql:
            active = await sql.scalar(
                select(RecordRow.resource_id)
                .where(
                    RecordRow.principal_id == actor.id,
                    RecordRow.namespace == JOBS,
                    RecordRow.deleted.is_(False),
                    RecordRow.payload["state"].as_string().in_(("queued", "working", "waiting")),
                )
                .limit(1)
            )
        if active:
            raise ValueError("Existing original jobs require their owning recovery; probe stopped")
        conversation = await runs.create_conversation(
            actor,
            {
                "title": "H02 engineering sample",
                "model_choice": {"mode": "explicit", "model_id": args.model_id},
                "memory_policy": {
                    "revision": 0,
                    "read_enabled": False,
                    "contribute_enabled": False,
                    "scope": {"resource_refs": []},
                },
            },
            meta("conversation-probe-create"),
        )

        async def enqueue(tx, admitted):
            await queue.enqueue(tx, admitted, actor)

        run = await runs.submit(
            actor,
            {
                "conversation_id": conversation["id"],
                "text": args.text_file.read_text(encoding="utf-8"),
                "attachment_refs": [],
            },
            meta("conversation-probe-submit"),
            on_admitted=enqueue,
        )
        report.update(run_id=run["id"], conversation_id=conversation["id"])
        save()
        for _ in range(8):
            t = monotonic()
            assert await queue.tick()
            job = (await records.get(actor, JOBS, run["id"])).payload
            report["phases"].append(
                {
                    "stage": job["stage"],
                    "state": job["state"],
                    "elapsed_ms": round((monotonic() - t) * 1000),
                    "failure": job.get("failure"),
                }
            )
            save()
            if job["state"] in ("finished", "blocked", "waiting"):
                break
        current = await runs.get_run(actor, run["id"])
        async with records.database.sessions() as sql:
            rows = list(
                await sql.scalars(
                    select(RecordRow).where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.deleted.is_(False),
                        (RecordRow.payload["run_id"].as_string() == run["id"])
                        | (RecordRow.payload["run_ref"]["id"].as_string() == run["id"]),
                    )
                )
            )
        for row in rows:
            if row.namespace == "model.attempts":
                report["attempts"].append(row.payload)
        report.update(
            status=current["status"],
            outcome=current.get("outcome"),
            elapsed_ms=round((monotonic() - started) * 1000),
            messages=[
                r.payload
                for r in rows
                if r.namespace == "items" and r.payload["type"] == "agent_message"
            ],
            decisions=[r.payload for r in rows if r.namespace == "agent.conversation.decisions"],
        )
        report["ledger"] = (await records.get(actor, "budget.ledgers", run["id"])).payload
        report["formal_artifacts_created"] = False
        async with records.database.sessions() as sql:
            refs = list(
                await sql.scalars(
                    select(RecordRow.payload).where(
                        RecordRow.principal_id == actor.id,
                        RecordRow.namespace == "tasks",
                        RecordRow.resource_id == run["task_id"],
                        RecordRow.deleted.is_(False),
                    )
                )
            )
        report["formal_artifacts_created"] = bool(refs and refs[0]["artifact_refs"])
        save()
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "outcome": report["outcome"],
                    "elapsed_ms": report["elapsed_ms"],
                    "attempts": len(report["attempts"]),
                    "actions": [d["decision"]["action"] for d in report["decisions"]],
                    "phases": report["phases"],
                    "usage": [a.get("usage") for a in report["attempts"]],
                    "artifacts_created": report["formal_artifacts_created"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if report["status"] in ("completed", "waiting_for_user") else 1
    except Exception as exc:
        report.update(
            status="probe_stopped",
            error_type=type(exc).__name__,
            error_code=getattr(getattr(exc, "failure", None), "code", None),
        )
        save()
        print(
            json.dumps(
                {
                    "status": "probe_stopped",
                    "error_type": report["error_type"],
                    "error_code": report["error_code"],
                }
            )
        )
        return 1
    finally:
        await control.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--text-file", type=Path, required=True)
    parser.add_argument("--model-id", default="deepseek-flash")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(probe(args), loop_factory=control_plane_loop))
