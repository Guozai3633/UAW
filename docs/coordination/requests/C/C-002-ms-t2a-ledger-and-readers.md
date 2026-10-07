# C-002：MS-T2a 持久阶段、权威 Reader 与后续 DTO 缺口

2026-10-07 · Session C · MS-T2a · 基线 `ms-i2a` / `ac9bf621e3caebf060300b3a628b77dee36f7ab0`。
状态：待 A 审阅；没有修改公共 schema、锁、组装、API、迁移或其他 worker 文件。

## 现在可消费的接口

```python
ledger = ToolLedger(PostgresRecordStore(database))
authority = ToolApprovalAuthority(ledger, registry, configuration, access_port, resource_reader)
# A 注入 Authority 到真实审批服务；默认的 None 不会授权。
approval_service = ApprovalService(store, configuration, authority)
gates = ToolApprovalAdapter(ledger, authority, approval_service)
budget_steps = ToolBudgetAdapter(ledger, budget_service, gates)
# MS-T2a facade 只进行持久审批等待/预检/复核；没有 executor，不会预留/发送。
facade = ToolFacade(registry, access_port, precheck=gates, recheck=gates)
```

ToolApprovalAdapter 消费公共 ApprovalPort；ToolBudgetAdapter 消费公共 BudgetPort；ToolApprovalAuthority 满足公共 ApprovalAuthorityPort。生产依赖必须由 A 注入，不用 C 的 fixture 替代。固定模型必须为 ctx.model_policy_ref，必须等于实际 RunAdmissionBinding。动作绑定包含 operation、scope、模型/能力政策、agent/task/node；attempt/trace 不改变 action，但同 attempt 的完整上下文不可换。只读原文、禁止改变文本/空值/版本边界。

ActionResourceReaderPort.resolve(validated_call, trusted_spec, ctx) 返回已从 owning domain 解析并当前授权的实际 Ref 元组，必须覆盖该工具实际触及的所有资源，由调用参数/schema推导，不能直接把模型 resource_refs/path 当授权。每个 Ref 必须保持真实版本并在 ctx.scope.resource_refs 范围内；变更、撤销、缺 Reader 明确失败。access_port 必须读当前角色/父政策交集/领域flag/环境/账号权限；Authority 还独立读取 SQL Run、预算取消/期限、执行政策链和固定/当前配置/提供方/flag。无法解析的 policy feature_flag_refs 明确不可用。ApprovalService 仍拒绝其基线不支持的父政策、规则、持续/非manual授权，不绕开这些限制。

没有配置真实 Reader、角色/环境、权限或提供方、executor 时，生产能力保持 unavailable；flags 从未开启。没有假 wait_ref：gate 读取真实 ApprovalRequest 的当前 id/revision，等待不预留预算；批准后仍 get/recheck、当前资源/权限检查，不自动发送。

## 已有 DTO 足以实现本包，无公共字段新增

本包使用既有 RecordStore 表，仅以命名空间及记录存在性表示阶段，每个 payload 保持原命名 DTO，**不把新私有结构塞进 Object**，也未改变 schema：

| 命名空间 | schema / 意义 |
| --- | --- |
| tool.calls / tool.specs / tool.contexts | ValidatedCall / ToolSpec / TrustedExecutionContext；run/action 的固定输入 |
| tool.attempt.calls / tool.attempt.contexts | ValidatedCall / TrustedExecutionContext；principal 下 attempt 唯一 |
| tool.effects | EffectRecord；初始 pending+空 attempt_ids，claim 时 unknown+实际 intent attempt；不是成功证明 |
| tool.approval.requests | ApprovalCreateRequest；由实际动作/Reader导出的固定审批输入 |
| tool.attempt.estimates | ResourceVector；固定尝试预算估计 |
| tool.budget.reserve.plans / tool.budget.reserved | BudgetReserveRequest / BudgetReservation；可恢复预留计划及实际回执 |
| tool.dispatch.intents | InternalToolInvocationDispatchRequest；唯一 action 派发意图 |
| tool.budget.dispatched | Acknowledgement；预算派发记账实际首个回执，保留 accepted/unchanged 原值 |
| tool.budget.release.refs / tool.budget.released | Ref / BudgetReservation；释放意图及实际服务回执 |
| tool.budget.settle.plans / tool.budget.unknown.settled | BudgetSettleRequest / UsageSettlement；未知用量待核算 |

动作 key 为 run/action 的 SHA256（所有数据仍按 Principal分区）。ToolLedger.bind 在 principal 的 tool-identities 锁下原子固定 action 和全局 attempt 身份；后续工具阶段用 tool-run 锁。每个 SQL 回调只读写记录，无 BudgetPort/ApprovalPort/Reader调用。ApprovalService 持有 conversation 锁调用 Authority 时，Authority只做普通SQL读取，不申请工具锁、不调用预算或审批，因此没有反向嵌套锁链。

预算 reserve/dispatch/release/settle 都在短工具事务提交后调用。各步骤 request_id 和参数存储稳定；超时/响应丢失只重放已保存的同一请求，不新建尝试或重发写动作。CAS确实拒绝后最多4个独立计划。恢复释放只重放确认存在的实际 reservation，不能在审批撤销后新建预留。服务回执失败保留计划；依赖无效DTO返回 dependency_protocol_invalid。账本辅助写入严格限制 tool 命名阶段与对应 schema。

ToolBudgetAdapter.mark_dispatch 是 A 未来接线用的内部**意图/预算记账接口**，不会调用 executor。必须先 gates.require_approved，随后原子 claim+unknown，最后 BudgetPort.dispatch。重放返回False，不提供第二个发送机会。缺真实依赖不调用它；当前 ToolFacade 即使审批通过也返回 dispatch unavailable且不预留。实际发送必须另行解决 fencing/lease、当前取消/撤销/句柄，不能用返回True本身当 Runner 授权。MS-T2a测试只模拟崩溃和记账阶段，未发出任何业务动作。

claim 已发生或服务回复丢失时，effect 保持unknown。新attempt reserve被拒绝；原dispatch attempt不能release。并发竞争中没有提交发送意图的另一个尝试可释放自己的未dispatch预留，预算服务仍复核真实account。settle_unknown只提交 billing_state=pending、实际未知资源省略，保留未观察额度，不把0当真实用量。

## 后续公共 DTO/port 缺口（未消费建议字段）

完整MS-T2需要公开的真实回执/对账port，至少给出：action/attempt固定绑定、provider_ref、真实receipt_ref、effect state、Usage以及可验证证据。没有权威Receipt Reader时，不实现confirmed回执/“未发生”恢复或将effect改为成功。本包只保守持久pending/unknown。

现有EffectState只有confirmed/pending/unknown；没有confirmed-not-applied，也不能区分“请求尚未发送”与“已经发出但结果未知”的公共证据。因此建议 A 决定一个严格命名的 ReconciliationReceipt：action_ref、attempt_id、provider_ref、observed_state（例如 applied/not_applied/unknown）、evidence_refs、observed_at/固定版本。not_applied需要真实提供方/执行器证明，单凭超时或预算尚未记账不能成立。恢复仍由固定ToolSpec.retry_policy_ref限制。字段/枚举/版本待A决定，本包不私加、不消费该DTO。

BudgetPort缺少恢复查询方法：当前ToolLedger为计划CAS读取已有RootBudgetLedger，并用已有BudgetReservation是否存在来限制恢复只重放已提交预留。若A希望禁止跨域储存读，应增加只读 `BudgetStatePort`（get_ledger/get_reservation + owning attempt校验），A批准发布新基线后C切换；现在没有更改BudgetPort或绕过BudgetService写入。

角色/环境/账号权限和资源 Reader 仍属真实接线缺口；不自行选择 D01/D03/D06。需要公共 aggregate lifecycle DTO或事件时由A命名与生成，本包没有新事件/迁移/依赖。A 的composition/API是消费方；既有调用签名/DTO未变，B/D不应消费未合入本包。

## 验证与接收要求

实际单元66 passed、0 failure/skip；Ruff/格式/Mypy(15源码文件)通过。17个SQL用例已收集并以--require-postgres尝试执行，但全部在fixture阶段因UAW_TEST_DATABASE_URL缺失停止，**实际SQL行为尚未验证，不宣布完成验收**。详见C handoff及tests/.artifacts/C/MS-T2a/。

A安排受控开发PG、独立测试主体后，在本分支或集成SHA运行：

```powershell
.venv/Scripts/python.exe -m pytest tests/integration/tool -q --require-postgres --junitxml=tests/.artifacts/C/MS-T2a/sql.xml
```

用例覆盖服务实例重建、真实持久审批引用、相同action/不同attempt、同ID参数/模型/操作绑定冲突、同attempt并发reserve、action独占claim、release/claim竞态、四个服务阶段提交后响应丢失、claim提交后记账前中断、预算取消、批准后资源/政策/提供方变化和unknown不重发/不释放。测试中的Reader/role/environment/connected提供方只是受控fixture，实际ApprovalService/BudgetService/PostgreSQL才是SQL验证目标；不注册到产品Container。

回退：A revert C源码提交及后续接线提交，保留现有记录和unknown效果，不用代码回退删除持久意图或视为撤销外部效果。没有新迁移、外部实际调用、真实业务副作用或开放flags。

A决定 / 发布SHA / 组合回归：待A在DISPATCH记录。
