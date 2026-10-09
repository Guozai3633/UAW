"""MS-C7 real SQL/FS baseline and candidate matrix; no Model HTTP/LLM claim."""

import asyncio
import json
import os
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import event

from tests.integration.context.registered_fixture import assemble
from tests.integration.context.test_assessment_chain_postgres import CountingReader
from tests.integration.context.test_assessment_postgres import ControlledAdvice
from tests.integration.context.test_registered_chain_postgres import ControlledSQLTools
from tests.integration.context.test_registered_postgres import (
    case as case,
)
from tests.integration.context.test_registered_postgres import (
    domain as domain,
)
from tests.integration.context.test_registered_postgres import (
    material,
    recipe,
    register_rule,
    rule,
)
from tests.integration.context.test_registered_postgres import (
    registration as registration,
)
from tests.integration.context.test_registered_postgres import (
    understanding as understanding,
)
from tests.unit.context.test_model_input import tool
from uaw.context.cache import PureComputationCache
from uaw.context.contracts import ModelToolSet
from uaw.context.model_input import GenericModelInputs


class SQLMeter:
    def __init__(self, records, reader, assessor):
        self.records, self.reader, self.assessor = records, reader, assessor
        self.gets, self.sql, self.phases = Counter(), 0, []
        self.actual_get = records.get

        async def get(principal, namespace, identifier, **kwargs):
            self.gets[namespace] += 1
            return await self.actual_get(principal, namespace, identifier, **kwargs)

        def cursor(*args):
            self.sql += 1

        self.cursor = cursor
        records.get = get
        event.listen(records.database.engine.sync_engine, "before_cursor_execute", cursor)

    async def run(self, name, operation):
        before, sql, reads, assessor = (
            self.gets.copy(),
            self.sql,
            self.reader.counts.copy(),
            self.assessor.calls,
        )
        started = time.perf_counter()
        result = "error"
        try:
            value = await operation
            result = "ok"
            return value
        finally:
            self.phases.append(
                dict(
                    boundary=name,
                    seconds=round(time.perf_counter() - started, 6),
                    record_get=sum((self.gets - before).values()),
                    namespaces=dict(self.gets - before),
                    sql_statement_round_trips=self.sql - sql,
                    reader=dict(self.reader.counts - reads),
                    assessor=self.assessor.calls - assessor,
                    result=result,
                )
            )

    def close(self):
        self.records.get = self.actual_get
        event.remove(self.records.database.engine.sync_engine, "before_cursor_execute", self.cursor)


@pytest.mark.parametrize("rule_count", [1, 2])
@pytest.mark.parametrize("with_tools", [False, True])
async def test_sql_read_measurement_matrix(registration, rule_count, with_tools):
    s = registration
    s.ctx = s.ctx.model_copy(
        update={
            "deadline": (datetime.now(UTC) + timedelta(minutes=55)).isoformat(),
            "operation_id": "measurement-build",
        }
    )
    assessor = ControlledAdvice()
    validator = ControlledSQLTools(s.records)
    s.inputs, s.components, _ = assemble(
        s.records,
        s.configuration,
        s.blob_directory,
        s.controller,
        current_runs=True,
        assessor=assessor,
        tool_validator=validator,
    )
    reader = CountingReader(s.inputs)
    s.components.sources.readers = dict.fromkeys(
        ("input", "content", "rule", "configuration"), reader
    )
    meter = SQLMeter(s.records, reader, assessor)
    phase = os.environ.get("UAW_CONTEXT_COST_PHASE", "candidate")
    directory = Path(os.environ.get("UAW_CONTEXT_EVIDENCE_DIR", "tests/.artifacts/B/MS-C7"))
    await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
    try:

        async def prepare():
            mat = await material(s)
            pins = tuple(
                [
                    await register_rule(
                        s,
                        rule(
                            s,
                            id=f"cost-rule-{i}",
                            text=f"保留用户原文和来源；格式建议 {i}。",
                            level="user_current",
                        ),
                        name=f"cost-rule-registration-{i}",
                    )
                    for i in range(rule_count)
                ]
            )
            tools = ()
            if with_tools:
                definition = tool()
                await s.records.put(
                    s.ctx.principal,
                    "test.context.tool_specs",
                    definition["id"],
                    "ToolSpec",
                    definition,
                    expected_revision=0,
                    request_id="cost-tool",
                )
                tools = (definition,)
            return await recipe(
                s, (mat,), pins, tools=ModelToolSet(run_id=s.ctx.run_id, tools=tools)
            )

        saved, _ = await meter.run("fixture_registration_excluded", prepare())
        built = await meter.run("build", s.components.build(saved.request.wire(), s.ctx))
        assert built["kind"] == "ok", built
        cache = PureComputationCache(max_entries=128, max_bytes=2097152)
        model = GenericModelInputs(s.components.composer, cache=cache)
        cold = await meter.run("ModelInput-cold", model.resolve(built["output_refs"][0], s.ctx))
        warm = await meter.run("ModelInput-warm", model.resolve(built["output_refs"][0], s.ctx))
        assert cold == warm and cache.stats.hits > 0
        assert s.original["text"] in [m["content"] for m in cold.messages]
        assert bool(cold.tools) == with_tools and not s.case.requests
        report = dict(
            phase=phase,
            baseline="d8023eb07e1460961782f297697da7428f6ad247",
            rules=rule_count,
            nonempty_tools=with_tools,
            phases=meter.phases,
            messages=cold.messages,
            tools=cold.tools,
            tokens=cold.estimated_tokens,
            cache=dict(hits=cache.stats.hits, misses=cache.stats.misses),
            note=(
                "Actual PostgreSQL55433 and FS; SQL cursor executions, not TCP packets/"
                "BEGIN/pool pings. Controlled semantic advice and SQL ToolSpec checker; "
                "zero LLM HTTP."
            ),
        )
        await asyncio.to_thread(
            (directory / f"{phase}-rules{rule_count}-tools{int(with_tools)}.json").write_text,
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    finally:
        meter.close()
