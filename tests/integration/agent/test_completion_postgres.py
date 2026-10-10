"""Actual Model/Context/artifact/report/Run CAS; controlled HTTP does not prove quality."""

import asyncio
import json

import httpx
import pytest
from sqlalchemy import select

from tests.integration.agent.conftest import agent_case as agent_case
from tests.integration.agent.test_root_postgres import decision, request, start
from tests.integration.model.test_gateway import reply
from tests.integration.test_control_plane import meta
from uaw.agent.completion.assembly import assemble_completion_runtime
from uaw.agent.completion.delivery import BUNDLES, REPORTS, row_pin
from uaw.infrastructure.db.models import RecordRow
from uaw.run.deliveries import DeliveryReader
from uaw.shared.contracts import Principal, Ref
from uaw.shared.errors import DomainError


def review(requirements, state="passed", evidence_ids=None):
    return httpx.Response(
        200,
        json=reply(
            json.dumps(
                {
                    "verdicts": [
                        {
                            "requirement_id": r["id"],
                            "state": state,
                            "reason": "Controlled semantic verdict",
                            "evidence_ids": evidence_ids
                            if evidence_ids is not None
                            else ["artifact", "input-0"],
                            "limitations": [],
                        }
                        for r in requirements
                    ],
                    "limitations": [],
                }
            )
        ),
    )


async def deliver(
    p, *, acceptance=False, state="passed", text="Actual bounded task result", ids=None
):
    from uaw.agent.completion.contracts import contract_from_frame

    completion = assemble_completion_runtime(p.control, p.assembly, acceptance_required=acceptance)
    root = await start(p)
    raw, ctx = await request(p, root)
    current = await p.assembly.sources.current(ctx)
    contract = contract_from_frame(current.frame, acceptance_required=acceptance)
    p.model_case.responses[:] = [
        decision("propose_completion", text),
        review(contract["requirements"], state, ids),
    ]
    result = await p.assembly.runtime.step(raw, ctx)
    if result.get("failure", {}).get("code") == "agent_request_invalid":
        # Expose the original internal contract error without sending a new attempt.
        from uaw.agent.contracts import identifier

        operation = await p.assembly.repository.operation(
            identifier("agent-op-", {"agent": root.id, "operation": ctx.operation_id}), ctx
        )
        await p.assembly.runtime.loop.advance(operation, ctx)
    assert result["kind"] == "ok", result
    proposal = Ref.model_validate(result["output_refs"][0])
    row = await p.control.records.get(ctx.principal, BUNDLES, proposal.id)
    bundle = row_pin("content", row.resource_id, row.payload)
    return completion, proposal, bundle, ctx


async def test_delivery_read_after_completion_and_new_login_keeps_original_sources(agent_case):
    p = agent_case
    completion, proposal, bundle_ref, ctx = await deliver(p)
    run = await p.domain[1].get_run(ctx.principal, ctx.run_id)
    await completion.controller.complete(proposal, ctx, meta("history-complete", run["revision"]))
    reader = DeliveryReader(p.control.records, p.control.blobs)
    fresh = ctx.principal.model_copy(update={"auth_session_id": "new-authenticated-login"})
    view, saved = await reader.read(fresh, ctx.run_id)
    assert view["content"] == "Actual bounded task result"
    assert view["report"]["outcome"] == "succeeded" and not view["stale"]
    assert view["bundle_ref"] == bundle_ref.wire() and saved == ctx
    assert "context" not in view and "acceptance" not in view
    with pytest.raises(DomainError):
        await reader.read(
            Principal(id="another-user", kind="user", auth_session_id="another-login"), ctx.run_id
        )
    with pytest.raises(DomainError):
        await reader.artifact(fresh, view["artifact"]["id"], "999")
    with pytest.raises(DomainError):
        await completion.controller.accept(
            fresh,
            bundle_ref,
            Ref.model_validate(view["artifact_ref"]),
            "accept",
            saved,
            meta("new-login-accept"),
        )
    assert len(p.model_case.requests) == 2


async def test_delivery_http_returns_real_content_and_rejects_hash_or_acceptance(agent_case):
    from pydantic import SecretStr

    from uaw.api.application import create_app
    from uaw.shared.settings import Settings

    p = agent_case
    completion, _, _, ctx = await deliver(p, acceptance=True)
    p.control.run_service = p.domain[1]
    p.control.completion_controller = completion.controller
    p.control.settings = Settings(
        profile="development",
        development_principal_id=ctx.principal.id,
        development_user_token=SecretStr("u" * 40),
        cursor_signing_key=SecretStr("k" * 40),
    )
    reader = DeliveryReader(p.control.records, p.control.blobs)
    view, _ = await reader.read(ctx.principal, ctx.run_id)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(p.control)), base_url="http://test"
    ) as client:
        headers = {"Authorization": "Bearer " + "u" * 40}
        response = await client.get(f"/v1/runs/{ctx.run_id}/delivery", headers=headers)
        assert response.status_code == 200, response.json()
        assert response.json()["payload"] == view
        artifact = view["artifact"]
        content = await client.get(
            f"/v1/artifacts/{artifact['id']}/content",
            headers=headers,
            params={"version": artifact["version"], "content_hash": artifact["content_hash"]},
        )
        assert (
            content.status_code == 200 and content.json()["payload"]["content"] == view["content"]
        )
        bad = await client.get(
            f"/v1/artifacts/{artifact['id']}/content",
            headers=headers,
            params={"version": artifact["version"], "content_hash": "0" * 64},
        )
        assert bad.status_code == 412
        invalid = await client.post(
            f"/v1/runs/{ctx.run_id}/delivery/acceptance",
            headers=headers,
            json={
                "meta": meta("http-old-session-accept").wire(),
                "payload": {
                    "bundle_ref": view["bundle_ref"],
                    "artifact_ref": view["artifact_ref"],
                    "decision": "accept",
                },
            },
        )
        assert (
            invalid.status_code == 403
            and invalid.json()["failure"]["code"] == "completion_user_required"
        )
    current = await p.domain[1].get_run(ctx.principal, ctx.run_id)
    assert current["status"] != "completed" and len(p.model_case.requests) == 2


async def test_real_artifact_report_terminal_cas_event_and_restart_replay(agent_case):
    p = agent_case
    completion, proposal, bundle_ref, ctx = await deliver(p)
    bundle = await completion.coordinator.bundle(bundle_ref, ctx)
    artifact, text, _ = await completion.coordinator.artifacts.repository.read(
        Ref.model_validate(bundle["artifact_ref"]), ctx
    )
    assert text == "Actual bounded task result" and artifact["size_bytes"] == len(text.encode())
    run = await p.domain[1].get_run(ctx.principal, ctx.run_id)
    assert run["status"] != "completed"
    report = (await p.control.records.get(ctx.principal, REPORTS, proposal.id)).payload
    assert report["outcome"] == "succeeded"
    assert report["verdicts"] and all(v["evidence_refs"] for v in report["verdicts"])
    submissions = await asyncio.gather(
        *(
            completion.controller.complete(proposal, ctx, meta("complete", run["revision"]))
            for _ in range(4)
        )
    )
    final = submissions[0]
    assert all(value == final for value in submissions)
    assert final["status"] == "completed" and final["revision"] == run["revision"] + 1
    from uaw.run.completion import RunCompletionController

    restarted = RunCompletionController(completion.coordinator)
    assert await restarted.complete(proposal, ctx, meta("complete", run["revision"])) == final
    task = (await p.control.records.get(ctx.principal, "tasks", ctx.task_id)).payload
    assert bundle["artifact_ref"] in task["artifact_refs"] and not task["active_run_refs"]
    assert len(p.model_case.requests) == 2


async def test_user_acceptance_is_independent_and_binds_artifact_version(agent_case):
    p = agent_case
    completion, proposal, bundle_ref, ctx = await deliver(p, acceptance=True)
    run = await p.domain[1].get_run(ctx.principal, ctx.run_id)
    with pytest.raises(DomainError, match="Await authenticated user acceptance"):
        await completion.controller.complete(proposal, ctx, meta("before-accept", run["revision"]))
    bundle = await completion.coordinator.bundle(bundle_ref, ctx)
    artifact = Ref.model_validate(bundle["artifact_ref"])
    with pytest.raises(DomainError, match="another artifact"):
        await completion.controller.accept(
            ctx.principal,
            bundle_ref,
            artifact.model_copy(update={"version": "999"}),
            "accept",
            ctx,
            meta("wrong-accept", 0),
        )
    await completion.controller.accept(
        ctx.principal, bundle_ref, artifact, "accept", ctx, meta("actual-accept", 0)
    )
    assert (
        await completion.controller.complete(
            proposal, ctx, meta("accepted-complete", run["revision"])
        )
    )["status"] == "completed"


@pytest.mark.parametrize("state", ["failed", "not_run", "blocked"])
async def test_incomplete_semantic_result_cannot_submit_terminal_state(agent_case, state):
    completion, proposal, _, ctx = await deliver(agent_case, state=state)
    run = await agent_case.domain[1].get_run(ctx.principal, ctx.run_id)
    with pytest.raises(DomainError, match="not all passed"):
        await completion.controller.complete(proposal, ctx, meta("not-complete", run["revision"]))
    assert (await agent_case.domain[1].get_run(ctx.principal, ctx.run_id))["status"] != "completed"


async def test_unverified_web_citation_blocks_even_a_passing_model(agent_case):
    completion, proposal, _, ctx = await deliver(
        agent_case, text="Claim [source](https://example.org/unknown)."
    )
    report = (await agent_case.control.records.get(ctx.principal, REPORTS, proposal.id)).payload
    assert report["outcome"] == "blocked"
    assert any(
        c["id"] == "unresolved-web-links" and c["state"] == "not_run" for c in report["checks"]
    )


async def test_cancel_after_review_does_not_complete(agent_case):
    p = agent_case
    completion, proposal, _, ctx = await deliver(p)
    run = await p.domain[1].get_run(ctx.principal, ctx.run_id)
    await p.domain[1].control(
        ctx.principal,
        {
            "run_id": ctx.run_id,
            "control": {"mode": "cancel", "preserve_refs": [], "reason": "Stop"},
        },
        meta("cancel-reviewed", run["revision"]),
    )
    with pytest.raises(DomainError):
        await completion.controller.complete(
            proposal, ctx, meta("cancel-complete", run["revision"])
        )
    assert (await p.domain[1].get_run(ctx.principal, ctx.run_id))["status"] != "completed"


async def test_invented_semantic_evidence_fails_before_bundle(agent_case):
    p = agent_case
    completion = assemble_completion_runtime(p.control, p.assembly)
    root = await start(p)
    raw, ctx = await request(p, root)
    from uaw.agent.completion.contracts import contract_from_frame

    contract = contract_from_frame((await p.assembly.sources.current(ctx)).frame)
    p.model_case.responses[:] = [
        decision("propose_completion"),
        review(contract["requirements"], evidence_ids=["invented"]),
    ]
    result = await p.assembly.runtime.step(raw, ctx)
    assert result["kind"] != "ok"
    assert result["failure"]["code"] == "provider_structured_output_invalid"
    assert (await p.domain[1].get_run(ctx.principal, ctx.run_id))["status"] != "completed"
    assert completion.coordinator


async def test_unknown_model_receipt_and_user_revision_prevent_terminal_commit(agent_case):
    """Inject valid unresolved persisted receipts; do not claim real provider timeout."""
    p = agent_case
    completion, proposal, _, ctx = await deliver(p)
    run = await p.domain[1].get_run(ctx.principal, ctx.run_id)
    async with p.control.records.database.sessions() as session:
        row = await session.scalar(
            select(RecordRow)
            .where(
                RecordRow.principal_id == ctx.principal.id,
                RecordRow.namespace == "model.invocations",
                RecordRow.payload["run_id"].as_string() == ctx.run_id,
            )
            .limit(1)
        )
        assert row is not None
        original = dict(row.payload)
    original.update(id="unresolved-extra", operation_id="unresolved-extra", state="claimed")
    original.pop("result", None)
    await p.control.records.put(
        ctx.principal,
        "model.invocations",
        "unresolved-extra",
        "ModelInvocation",
        original,
        expected_revision=0,
        request_id="unknown-claim",
    )
    with pytest.raises(DomainError, match="invocation is unresolved"):
        await completion.controller.complete(proposal, ctx, meta("claimed-block", run["revision"]))
    original.update(
        state="finished",
        result={
            "kind": "failed",
            "failure": {
                "category": "unknown_effect",
                "code": "controlled_lost_reply",
            },
        },
    )
    await p.control.records.put(
        ctx.principal,
        "model.invocations",
        "unresolved-extra",
        "ModelInvocation",
        original,
        expected_revision=1,
        request_id="unknown-finished",
    )
    with pytest.raises(DomainError, match="invocation is unresolved"):
        await completion.controller.complete(proposal, ctx, meta("unknown-block", run["revision"]))
    await p.control.records.delete(
        ctx.principal,
        "model.invocations",
        "unresolved-extra",
        expected_revision=2,
        request_id="remove-test-injection",
    )
    from uaw.tool.invocation.schema import normalize

    registry = p.tools.facade.registry
    late_ctx = ctx.model_copy(update={"operation_id": "late-tool", "attempt_id": "late-tool"})
    late = normalize(
        {"tool_ref": p.tool_ref.wire(), "arguments": {"text": "late"}, "action_id": "late-tool"},
        registry,
    )
    await p.tools.ledger.bind(late, registry.get(p.tool_ref.wire()).spec(), late_ctx)
    with pytest.raises(DomainError) as changed:
        await completion.controller.complete(
            proposal, ctx, meta("late-tool-block", run["revision"])
        )
    assert changed.value.failure.code == "completion_activity_changed"
    state = await p.control.records.get(ctx.principal, "run.input_sets", ctx.run_id)
    await p.domain[1].append_requirement(
        ctx.principal,
        ctx.run_id,
        "Change the required output before completion.",
        meta("post-review-steer", state.revision),
    )
    with pytest.raises(DomainError):
        await completion.controller.complete(proposal, ctx, meta("stale-block", run["revision"]))
    assert (await p.domain[1].get_run(ctx.principal, ctx.run_id))["status"] != "completed"
