"""Actual pure calculations and verifiers; no controlled LLM selection claim."""

import hashlib
from copy import deepcopy
from decimal import getcontext, setcontext

import pytest

from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.shared.schema import validate_contract
from uaw.tool.invocation.schema import normalize
from uaw.tool.providers.arithmetic import ArithmeticVerifier, arithmetic_spec, calculate
from uaw.tool.providers.json_data import JsonDataVerifier, inspect_json, json_data_spec
from uaw.tool.registry import ToolRegistry
from uaw.tool.schema import compile_schema

PROVIDER = Ref(kind="provider", id="local-office", version="1")


@pytest.mark.parametrize(
    "op,operands,value",
    [
        ("add", ["0.1", "0.2"], "0.3"),
        ("add", ["1.00", "2.0", "3"], "6.00"),
        ("subtract", ["10", "3", "2"], "5"),
        ("multiply", ["-2", "1.25", "4"], "-10.00"),
        ("divide", ["1", "8"], "0.125"),
        ("percent", ["200", "12.5"], "25.0"),
        ("percent", ["-100", "0"], "-0"),
        ("add", ["-0", "0"], "0"),
    ],
)
def test_actual_decimal_operations(op, operands, value):
    data = calculate({"operation": op, "operands": operands})
    assert data == {
        "value": value,
        "precision": 34,
        "rounding": "ROUND_HALF_EVEN",
        "rounded": False,
        "inexact": False,
    }
    compile_schema(arithmetic_spec(PROVIDER)["output_schema"]).validate(data)


def test_decimal_rounding_and_ambient_context_are_explicit():
    before = getcontext().copy()
    try:
        getcontext().prec = 2
        getcontext().rounding = "ROUND_UP"
        for signal in getcontext().traps:
            getcontext().traps[signal] = False
        value = calculate({"operation": "divide", "operands": ["1", "3"]})
        assert value["value"] == "0." + "3" * 34
        assert value["rounded"] and value["inexact"]
        assert getcontext().prec == 2
    finally:
        setcontext(before)


@pytest.mark.parametrize(
    "args",
    [
        {},
        {"operation": "eval", "operands": ["1", "2"]},
        {"operation": "add", "operands": ["1"]},
        {"operation": "divide", "operands": ["1", "2", "3"]},
        {"operation": "percent", "operands": ["1", "2", "3"]},
        {"operation": "divide", "operands": ["1", "-0.00"]},
        {"operation": "multiply", "operands": ["9" * 64] * 32},
        {"operation": "add", "operands": ["1", "2"], "script": "anything"},
        {"operation": "add", "operands": ["1"] * 33},
        {"operation": "add", "operands": ("1", "2")},
    ],
)
def test_invalid_operation_and_bounds(args):
    with pytest.raises(ValueError):
        calculate(args)


@pytest.mark.parametrize(
    "bad",
    [
        "NaN",
        "Infinity",
        "-Inf",
        "1e100000",
        "1E2",
        "+1",
        "01",
        ".1",
        "1.",
        " 1",
        "1 ",
        "١",
        "1+2",
        "__import__('os')",
        "9" * 65,
        1,
        True,
        None,
    ],
)
def test_arithmetic_never_coerces_or_executes(bad):
    with pytest.raises(ValueError):
        calculate({"operation": "add", "operands": ["1", bad]})


@pytest.mark.parametrize(
    "text,kind,count,depth",
    [
        ('{"a":1,"b":[true,null]}', "object", 2, 2),
        ("[1,2]", "array", 2, 1),
        ('"exact"', "string", 1, 0),
        ("1.23", "number", 1, 0),
        ("true", "boolean", 1, 0),
        ("null", "null", 1, 0),
        ("{}", "object", 0, 1),
        ("[]", "array", 0, 1),
    ],
)
def test_actual_json_structure(text, kind, count, depth):
    data = inspect_json({"text": text})
    assert (data["root_type"], data["count"], data["depth"]) == (kind, count, depth)
    assert data["sha256"] == hashlib.sha256(text.encode()).hexdigest()
    compile_schema(json_data_spec(PROVIDER)["output_schema"]).validate(data)


def test_required_keys_preserve_names_and_missing_order():
    text = ' {" z ": 1, "a": 2}\r\n'
    data = inspect_json({"text": text, "required_keys": [" z ", "z", "missing"]})
    assert data["keys"] == [" z ", "a"] and data["missing_keys"] == ["z", "missing"]
    assert data["nodes"] == 5 and data["utf8_bytes"] == len(text.encode())


@pytest.mark.parametrize(
    "text",
    [
        '{"a":1,"a":2}',
        '{"a":1,"\\u0061":2}',
        '{"x":{"a":1,"a":2}}',
        "NaN",
        "Infinity",
        "-Infinity",
        "[1e999]",
        "1e" + "9" * 30,
        "[" * 17 + "0" + "]" * 17,
        "[" + ",".join(["0"] * 257) + "]",
        "[" + ",".join(["[" + ",".join(["0"] * 256) + "]"] * 4) + "]",
        '{"' + "x" * 257 + '":1}',
        '"\\ud800"',
        '{"\\udfff":1}',
        '"' + "原" * 6000 + '"',
        "",
        "{",
        "{} trailing",
        "01",
    ],
    ids=lambda value: "bounded-input-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:8],
)
def test_json_rejects_unsafe_or_oversized_data(text):
    with pytest.raises(ValueError):
        inspect_json({"text": text})


@pytest.mark.parametrize(
    "args",
    [
        {"text": 1},
        {"text": "{}", "unknown": True},
        {"text": "[]", "required_keys": []},
        {"text": "{}", "required_keys": ["a", "a"]},
        {"text": "{}", "required_keys": [1]},
        {"text": "{}", "required_keys": ["x" * 257]},
        {"text": "{}", "required_keys": [str(n) for n in range(65)]},
    ],
)
def test_required_keys_and_input_are_bounded(args):
    with pytest.raises(ValueError):
        inspect_json(args)


def test_json_strings_do_not_count_as_nesting_and_boundary_is_accepted():
    assert inspect_json({"text": '"[[[[}}}}\\\\\\""'})["depth"] == 0
    assert inspect_json({"text": "[" * 16 + "0" + "]" * 16})["depth"] == 16


@pytest.mark.parametrize(
    "factory,verifier,args,calculator",
    [
        (
            arithmetic_spec,
            ArithmeticVerifier,
            {"operation": "divide", "operands": ["1", "8"]},
            calculate,
        ),
        (
            json_data_spec,
            JsonDataVerifier,
            {"text": '{"a":1}', "required_keys": ["b"]},
            inspect_json,
        ),
    ],
)
async def test_exact_registered_binding_recomputed_output_and_tamper(
    ctx, factory, verifier, args, calculator
):
    spec = factory(PROVIDER)
    validate_contract("ToolSpec", spec)
    registry = ToolRegistry()
    registry.register(spec, expected_revision=0)
    raw = {
        "action_id": "office-action",
        "tool_ref": registry.reference(registry.snapshot()[1][0]),
        "arguments": args,
    }
    call = normalize(raw, registry)
    v = verifier(PROVIDER)
    data = calculator(args)
    await v.verify(data, call, spec, ctx)
    changed = {**data, "precision": 2} if factory == arithmetic_spec else {**data, "nodes": 999}
    with pytest.raises(DomainError):
        await v.verify(changed, call, spec, ctx)
    for field, value in [("version", "2"), ("content_hash", "0" * 64)]:
        bad = deepcopy(call)
        bad["tool_ref"][field] = value
        with pytest.raises(DomainError):
            await v.verify(data, bad, spec, ctx)
    bad = deepcopy(call)
    bad["arguments_hash"] = "0" * 64
    with pytest.raises(ValueError):
        await v.verify(data, bad, spec, ctx)
