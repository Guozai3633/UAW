# C-004：MS-T2c 统一核对入口与明确 outcome 接线

日期：2026-10-08。Session C，目录 `E:/UAW/.worktrees/tool`，分支 `dev/tool`。固定基线 `ms-i2e` / `ba2f3b0d9417e6d695eaa74c2f766217c98b01f1`；源码提交 `3d8cda36d1422a70fb877a87868affe587c1441c`。本包依据 A 的 MS-I2e-next-packages 第3节，只新增 C 内部接口和恢复消费方法。没有修改公共 DTO、shared port、schema、composition、API、锁或迁移。

## 内部接口与默认分支

```python
# src/uaw/tool/receipt_lookup.py
class ActionReceiptLookupPort(Protocol):
    async def find(self, action_id: str, ctx: TrustedExecutionContext) -> Ref | None: ...

# src/uaw/tool/facade.py
ToolFacade(..., lookup: ActionReceiptLookupPort | None = None,
           reconciler: ToolReconciler | None = None)
await facade.reconcile(request, ctx)  # ReconcileRequest -> RuntimeToolruntimeReconcileResult
await facade.read_outcome(action_id, ctx)  # 实际 ToolReconciliationReceipt wire，失败抛 DomainError

# src/uaw/tool/reconciliation.py
await reconciler.check_action(action_id, ctx)  # 固定 Tool 绑定；不是当前来源授权
await reconciler.read_outcome(action_id, ctx)  # 与 facade 委托方法同语义
```

`ToolFacade.reconcile`只接受已有 `action_id/expected_revision`；有界严格 JSON 校验后冻结参数，revision 为严格整数，额外 `receipt_ref`、approved、attempt 等字段拒绝。原 attempt/context/action 必须已经存在且绑定一致，Lookup await 前后都检查；不调用 invoke/discover/_access 或创建身份记录。Lookup 返回的必须是实际固定 `Ref`，最终仍由现有 ToolReconciler 核对 receipt Reader、真实证据、精确 action/attempt/provider/receipt/Usage 绑定、版本、CAS 和原费用计划。

缺 Lookup/Reconciler 返回 dependency_unavailable；没有生产 receipt/evidence Reader 也不能成功。Lookup 的 None 只表示本次没有可读已登记来源，返回 missing/receipt_missing，保留 unknown、已有结论和额度。None、超时、未记 dispatch、取消都不代表 not_applied 或零费用。查找本身不产生权限。

## A 的最小接线样例

以下变量必须由 A 提供真实 owning domain 实现，不是 tests 中的受控组件。`Container.records/budgets`是当前已发布实际属性；Tool Runtime 当前仍未挂载。

```python
assert container.records is not None and container.budgets is not None
ledger = ToolLedger(container.records)
budget_steps = ToolBudgetAdapter(
    ledger, container.budgets, existing_tool_approval_adapter,
    state=container.budgets,  # 同一实际 BudgetService 满足读写 port
)
reconciler = ToolReconciler(
    ledger, budget_steps,
    receipts=owning_domain_receipt_reader,
    evidence=owning_domain_evidence_reader,
)
facade = ToolFacade(
    registry, current_role_environment_access,
    precheck=existing_tool_approval_adapter,
    recheck=existing_tool_approval_adapter,
    lookup=owning_domain_action_receipt_lookup,
    reconciler=reconciler,
)
# ctx 必须从可信持久原 attempt 恢复；模型不提供 ctx/receipt_ref。
request = {"action_id": original_action_id, "expected_revision": effect_revision}
result = await facade.reconcile(request, original_attempt_context)
if result["kind"] == "ok":
    actual = await facade.read_outcome(original_action_id, original_attempt_context)
    outcome = actual["outcome"]  # applied / not_applied / unknown
    # 分别消费真实成果、预算状态/结算回执；此处不产生 Task 完成或 retry 授权。
```

现有 ToolApprovalAuthority 仍须注入 `policies=container.execution_permissions`，保留角色、资源、固定模型、active provider 和 flags 校验。本包没有改变新执行规则。恢复入口只走当下**恢复数据访问**：独立 Lookup/Receipt/Evidence Reader 核对实际主体、scope、Run、原 attempt/action/provider、当前来源许可及版本/签名/完整性。当前执行权限撤销、Run取消/过期不能自动禁止允许的原尝试核算；实际来源数据撤销必须拒绝，不用旧 approval/scope 或预算读取补授权。

Lookup 必须从 owning domain 独立登记的原动作/attempt 来源取 Ref；不能从 EffectRecord、超时、预算状态或任意模型引用制造来源，Tool 不直接读取未来 Runner 私有账本。恢复未决费用计划时须仍可返回该实际固定版本；若只提供更新版本，现有 Reconciler 会拒绝抢占未完成计划，A须安排旧固定版本恢复，不得替换参数/attempt或伪造费用完成。

## 明确 outcome 与效果/费用消费

`read_outcome`读取 EffectRecord.receipt_ref 指向的 **已接受** ToolReconciliationReceipt，核对本 attempt 的 active 记录、原 send intent 和原绑定。重新调用来源/evidence Reader，严格比较实际内容与已接受快照；同版本内容变化拒绝，await期间已接受结论被新回执替代则 stale。结果复制，调用方修改不污染账本。它不使用 Lookup 的未接受新回执，也不调用 BudgetService 或写账本。

已接受效果观察不要求费用已经完成；响应丢失或费用被明确拒绝后，真实固定 outcome 仍可读。反过来，confirmed Usage/真实费用结算不能证明应用效果。`read_outcome`没有已接受回执时返回明确错误，不从 EffectRecord.confirmed推断结论。

| 实际 receipt.outcome | EffectRecord state | 消费边界 |
| --- | --- | --- |
| applied | confirmed | 已有应用证据，Task/成果验收仍由其 owner 判断 |
| not_applied | confirmed | 结论确定为未应用；可以有非零实际费用，不授权重试 |
| unknown | unknown | 结论未决；不能重发或从费用状态推定未应用 |

**核对 ok、EffectRecord.confirmed 均不等于 applied、工具成功或 Task 完成。** 费用是否已记账必须消费预算 owner 的真实状态/结算回执，不能用 receipt.outcome 或 receipt.usage 替代记账完成证明。

原 attempt、参数、原文、用户模型、provider、operation/trace/deadline、固定费用请求和 unknown 维度额度均保持 MS-T2b。恢复不 reserve/dispatch/retry，不换 attempt、不授权新写；所有来源/预算服务 await 在 Tool 事务锁外。默认 registry/flags/HTTP/Runtime 产品能力仍不开放。

## 可执行例子及错误语义

- 成功和明确未应用：`test_sql_facade_lookup_explicit_outcome_and_independent_fees`。not_applied + confirmed 账单保留0.03实际费用；unknown + pending仍保留0.01及未观察tool_calls额度。ok只表示核对记录，随后单独读实际outcome。
- 拒绝：`test_sql_facade_model_receipt_ref_rejected_before_lookup`返回invalid_arguments；`test_sql_facade_rejects_foreign_context_before_lookup`在Lookup前拒绝跨主体/attempt/Run/action；登记与实际provider绑定分别有拒绝用例。来源撤销返回denied，账本/额度不改。
- 重复/恢复：`test_sql_facade_duplicate_restart_and_read_outcome_have_one_fee_plan`、并发用例、新进程用例。重复相同固定回执不新增费用计划或attempt；实例/进程重建从独立SQL登记查找，不接受wire receipt_ref。
- 已接受回执同版本变化：`test_sql_outcome_pinned_body_conflict_rejected_after_acceptance`返回receipt_conflict；并发效果变化的单元用例返回receipt_version_stale。费用回复丢失仍可读not_applied，再重放原费用计划。
- 缺port为failed/dependency_unavailable；Lookup None为missing/receipt_missing；错误参数为failed/invalid_arguments；原绑定/CAS冲突保留conflict；版本变化为stale；Lookup/Reader超时为failed/reconciliation_interrupted。asyncio.CancelledError传播，固定已提交阶段保留。

SQL fixture `ControlledActionReceiptLookup`使用独立 `tool.fixture.lookup` 里的既有 ToolReconciliationReceipt 登记及实际受控 receipt Reader，不从 Tool effects/budget 猜来源。`NoNewExecutionAccess`与`RecoveryBudgetOnly`使任何恢复新准入/reserve/dispatch变成测试失败，并核对原执行阶段记录没有新增或改写。所有 fixture明示受控、无真实 provider/Runner/IPC/executor能力，不能注册到产品。

## 验证与 A 接受要求

本工作区 **135单元 passed**（原97＋新38），Ruff通过，33文件格式检查通过，Mypy strict 17源码文件通过；单元＋SQL合并收集205项，无同名模块冲突。原43项SQL完全保留在 A 已修正的模块名之下，新模块为`test_tool_recovery_facade_postgres.py`，新增27项。

实际运行70项SQL：**70 setup errors，0 passed/failure/skip，exit 1**，唯一原因`UAW_TEST_DATABASE_URL`缺失；没有连接PG或执行SQL业务断言。ms-i2e下原43项已被A实跑接受，但不能因此宣布本包改动通过SQL。没有复制凭据、启动共享DB/迁移或用mock冒充SQL。

```powershell
Set-Location E:/UAW/.worktrees/tool
.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider --junitxml=tests/.artifacts/C/MS-T2c/unit.xml
.venv/Scripts/python.exe -m pytest tests/integration/tool -q -p no:cacheprovider --require-postgres --junitxml=tests/.artifacts/C/MS-T2c/sql.xml
```

原始txt/XML及环境/源码摘要在本session忽略目录`tests/.artifacts/C/MS-T2c/`，handoff列出全部命令。A提供受控PG并在实际集成SHA跑70项SQL及组合回归，再接生产Lookup/Reader和实际消费方。当前shared.ToolPort只声明invoke；如A要挂新的Runtime/HTTP操作，由A独立处理内部port/组装/实施范围，C没有直接扩公共接口。

C-003中pending Usage增量预算规则、最终费用调整及orphan未记Budget dispatch会计协调仍由A负责，本包没有为其设定规则或写会计私有表。没有新增公共DTO缺口；无需改EffectRecord或ReconcileRequest。生产Lookup/Reader/executor、租约/fence/撤销的真实执行接线及完整MS-T2仍等待；D01/D03/D06未自行决定。
