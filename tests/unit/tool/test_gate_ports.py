"""Controlled gate responses only: no real approvals, budget, LLM, SQL or Runner."""

from uaw.tool.facade import ToolFacade


class PrecheckFixture:
    def __init__(self, *, waiting=False, approval=False, mutation=False, after=None):
        self.waiting, self.approval, self.mutation, self.after = waiting, approval, mutation, after
        self.calls = 0

    async def precheck(self, call, spec, ctx):
        self.calls += 1
        if self.after:
            self.after()
        if self.mutation:
            call["arguments"]["count"] = 99
        if self.waiting:
            return {
                "kind": "waiting",
                "output_refs": [],
                "wait_ref": {"kind": "approval", "id": "fixture-wait", "version": "1"},
            }
        return {
            "kind": "ok",
            "output_refs": [],
            "payload": {
                "allowed": True,
                "approval_required": self.approval,
                "policy_ref": ctx.capability_policy_ref.wire(),
                "resource_refs": [],
                "violations": [],
            },
        }


class RecheckFixture:
    def __init__(self, *, stale=False):
        self.calls, self.stale = 0, stale

    async def recheck(self, call, spec, precheck, ctx):
        self.calls += 1
        if self.stale:
            return {
                "kind": "stale",
                "output_refs": [],
                "failure": {
                    "code": "approval_stale",
                    "category": "conflict",
                    "message": "Resource changed",
                    "retryable": False,
                    "failed_phase": "recheck",
                },
            }
        return {
            "kind": "ok",
            "output_refs": [],
            "payload": {
                "allowed": True,
                "validated_call_ref": {"kind": "tool_call", "id": "fixture-call", "version": "1"},
                "resource_refs": [],
                "reason": "Controlled response; not real authorization",
            },
        }


async def test_verifiable_wait_propagated_and_changed_parameters_conflict(
    registry, access, call, ctx
):
    before, after = PrecheckFixture(waiting=True), RecheckFixture()
    facade = ToolFacade(registry, access, precheck=before, recheck=after)
    first = await facade.invoke(call, ctx)
    assert first["kind"] == "waiting" and first["wait_ref"]["id"] == "fixture-wait"
    assert after.calls == 0
    duplicate = await facade.invoke(call, ctx.model_copy(update={"attempt_id": "attempt-2"}))
    assert duplicate == first
    changed = {**call, "arguments": {**call["arguments"], "count": 3}}
    assert (await facade.invoke(changed, ctx))["failure"]["code"] == "action_conflict"


async def test_approved_ports_still_do_not_dispatch_and_stale_recheck_propagates(
    registry, access, call, ctx
):
    before, after = PrecheckFixture(), RecheckFixture()
    facade = ToolFacade(registry, access, precheck=before, recheck=after)
    result = await facade.invoke(call, ctx)
    assert result["failure"]["code"] == "dependency_unavailable"
    assert result["failure"]["failed_phase"] == "dispatch"
    assert before.calls == after.calls == 1
    after.stale = True
    assert (await facade.invoke(call, ctx))["failure"]["code"] == "approval_stale"


async def test_missing_approval_recheck_or_invalid_wait_are_not_success(
    registry, access, call, ctx
):
    for before, phase in (
        (PrecheckFixture(approval=True), "approval"),
        (PrecheckFixture(), "recheck"),
    ):
        result = await ToolFacade(registry, access, precheck=before).invoke(call, ctx)
        assert result["failure"]["failed_phase"] == phase

    class InvalidWait:
        async def precheck(self, call, spec, ctx):
            return {"kind": "waiting", "output_refs": []}

    result = await ToolFacade(registry, access, precheck=InvalidWait()).invoke(call, ctx)
    assert result["kind"] == "failed"


async def test_mutation_and_revocation_during_await_never_reach_recheck(
    registry, access, call, ctx
):
    before, after = PrecheckFixture(mutation=True), RecheckFixture()
    result = await ToolFacade(registry, access, precheck=before, recheck=after).invoke(call, ctx)
    assert result["failure"]["code"] == "action_conflict" and after.calls == 0
    before = PrecheckFixture(after=lambda: access.changes.update(cancelled=True))
    result = await ToolFacade(registry, access, precheck=before, recheck=after).invoke(call, ctx)
    assert result["kind"] == "cancelled" and after.calls == 0


async def test_gate_receives_effect_from_spec_and_recheck_revocation_is_live(
    registry, spec, binding, access, call, ctx
):
    spec["effect"] = "external_write"
    writes = type(registry)()
    writes.register(spec, expected_revision=0, binding=binding)
    call["tool_ref"] = writes.reference(writes.snapshot()[1][0])

    class InspectPrecheck(PrecheckFixture):
        async def precheck(self, validated, trusted_spec, trusted_ctx):
            assert trusted_spec["effect"] == "external_write"
            assert "effect" not in validated
            assert trusted_ctx.model_policy_ref == ctx.model_policy_ref
            return await super().precheck(validated, trusted_spec, trusted_ctx)

    class RevokingRecheck(RecheckFixture):
        async def recheck(self, validated, trusted_spec, decision, trusted_ctx):
            access.changes = {"denied_capabilities": frozenset({"content.read"})}
            return await super().recheck(validated, trusted_spec, decision, trusted_ctx)

    result = await ToolFacade(
        writes, access, precheck=InspectPrecheck(), recheck=RevokingRecheck()
    ).invoke(call, ctx)
    assert result["kind"] == "denied"
