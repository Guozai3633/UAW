"""Disposable hidden D SQL process; inherited test DB only, no secret output."""

import asyncio
import json
import os
import sys

from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.session import Database
from uaw.infrastructure.db.transactions import TransactionalStore
from uaw.infrastructure.event_loop import control_plane_loop
from uaw.run.clock_ports import ClockChange
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.execution_clock import ExecutionClocks
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.errors import DomainError


async def main():
    request = json.loads(sys.stdin.read())
    db = Database(os.environ["UAW_TEST_DATABASE_URL"])
    try:
        actor = Principal.model_validate_json(json.dumps(request["actor"]))
        clocks = ExecutionClocks(
            PostgresRecordStore(db), effects=RunIdleEffects(), now=lambda: request["now"]
        )
        if request["mode"] == "read":
            result = (await clocks.current(actor, request["run"])).wire()
        else:

            async def change(tx):
                return (
                    await clocks.change(
                        tx, actor, request["run"], ClockChange(request["expected"], "active")
                    )
                ).wire()

            result = await TransactionalStore(db).execute(
                actor,
                request["aggregate"],
                RequestMeta(request_id=request["key"], schema_version="0.1"),
                {},
                change,
            )
        print(json.dumps({"kind": "ok", "clock": result}))
    except DomainError as exc:
        print(json.dumps({"kind": "denied", "status": exc.status_code, "code": exc.failure.code}))
    finally:
        await db.close()


if __name__ == "__main__":
    with asyncio.Runner(loop_factory=control_plane_loop) as runner:
        runner.run(main())
