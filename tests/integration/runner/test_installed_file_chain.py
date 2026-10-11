"""A8 original FileTool execution, actual OS/SQL/IPC; decisions controlled."""

from tests.integration.runner.installed_file_fixture import installed_file_case
from tests.integration.test_browser_sessions import web as web


async def test_a8_file_facade_approval_budget_actual_helper_read(web, tmp_path, monkeypatch):
    async with installed_file_case(web, tmp_path, monkeypatch) as p:
        await p.approve()
        assert p.metrics["sends"] == [] and (await p.child_metrics())["opens"] == 0
        async with p.phase("approved_facade_to_signed_result"):
            result = await p.bindings.tool.facade.invoke(p.raw, p.ctx)
        assert result["kind"] == "ok", result
        assert result["payload"]["status"] == "succeeded", result
        assert result["payload"]["effect_state"] == "confirmed", result
        original = await p.bindings.tool.receipts.read_observation(p.raw["action_id"], p.ctx)
        assert original.snapshot == "actual 中😀\r\nKeeṕ exact  ".encode()
        assert original.receipt.kind == "ok"
        assert original.source.owner == p.owner
        assert original.source.command.trusted_context == p.ctx
        assert original.source.command.trusted_context.model_policy_ref == p.ctx.model_policy_ref
        assert original.source.command.parameters == {
            "action": "file.read",
            "parameters": p.raw["arguments"],
        }
        assert original.receipt.attempt_id == p.ctx.attempt_id
        assert original.receipt_ref.kind == "content" and original.receipt_ref.version == "1"
        assert p.metrics["sends"].count("command") == 1
        assert (await p.child_metrics())["opens"] == 1
        p.metrics["read_outcome"] = {
            "kind": original.receipt.kind,
            "attempts": 1,
            "billing_state": original.receipt.usage["billing_state"],
            "ref_kind": original.receipt_ref.kind,
            "ref_version": original.receipt_ref.version,
        }
