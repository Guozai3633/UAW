"""Pure schema memoization cannot become current-state or cross-task permission."""

import asyncio

import pytest

from uaw.shared import schema
from uaw.shared.schema import ContractViolation, contract_validation_scope, validate_contract


async def test_same_json_hits_but_mutation_and_wrong_schema_are_revalidated():
    value = {"id": "shape-user", "kind": "user", "auth_session_id": "shape-session"}
    async with contract_validation_scope() as scope:
        validate_contract("Principal", value)
        validate_contract("Principal", dict(reversed(list(value.items()))))
        assert (scope.hits, scope.misses) == (1, 1)
        value["approved"] = True
        with pytest.raises(ContractViolation) as invalid:
            validate_contract("Principal", value)
        assert invalid.value.paths and scope.hits == 1
        with pytest.raises(ContractViolation):
            validate_contract("Ref", {k: v for k, v in value.items() if k != "approved"})
        assert len(scope.entries) == 1
    assert not scope.entries and schema._shape_scope.get() is None


async def test_validator_replacement_cannot_reuse_old_success(monkeypatch):
    async with contract_validation_scope() as scope:
        validate_contract("ID", "shape-id")
        original = schema.validator("ID")
        changed = type(original)({"type": "integer"})
        get_validator = schema.validator
        monkeypatch.setattr(
            schema, "validator", lambda n: changed if n == "ID" else get_validator(n)
        )
        with pytest.raises(ContractViolation):
            validate_contract("ID", "shape-id")
        assert scope.hits == 0 and scope.misses == 2


async def test_nested_child_thread_and_later_scope_are_isolated():
    async with contract_validation_scope() as scope:
        validate_contract("ID", "shape-id")
        async with contract_validation_scope() as nested:
            assert nested is scope
            validate_contract("ID", "shape-id")

        async def child():
            # Inherited context alone is never a hit for this different task.
            validate_contract("ID", "shape-id")
            async with contract_validation_scope() as separate:
                assert separate is not scope
                validate_contract("ID", "shape-id")
                assert separate.misses == 1 and separate.hits == 0
            assert not separate.entries

        await asyncio.create_task(child())
        await asyncio.to_thread(validate_contract, "ID", "shape-id")
        assert scope.hits == 1 and scope.misses == 1
    async with contract_validation_scope() as later:
        validate_contract("ID", "shape-id")
        assert later.misses == 1 and later.hits == 0


async def test_failed_and_cancelled_scope_clears_all_digests():
    ready = asyncio.Event()
    captured = []

    async def owned():
        try:
            async with contract_validation_scope() as scope:
                captured.append(scope)
                validate_contract("ID", "shape-id")
                ready.set()
                await asyncio.Event().wait()
        finally:
            assert schema._shape_scope.get() is None

    task = asyncio.create_task(owned())
    await ready.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not captured[0].entries
    with pytest.raises(ContractViolation):
        async with contract_validation_scope() as failed:
            validate_contract("ID", "shape-id")
            validate_contract("ID", {})
    assert not failed.entries and schema._shape_scope.get() is None


async def test_entry_bound_and_unsupported_python_types_never_collide():
    assert schema._shape_bytes([1]) != schema._shape_bytes([True])
    assert schema._shape_bytes([1.0]) != schema._shape_bytes([1])
    assert schema._shape_bytes((1,)) is None
    assert schema._shape_bytes({1: "value"}) is None
    assert schema._shape_bytes({"value": float("nan")}) is None
    assert schema._shape_bytes("a" * 16385) is None
    assert schema._shape_bytes([0] * 2049) is None

    class CustomString(str):
        pass

    assert schema._shape_bytes(CustomString("shape-id")) is None
    cyclic = []
    cyclic.append(cyclic)
    assert schema._shape_bytes(cyclic) is None
    async with contract_validation_scope() as scope:
        for number in range(257):
            validate_contract("ID", f"shape-{number}")
        assert len(scope.entries) == 256
        validate_contract("ID", "shape-256")
        assert scope.misses == 258 and scope.hits == 0
        validate_contract("ID", CustomString("shape-0"))
        assert scope.misses == 259 and scope.hits == 0


async def test_each_invalid_attempt_retains_original_error_paths():
    invalid = {"id": "shape-id", "kind": "unknown", "auth_session_id": "shape-session"}
    with pytest.raises(ContractViolation) as baseline:
        validate_contract("Principal", invalid)
    async with contract_validation_scope() as scope:
        for _ in range(2):
            with pytest.raises(ContractViolation) as current:
                validate_contract("Principal", invalid)
            assert current.value.paths == baseline.value.paths
        assert scope.misses == 2 and not scope.entries
