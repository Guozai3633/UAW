"""Exact file contracts, real signature checks, full/partial and cursor evidence."""

import hashlib
from copy import deepcopy
from dataclasses import replace

import pytest

from tests.unit.tool.file_evidence_fixture import (
    WORKSPACE,
    make_evidence,
    resign_evidence,
)
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.tool.providers.file_read import file_arguments, verify_file_evidence
from uaw.tool.schema import canonical, canonical_result, compile_schema


def checked(ctx, evidence, call, spec, signatures):
    return verify_file_evidence(
        evidence,
        call,
        spec,
        ctx,
        signatures=signatures,
        provider_ref=Ref.model_validate(spec["provider_ref"]),
    )


@pytest.mark.parametrize(
    "location",
    [
        {"kind": "whole"},
        {"kind": "text_span", "start": 1, "end": 5},
        {"kind": "lines", "start": 2, "end": 2},
    ],
)
def test_actual_snapshot_exact_selection_and_whole_hash(ctx, location):
    _, call, spec, evidence, signatures = make_evidence(
        ctx, arguments={"workspace_ref": WORKSPACE.wire(), "path": "file.txt", "location": location}
    )
    data = checked(ctx, evidence, call, spec, signatures)
    assert data["content_hash"] == hashlib.sha256(evidence.snapshot).hexdigest()
    compile_schema(spec["output_schema"]).validate(data)


@pytest.mark.parametrize(
    "part",
    [
        "signature",
        "attempt",
        "owner",
        "workspace",
        "path",
        "hash",
        "text",
        "location",
        "cursor",
        "command_ref",
        "snapshot",
    ],
)
def test_signed_runner_ok_does_not_prove_content_or_binding(ctx, part):
    _, call, spec, e, signatures = make_evidence(ctx)
    data = deepcopy(e.receipt.payload["result"])
    if part in {"workspace", "path", "hash", "text", "location", "cursor"}:
        key = {"workspace": "workspace_ref", "hash": "content_hash", "cursor": "next_cursor"}.get(
            part, part
        )
        data[key] = (
            {"kind": "workspace", "id": "foreign", "version": "1"}
            if part == "workspace"
            else (
                {"kind": "text_span", "start": 0, "end": 1}
                if part == "location"
                else "bad"
                if part != "hash"
                else "0" * 64
            )
        )
        e = resign_evidence(e, data, signatures)
    elif part == "signature":
        e = replace(e, receipt=e.receipt.model_copy(update={"signature": "bad"}))
    elif part == "attempt":
        e = replace(e, receipt=e.receipt.model_copy(update={"attempt_id": "foreign"}))
    elif part == "owner":
        e = replace(
            e,
            source=replace(
                e.source, owner=ctx.principal.model_copy(update={"auth_session_id": "foreign"})
            ),
        )
    elif part == "command_ref":
        e = replace(e, command_ref=e.command_ref.model_copy(update={"content_hash": "0" * 64}))
    else:
        e = replace(e, snapshot=b"current changed file")
    with pytest.raises((DomainError, ValueError)):
        checked(ctx, e, call, spec, signatures)


@pytest.mark.parametrize(
    "text", ["a" * 65536, "\n" * 65536, "原" * 21845], ids=["ascii-64k", "escaped-64k", "utf8-64k"]
)
def test_64k_bytes_result_envelope_is_explicit_and_default_bounds_remain(ctx, text):
    _, call, spec, e, signatures = make_evidence(ctx, text=text)
    data = checked(ctx, e, call, spec, signatures)
    result = {
        "call_ref": {"kind": "tool_call", "id": "call", "version": "1"},
        "status": "succeeded",
        "effect_state": "confirmed",
        "data": data,
        "output_refs": [],
        "usage_ref": {"kind": "usage", "id": "usage", "version": "1"},
    }
    assert canonical_result(result)
    with pytest.raises(ValueError):
        canonical(result)


@pytest.mark.parametrize("path", ["../x", "/x", "C:/x", "a/../x", "a//x", "a/./x", "x.", "x "])
def test_only_canonical_relative_file_paths(ctx, path):
    _, call, spec, _, _ = make_evidence(ctx)
    call["arguments"]["path"] = path
    from uaw.tool.schema import digest

    call["arguments_hash"] = digest(call["arguments"])
    with pytest.raises(ValueError):
        file_arguments(
            call,
            spec,
            Ref.model_validate(spec["provider_ref"]),
        )


def test_original_cursor_registry_and_actual_snapshot_needed(ctx):
    args = {"workspace_ref": WORKSPACE.wire(), "path": "file.txt", "cursor": "original-page-2"}
    _, call, spec, e, signatures = make_evidence(ctx, arguments=args, text="abcdef")
    data = {**e.receipt.payload["result"], "text": "cde", "next_cursor": "original-page-3"}
    e = resign_evidence(e, data, signatures)
    e = replace(
        e, selection={"kind": "text_span", "start": 2, "end": 5}, next_cursor="original-page-3"
    )
    assert checked(ctx, e, call, spec, signatures)["text"] == "cde"
    e = replace(e, next_cursor="original-page-2")
    with pytest.raises(DomainError):
        checked(ctx, e, call, spec, signatures)


def test_current_key_revocation_and_foreign_project_rejected(ctx):
    _, call, spec, e, signatures = make_evidence(ctx)
    signatures.revoked = True
    with pytest.raises(DomainError):
        checked(ctx, e, call, spec, signatures)
    signatures.revoked = False
    foreign = ctx.model_copy(
        update={"scope": ctx.scope.model_copy(update={"project_id": "foreign"})}
    )
    with pytest.raises(DomainError):
        checked(foreign, e, call, spec, signatures)


@pytest.mark.parametrize("text", ["bad\x00binary", "bad\x1bescape", "bad\x7fcontrol"])
def test_signed_utf8_control_snapshot_cannot_masquerade_as_plain_file(ctx, text):
    _, call, spec, e, signatures = make_evidence(ctx, text=text)
    with pytest.raises(ValueError):
        checked(ctx, e, call, spec, signatures)


@pytest.mark.parametrize(
    "selection",
    [
        {"kind": "text_span", "start": 1, "end": 3},
        {"kind": "text_span", "start": 0, "end": 100},
    ],
)
def test_independently_registered_page_still_constrained_to_original_range(ctx, selection):
    _, call, spec, e, signatures = make_evidence(ctx, text="abcdef")
    e = replace(e, selection=selection, next_cursor="registered-next")
    with pytest.raises(ValueError):
        checked(ctx, e, call, spec, signatures)
