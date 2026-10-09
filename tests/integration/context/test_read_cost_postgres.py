"""MS-C7 real SQL/FS baseline and candidate matrix; no Model HTTP/LLM claim."""

import asyncio
import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import event

from tests.integration.context.registered_fixture import assemble
from tests.integration.context.test_assessment_chain_postgres import CountingReader
from tests.integration.context.test_assessment_postgres import ControlledAdvice
from tests.integration.context.test_registered_chain_postgres import (
    ControlledSQLTools,
    CountingInputs,
)
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


class SQLMeter:
    def __init__(self, records, reader, assessor, inputs):
        self.records, self.reader, self.assessor = records, reader, assessor
        self.gets, self.sql, self.phases = Counter(), 0, []
        self.actual_get = records.get
        self.extra, self.timings = Counter(), Counter()
        self.restore = []
        for target, method, label in (
            (inputs.blobs, "get", "blob"),
            (inputs.runs, "read", "actual_run_reader"),
            (inputs.runs, "authorize", "current_authorize"),
            (reader, "read", "reader_read"),
            (reader, "check", "reader_check"),
            (assessor, "assess", "assessor"),
        ):
            actual = getattr(target, method)
            self.restore.append((target, method, actual))

            async def measured(*args, _actual=actual, _label=label, **kwargs):
                self.extra[_label] += 1
                started = time.perf_counter()
                try:
                    return await _actual(*args, **kwargs)
                finally:
                    self.timings[_label] += time.perf_counter() - started

            setattr(target, method, measured)

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
        extra, timings = self.extra.copy(), self.timings.copy()
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
                    io_calls=dict(self.extra - extra),
                    io_seconds_inclusive={
                        k: round(v - timings[k], 6) for k, v in self.timings.items()
                    },
                )
            )

    def close(self):
        for target, method, actual in self.restore:
            setattr(target, method, actual)
        self.records.get = self.actual_get
        event.remove(self.records.database.engine.sync_engine, "before_cursor_execute", self.cursor)


@pytest.mark.parametrize("rule_count", [1, 2])
@pytest.mark.parametrize("with_tools", [False, True])
async def test_sql_read_measurement_matrix(registration, rule_count, with_tools):
    s = registration
    constructor = None
    if os.environ.get("UAW_CONTEXT_FIXED_BASELINE") == "1":
        from uaw.context.registered import RegisteredContextInputs

        fixed_result = await asyncio.to_thread(
            subprocess.run,
            [
                "git",
                "show",
                "d8023eb07e1460961782f297697da7428f6ad247:src/uaw/context/registered.py",
            ],
            capture_output=True,
            check=True,
        )
        fixed = fixed_result.stdout.decode("utf-8")
        module = ModuleType("uaw.context._fixed_c7_baseline")
        sys.modules[module.__name__] = module
        exec(compile(fixed, "<published B baseline>", "exec"), module.__dict__)

        def constructor(**kwargs):
            assert not kwargs.pop("batch_required") and kwargs.pop("record_batch") is None
            return module.RegisteredContextInputs(**kwargs)
    else:
        from uaw.context.registered import RegisteredContextInputs

        constructor = RegisteredContextInputs
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
        inputs_type=constructor,
    )
    reader = CountingReader(s.inputs)
    s.components.sources.readers = dict.fromkeys(
        ("input", "content", "rule", "configuration"), reader
    )
    meter = SQLMeter(s.records, reader, assessor, s.inputs)
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
        model = CountingInputs(s.components.composer, cache=cache)
        cold = await meter.run("ModelInput-cold", model.resolve(built["output_refs"][0], s.ctx))
        cold_compute = model.calls
        warm = await meter.run("ModelInput-warm", model.resolve(built["output_refs"][0], s.ctx))
        assert cold == warm and cache.stats.hits > 0
        assert s.original["text"] in [m["content"] for m in cold.messages]
        assert bool(cold.tools) == with_tools and not s.case.requests
        report = dict(
            phase=phase,
            baseline="d8023eb07e1460961782f297697da7428f6ad247",
            record_strategy="sequential-get; no A SQL adapter",
            context_preparation_seconds=round(
                sum(
                    p["seconds"]
                    for p in meter.phases
                    if p["boundary"] in ("build", "ModelInput-cold")
                ),
                6,
            ),
            model_http_calls=0,
            rules=rule_count,
            nonempty_tools=with_tools,
            phases=meter.phases,
            messages=cold.messages,
            tools=cold.tools,
            tokens=cold.estimated_tokens,
            pure_format=dict(cold=cold_compute, warm=model.calls - cold_compute),
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
