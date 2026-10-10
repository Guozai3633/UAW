"""Controlled bridge metadata; real file evidence crypto and exact routing, no dispatch."""

from types import SimpleNamespace

import pytest

from tests.unit.tool.file_evidence_fixture import WORKSPACE, make_evidence
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError
from uaw.tool.providers.file_store import (
    FileReadExecutor,
    FileReadVerifier,
    FileReceiptStore,
    FileResourceReader,
)
from uaw.tool.providers.multiplex import ToolExecutorBinding, ToolExecutorRouter
from uaw.tool.schema import canonical


class ControlledBridge:
    def ready(self):
        pass

    async def resolve(self, call, spec, ctx):
        return (WORKSPACE,)


def store(ctx, *, bridge=None, signatures=None):
    _, call, spec, evidence, actual = make_evidence(ctx)
    source = FileReceiptStore(
        None,
        None,
        provider_ref=Ref.model_validate(spec["provider_ref"]),
        provider=Principal(
            kind="service", id="file-service", auth_session_id="controlled-file-session"
        ),
        bridge=bridge,
        signatures=signatures,
    )
    return source, call, spec, evidence, actual


@pytest.mark.parametrize("missing", ["bridge", "signatures"])
def test_missing_actual_sources_refused_synchronously(ctx, missing):
    source, call, spec, _, signatures = store(ctx)
    source.bridge = None if missing == "bridge" else ControlledBridge()
    source.signatures = None if missing == "signatures" else signatures
    executor = FileReadExecutor(source, provider=source.provider)
    with pytest.raises(DomainError) as error:
        executor.check(call, spec)
    assert error.value.failure.code == "dependency_unavailable"


@pytest.mark.parametrize("change", ["hash", "version", "provider"])
def test_finite_exact_router_refuses_changed_file_binding(ctx, change):
    source, call, spec, _, signatures = store(ctx, bridge=ControlledBridge())
    source.signatures = signatures
    executor = FileReadExecutor(source, provider=source.provider)
    router = ToolExecutorRouter(
        (
            ToolExecutorBinding(
                Ref.model_validate(call["tool_ref"]), source.provider_ref, executor, executor.check
            ),
        )
    )
    router.check(call, spec)
    changed = {
        **call,
        "tool_ref": {
            **call["tool_ref"],
            change if change != "hash" else "content_hash": "2"
            if change == "version"
            else "0" * 64,
        },
    }
    if change == "provider":
        changed = call
        spec = {**spec, "provider_ref": {"kind": "provider", "id": "foreign", "version": "1"}}
    with pytest.raises((DomainError, ValueError)):
        router.check(changed, spec)


async def test_resource_reader_requires_current_workspace_in_scope(ctx):
    source, call, spec, _, _ = store(ctx)
    reader = FileResourceReader(source.provider_ref, ControlledBridge())
    with pytest.raises(DomainError):
        await reader.resolve(call, spec, ctx)
    allowed = ctx.model_copy(
        update={"scope": ctx.scope.model_copy(update={"resource_refs": (WORKSPACE,)})}
    )
    assert await reader.resolve(call, spec, allowed) == (WORKSPACE,)
    with pytest.raises(DomainError):
        await FileResourceReader(source.provider_ref).resolve(call, spec, allowed)


async def test_verifier_uses_original_snapshot_after_await_not_runner_ok(ctx):
    source, call, spec, evidence, signatures = store(ctx)

    async def binding(_):
        return call, spec

    async def original(_):
        return evidence

    verifier = FileReadVerifier(
        SimpleNamespace(
            provider_ref=source.provider_ref,
            signatures=signatures,
            binding=binding,
            original=original,
            data_bytes=source.data_bytes,
        )
    )
    actual = evidence.receipt.payload["result"]
    await verifier.verify(actual, call, spec, ctx)
    with pytest.raises(ValueError):
        await verifier.verify(
            {**actual, "text": "same signed Runner ok cannot prove this"}, call, spec, ctx
        )


def test_file_envelope_bound_does_not_expand_original_request_limit(ctx):
    source, _, _, _, _ = store(ctx)
    _, _, _, evidence, _ = make_evidence(ctx, text="\n" * 65536)
    actual = evidence.receipt.payload["result"]
    assert len(source.data_bytes(actual)) > 65536
    with pytest.raises(ValueError):
        canonical(actual)
    with pytest.raises(ValueError):
        source.data_bytes({**actual, "text": "原" * 22000})


def test_freeze_original_evidence_protects_nested_usage_and_file_content(ctx):
    from uaw.tool.providers.file_read import freeze_file_evidence

    _, _, _, e, _ = store(ctx)
    frozen = freeze_file_evidence(e)
    e.receipt.payload["result"]["text"] = "mutated by owning adapter"
    e.receipt.usage["resources"]["wall_time_ms"] = 999
    e.selection["kind"] = "lines"
    assert frozen.receipt.payload["result"]["text"] != e.receipt.payload["result"]["text"]
    assert frozen.receipt.usage["resources"]["wall_time_ms"] == 1
    assert frozen.selection == {"kind": "whole"}


def test_unknown_file_fee_has_no_implicit_zero_reservation_ceiling():
    from uaw.tool.providers.file_read import file_estimates

    with pytest.raises(DomainError) as error:
        file_estimates()
    assert error.value.failure.code == "dependency_unavailable"
    assert file_estimates(money_ceiling="0.05")["money"] == "0.05"
