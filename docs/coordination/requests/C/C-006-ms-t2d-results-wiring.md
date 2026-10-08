# C-006：MS-T2d 最终结果链与A接线要求

日期2026-10-08。实际目录`E:/UAW/.worktrees/tool`，分支`dev/tool`。固定基线`ms-i2g-start / 0bd8e2b8387a46e16435dc033956c2b69bb1a859`。

阶段源码`27d17a3c2f3d2637ce5c7e386ae6eec3d2a9be63`、阶段接口文档`717c2371c407b6c5a7be083c9b8f601f5fd0d87f`保留；C连续完成同包后半段。最终源码`859f5d0f1ac90dc51e8500282b70d1acee924c06`；实际验证回执见[C handoff](../../handoffs/C.md)。本包不改变公共DTO，不请求A增加schema/迁移/锁字段；生产接线与完整MS-T2仍由A验收。

## 最终内部接口

```python
ToolInvocation(registry, ledger, budgets: ToolBudgetAdapter,
    approvals: ToolApprovalAdapter | None, *, access=None, executor=None,
    estimates=None, results=None, prepare=None)
await invocation.invoke(request: JsonObject, ctx) -> JsonObject

ToolReceiptStore(ledger, blobs: BlobStorePort, *, provider_ref: Ref,
    provider: Principal, access: ToolRecoveryAccessPort | None = None,
    verifier: ToolOutputVerifierPort | None = None)
await source.publish(receipt: JsonObject, ctx,
    *, authenticated_provider: Principal) -> Ref
await source.find(action_id: str, ctx) -> Ref | None
await source.read(receipt_ref: Ref, ctx) -> JsonObject
await source.check(raw_result_ref: Ref, ctx) -> Ref
await source.provider_receipt(ctx) -> JsonObject | None
await source.read_raw(raw_result_ref: Ref, ctx) -> JsonObject

ToolResults(source: ToolReceiptStore, reconciler: ToolReconciler)
results.ready() -> None
await results.resume(call: JsonObject, ctx) -> JsonObject
await results.read_result(action_id: str, ctx) -> JsonObject
```

`ToolResults.read_result`返回既有`RuntimeToolruntimeInvokeResult`，payload是实际持久`ToolResult`；不改变公共Runtime入口。阶段版局部`ToolInvocationResultsPort`增加同步`ready()`，在预留前检查当前恢复权威与实际验证器已装配。只有原尝试已持久send意图的恢复可省略新执行access/executor/approvals；新调用缺任何必要依赖都明确不可用。

`ToolReceiptStore`同时实现现有Lookup、ToolReceiptReader和ToolEvidenceReader，读取独立持久源，不拿EffectRecord或预算状态生成回执。`ToolRecoveryAccessPort.check(call,spec,ctx,*,provider)`必须由A注入实际当前数据权限来源，核对完整主体/session、原Run/conversation/task、固定用户模型、scope与当前资源、固定provider及其完整服务身份。旧审批、ctx或Ref不授予恢复权限。取消/过期后的原数据和账务恢复与新动作准入分离；权限撤销后旧结果同样拒绝。

## A构造与消费样例

以下是可信内部组装样例，变量均来自A实际来源；不是已挂载的产品能力，也不是独立HTTP/模型接口。C不自动登记text.inspect、不开放flag。A若明确批准内部诊断使用，应先固定`text_spec(provider_ref)`版本及实际adapter绑定，再提供`registered_text_ref`。

```python
from uaw.tool.approval import ToolApprovalAdapter
from uaw.tool.budget import ToolBudgetAdapter
from uaw.tool.facade import ToolFacade
from uaw.tool.invocation.dispatch import ToolInvocation
from uaw.tool.ledger import ToolLedger
from uaw.tool.providers.text import TextInspectExecutor, TextInspectVerifier, text_estimates
from uaw.tool.receipt_store import ToolReceiptStore
from uaw.tool.reconciliation import ToolReconciler
from uaw.tool.results import ToolResults

ledger = ToolLedger(actual_records)
gates = ToolApprovalAdapter(ledger, actual_tool_authority, actual_approval_service)
budget_steps = ToolBudgetAdapter(ledger, actual_budget_service, gates,
    state=actual_budget_service)
source = ToolReceiptStore(ledger, actual_private_blob_store,
    provider_ref=fixed_text_provider_ref,
    provider=authenticated_internal_text_service,
    access=current_recovery_data_authority,
    verifier=TextInspectVerifier(fixed_text_provider_ref))
executor = TextInspectExecutor(source, provider=authenticated_internal_text_service,
    currency=actual_budget_currency)
reconciler = ToolReconciler(ledger, budget_steps, receipts=source, evidence=source)
results = ToolResults(source, reconciler)
invocation = ToolInvocation(registry, ledger, budget_steps, gates,
    access=current_role_environment, executor=executor,
    estimates=text_estimates(actual_budget_currency), prepare=executor.check,
    results=results)
facade = ToolFacade(registry, current_role_environment,
    invocation=invocation, lookup=source, reconciler=reconciler)
request = {"tool_ref": registered_text_ref.wire(), "action_id": original_action_id,
           "arguments": {"text": "  原文\r\nKeep\u0301 exact  "}}
result = await facade.invoke(request, original_ctx)  # waiting必须引用真实审批
# 由既有审批入口决定；批准后重调相同request/ctx，不能换attempt。
# 获得ok后仍以当前实际Reader复查；ok不表示Task完成。
if result["kind"] == "ok":
    outcome = await facade.read_outcome(original_action_id, original_ctx)
    read_back = await results.read_result(original_action_id, original_ctx)
    reconciled = await facade.reconcile({"action_id": original_action_id,
        "expected_revision": read_back["revision"]}, original_ctx)
```

实际纯计算样例：输入字符串`"  原文\r\nKeep\u0301 exact  "`，不规范化原文，其data为：

```json
{"characters":19,"utf8_bytes":24,"lines":2,"sha256":"5af39d680d1fbb3455d105c384cba0d32390bf0d929c4ee3338bf24c86c3f62c"}
```

characters计Python字符/code point，utf8_bytes计原UTF-8字节，lines采用splitlines（CRLF算一个分隔符，结尾分隔符不额外加行，空串0行）。容量上限32768 UTF-8 bytes，唯一参数text，拒绝额外字段。免费本地计算计费定义显式固定：tool_calls=1、模型/children/tokens/网络费0、money=0.00；wall_time_ms实测纯计算，不包含审批/SQL/blob协调时间。A必须与预算currency匹配；零费用没有从HTTP200、Runner ok或effect confirmed推断。

## 保存与恢复边界

| 命名记录 | 现有具体schema | 用途 |
| --- | --- | --- |
| tool.response.refs | Ref | 原尝试实际raw JSON的固定主体隔离blob摘要 |
| tool.response.providers | Principal | 完整独立provider服务身份 |
| tool.provider.receipts | ProviderReceipt | 已实际保存响应及测量Usage |
| tool.invocation.receipts | ProviderReceipt | executor返回的严格接收回执（响应丢失时可缺） |
| tool.source.receipts | ToolReconciliationReceipt | 严格发布的固定证据/outcome/usage |
| tool.results | ToolResult | 验证输出且费用回执完成后的不可变结果 |

实际JSON通过现有主体隔离BlobStore保存，命名SQL记录不使用无约束Object；无新永久表/迁移。raw Ref为content固定version1与实际字节hash。source receipt Ref也是content/version1，其hash绑定实际ProviderReceipt、完整原ctx、完整独立provider和provider_ref；不自引用整个reconciliation envelope。observed_at仅首次发布生成，重复publish返回同一记录/Ref；不能借版本变化替换原观察。Lookup不自动发布，也不是准入授权。

只读成功需要ProviderReceipt严格绑定、真实保存raw、固定output_schema及TextInspectVerifier独立核对实际文本；effect confirmed/transport完成不是成功依据。ToolResult保存实际call/raw/receipt/settled usage Ref，并在每次读取重新核对来源、证据、绑定、输出与当前恢复权限。reconcile ok仅代表观察和费用核对，read_outcome始终返回明确ToolReconciliationReceipt；消费者必须检查outcome，不能视为工具成功或Task完成。

效果与费用沿用原ToolReconciler/ToolBudgetAdapter独立恢复。真实费用提交后响应丢失复用原固定计划/请求ID；已接受applied可在费用响应恢复前读取，但没有实际费用Ref不能生成成功ToolResult。send意图持久CAS后没有第二次发送权；即使超时发生在实际计算之前，也保留unknown和未知维度额度，不从缺Budget dispatch记录或超时推断未执行。收到坏输出时保留实际raw/Usage、unknown及额度，不伪造成功/零费用。仅本次已准入reserve/send失败且明确无send意图才清理原预留；冲突/畸形请求不能释放原尝试额度。

所有BudgetService、权限/验证器、blob/executor await都在Tool会话事务锁外；SQL只短暂固定immutable记录、意图和CAS。恢复不新建attempt、不reserve、不dispatch、不retry。

## 接线缺口与消费方影响

- A需提供实际ToolAccess角色/环境、原资源Reader、ToolApprovalAuthority当前Run/配置/资源/ExecutionPolicyPort、真实ApprovalService与BudgetService/State、可信provider完整Principal及当前恢复数据授权。C的SQL角色/资源/恢复权限fixture明确是受控组件，不能登记为生产能力。
- A将最终source/results/executor注入既有ToolFacade；缺任一必要依赖保持unavailable，默认Container/Runtime尚未挂载。本包没有编辑公共composition/API/schema/锁或读取D开发分支；网络、用户文件、安装/写入/exec不属于本包。
- pending增量预算规则、orphan账务协调仍由A处理。无实际响应或输出无效的原尝试保留证据/未知额度，不能替换为新尝试自动重发；本source仅发布已独立验证的text只读applied，不虚构not_applied/unknown业务观察。
- D01/D03/D06保持待确认，用户模型固定，产品目录/flags与完整MS-T2/P1-03接受仍等A整链验收。

## 实际验证回执

最终单元162项通过；真实SQL以原70项通过和最终新增30项通过合计100个不同用例，最终验证覆盖0未通过/错误/跳过。原70模块与固定基线字节一致，本包最终修正只影响新增调用/source/results路径，因此保留原回归实跑回执并复跑全部新SQL模块，没有将汇总冒充一次100项完整实跑。首轮SQL共97项：96 passed/1 failed/0 errors/0 skipped；失败是新测试审批decision误写deny，依既有公共枚举修正为decline，随后全部30项新增SQL通过。首轮及修正回执同时保留，没有隐藏失败或改公共契约。Ruff、45文件format检查及22源码Mypy通过。C独立端口55434迁移head成功；权限/角色/Reader受控，实际计算、PostgreSQL、blob和跨Python进程恢复是真实实现。

回执在本worktree ignored `tests/.artifacts/C/MS-T2d/`：`unit.xml/unit.txt`、`sql-initial.xml/sql-initial.txt`、`sql-new.xml/sql-new.txt`、`ruff.txt/format.txt/mypy.txt`、`environment.json`。新SQL模块名与单元模块不同；旧70项模块保留。未实跑产品Runtime/实际用户授权、网络LLM、Runner/IPC，也未启用产品目录/flag；这些不列为本包测试通过。
