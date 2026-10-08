# C-003：MS-T2b 核对接线及剩余接口边界

日期：2026-10-08。Session C / MS-T2b。固定基线 `ms-i2c` / `1411f6aa477b0d000bee871c0f324fbfd67b4ff5`。待 A 审阅；公共schema、锁、组装、API、迁移及其他worker文件未修改。

## 本包已收敛的接线

```python
ledger = ToolLedger(store)
authority = ToolApprovalAuthority(
    ledger, registry, configuration, role_environment_access, action_resource_reader,
    policies=execution_permissions,  # ExecutionPolicyPort，真实当前父链
)
approval_service = ApprovalService(store, configuration, authority)
gates = ToolApprovalAdapter(ledger, authority, approval_service)
budget_steps = ToolBudgetAdapter(ledger, budgets, gates, state=budgets)
# Container.budgets 的同一 BudgetService 实例满足读写 port；不可默认为任意写 port 也能读。
reconciliation = ToolReconciler(
    ledger, budget_steps, receipts=actual_receipt_reader, evidence=actual_evidence_reader,
)
result = await reconciliation.reconcile(pinned_receipt_ref, original_attempt_context,
                                         expected_revision=current_effect_revision)
```

- `policies`为公共ExecutionPolicyPort，未注入明确不可用。Tool不再遍历execution.policies或读取budget.*。检查返回snapshot的run/scope/叶policy版本hash/capability绑定，权限决策交A实时port；随后仍核查固定用户模型、角色、实际资源Reader、固定/当前配置、active提供方、旗标及环境。旧connected字段没有带回。
- `state`为公共BudgetStatePort，未注入明确不可用。查询原Run/attempt真实状态及revision，不产生新准入；后续reserve/dispatch/settle/release仍走BudgetPort，写操作仍CAS。取消/过期原尝试恢复与新动作准入分开，恢复不调用reserve/dispatch来猜测结果。
- `ToolLedger.claim`现在接收由BudgetStatePort读取的budget/reservation只读snapshot，而不是跨owner查询。它只记录Tool意图，不授权发送。实际BudgetService.dispatch仍核验当前状态；不同服务的查询与外部发送不是原子事务，真实executor/lease/fence仍待完整MS-T2。
- `ToolReconciler`是内部固定Ref消费入口，未挂载Tool/HTTP Runtime；使用既有RuntimeToolruntimeReconcileResult返回。没有Reader/executor时不开放目录、flags或dispatch。查询来源、版本/摘要、签名/协议、本人范围由真实ToolReceiptReaderPort负责；C严格比较原action_ref/attempt/provider/receipt_ref和usage.attempt_id，Reader并非模型或timeout结论。

## 实际证据 port（本包内部，无新增wire DTO）

`ToolEvidenceReaderPort.check(ref: Ref, ctx: TrustedExecutionContext) -> Ref`需由证据owning domain实现：每次检查当前来源访问、真实固定版本/摘要/完整性并返回实际Ref。不能只把传入Ref原样当作证明，不能以旧Scope或批准来缓存授权。C复查返回Ref精确一致，证据存在不等于可访问；applied/not_applied至少一条真实证据，缺Reader拒绝。证据检查后再次读取同版本receipt，来源撤销或变化拒绝。

这些Reader必须支持**原尝试数据恢复权限**，而不是把已取消/过期Run的新执行权限当读取准入。来源撤销而不能读取时保持原unknown/已知结论及未决额度；不倒推not_applied。生产Reader当前未提供，默认None始终不可用；tests的SQL Reader只读取本session受控fixture，不是真实提供方执行证明。

## 严格持久核对阶段

| 命名空间 | 已发布schema与含义 |
| --- | --- |
| tool.reconciliation.receipts | ToolReconciliationReceipt；不可变实际回执快照 |
| tool.reconciliation.active | ToolReconciliationReceipt；每个attempt当前核对计划，记录revision CAS切换 |
| tool.reconciliation.budget.plans | BudgetSettleRequest；每个回执固定费用计划，最多4个确定CAS冲突重读 |
| tool.reconciliation.settled | UsageSettlement；原预算服务实际结算回执，不重造账单 |
| tool.reconciliation.failures | Failure；已知预算事务拒绝记录，保留证据效果而不宣称费用完成 |

同一principal下receipt的kind/id/version组成唯一身份；同版本改hash/location/body冲突，不能改idempotency键重新计费。首次核对要求当前EffectRecord revision，重复已接受的相同receipt复用固定计划/回执，不再次更新效果或费用。实际action/attempt/provider/usage绑定必须匹配已持久send intent。没有send intent不推定未应用，也不新建发送。

工具事务只读写Tool记录，无Reader/BudgetService调用；预算状态查询和write均在事务提交后进行。所有费用请求使用原attempt/operation/trace/deadline，不延长期限、不换用户模型或修改原文。响应丢失后重放同一个请求/参数，不能用当前revision覆盖旧计划。新receipt在前一不确定计划完成前拒绝抢占；确定的usage_reconciliation_denied/usage_settlement_denied保留失败记录，可接受后续真实confirmed账单。已被后续证据替代的未完成旧receipt不能重新抢占费用阶段。

效果证据在Tool事务提交，费用随后独立写入；费用服务异常不回滚真实已知效果。同样，费用confirmed不把unknown效果改为applied。同usage的新效果证明复用已完成实际费用回执，不再次收费。此前MS-T2a的pending UsageSettlement可按其固定费用计划桥接，不重复记账。unknown禁止新写attempt/重发；not_applied仍核对actual Usage，不能视为零费用或自动获得retry授权。

## 需要 A 注意的公共边界与缺口

1. **EffectRecord.state=confirmed表示结论确定，不是应用成功。** applied和not_applied的区别保存在严格ToolReconciliationReceipt.outcome与receipt_ref中；新Reconciler的ok表示核对记录提交。所有消费方都必须读取确定outcome，不能仅凭confirmed播放工具成功/触发依赖任务。本包不添加EffectRecord.outcome或改公共schema。
2. 现有公共ReconcileRequest只有action_id/expected_revision，没有receipt查找/选取来源。内部入口采用可信pinned_receipt_ref；A在组装公开Runtime之前必须由权威来源确定该Ref，或独立发布严格Lookup port/版本。不能把模型随意指定的Ref当作真实工具回执来源。本包未扩请求、未挂API。
3. BudgetService目前允许初次pending/estimated及后续confirmed；新的pending观察增量会明确usage_reconciliation_denied。C保留该receipt和已知效果、原有额度/预算拒绝，后续真实confirmed账单可继续。若需支持pending增量或最终账单调整，请A在BudgetPort/合同中明确单调合并、对账revision、原attempt/CAS及计费去重后发布新基线；C不会私写accounting或伪造完整Usage。
4. orphan Tool意图没有完成Budget dispatch记账时，真实BudgetService可能拒绝settle；C保存真实证据结论及未决费用，不调用dispatch来推定或伪造执行，不抹掉unknown。真实执行闭环需A明确会计恢复/dispatch协调。
5. 原attempt上下文必须保持固定身份与授权来源；恢复Reader独立复核当前数据访问。ExecutionPolicyPort成功/预算read成功都不等同真实发送授权；没有生产Reader、executor和lease/fence时完整MS-T2继续等待。

以上需要公共变化的字段/Lookup/Budget规则均为待A决定的提案，本包未消费未批准字段，无新DTO、依赖、迁移或事件。A/B/Agent/结果消费方需遵守outcome/费用分离；D不依赖C开发分支。

## 验证与接受

97项单元通过、Ruff/格式28文件通过、Mypy strict 16源码文件通过。原66项MS-T2a单元仍通过，新增31项组件用例；原17项SQL由A在ms-i2c已验证，不代表本包变更后的状态。

本包新增26项SQL，合计43项已收集并用--require-postgres尝试；因本工作区UAW_TEST_DATABASE_URL缺失，43 setup errors、0 passed/skip，业务断言没有运行。不能以收集/内存替身宣称SQL通过。回执在tests/.artifacts/C/MS-T2b。A须安排受控开发库，独立测试主体（既有fixture随机principal并只清理该主体）再跑：

```powershell
.venv/Scripts/python.exe -m pytest tests/integration/tool -q -p no:cacheprovider --require-postgres --junitxml=tests/.artifacts/C/MS-T2b/sql.xml
```

SQL覆盖跨进程/实例重建、固定费用回复丢失、Tool提交后回复丢失、重复与同版本冲突、并发核对、效果与费用分别更新、pending未知额度保留、not_applied非零账单、批准/政策/来源撤销、取消和过期原attempt清理、没有Reader/state port、禁止所有Tool私有预算/政策读取的守卫和真实父链拒绝。

回退由A revert源码/接线提交，保留持久意图/unknown与实际费用记录；不得用代码回退宣称已撤销外部效果。本包未发生真实业务dispatch/外部副作用。A决定、发布SHA与组合回归写DISPATCH，C不改公共派发表。
