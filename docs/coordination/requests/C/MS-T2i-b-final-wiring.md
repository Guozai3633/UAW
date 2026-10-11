# MS-T2i-b：有限原 Tool runtime 路由最终接线

2026-10-11，Session C，`E:/UAW/.worktrees/tool` / `dev/tool`。

执行基线 `ms-i2l-a8 / 06ff3ef56b68d391387bc7b154fa58ecb00571f9`，源码标签 `ms-i2l-a8-source / 16e0efaf6daff2fbbd0281473a8c6cc1f652d0e6`，固定规则标签 `ms-i2l-a8-followup / 610a920d9cc83900f056b0eb2ccfaf13cb122ff8`。均已 fetch 后核对远端；干净从 c8c54563793ebb4c33e846163a0928179c87ee44 快进执行标签。未合浮动 integration，原 ms-i2l-start 未移动。

M1/M2接口源码 **f80ca330fc8a6817b98d55f6c8ce042f2f2a49ad**，阶段接线 c9e39ad77649e83912f21e6a700404f8917704ab；原组装缺口提案 b0afbf7a29d04a841fdc67902547606dea0fa854；M3恢复/SQL源码 **4e0bec668acc644f7c5e00ddca9b8dc7565043d9**；最终源码/测试 **223c9a9963414bdc1ae71d3e723224d0958ab63c**。最终仅修正测试对未发布办公回执的预期，不改变旧 Lookup/Invocation。独立handoff随后提交。

## A 消费与最小接线缺口

固定接口在 `src/uaw/tool/runtime_router.py`：ToolResultReadPort、冻结 ToolRuntimeRoute、RoutedToolRuntime 的 discover/invoke/reconcile/read_outcome/read_result。构造严格1–128完整tuple，全Tool配置Ref必须含规格hash，provider含原版本及存在的hash；禁止额外位置/范围、重复tool id/version及错规格/provider。每个原facade/Invocation与router共享同registry、同实际records store，原Invocation存在且 `invocation.access is effective_agent_access`。不修改传入实例。

A8 `assemble_office_tools`、`assemble_file_tool` 和 `assemble_installed_file` 尚未提供单独有效Agent access构造参数；具名最小提案见 [MS-T2i-b-agent-access-proposal.md](MS-T2i-b-agent-access-proposal.md)。A在原组装路径构造相同有效port，保留独立Run/config/审批/data sources检查，不能全局把container.tool_access换成不兼容的Agent包装。A负责Agent/composition/审批HTTP所属服务路由/flags/provider和真实native来源。

```python
from uaw.tool.results import ToolResults
from uaw.tool.runtime_router import RoutedToolRuntime, ToolRuntimeRoute

# office/file 均是A以同registry/records store/effective_agent_access构造的原bindings。
file_invocation = file.facade.invocation
assert file_invocation is not None
file_results = file_invocation.results
assert isinstance(file_results, ToolResults)  # A8 FileToolBindings没有独立results字段
routes = tuple(
    ToolRuntimeRoute(pin, office_provider_ref, office.facade, office.results)
    for pin in office_tool_refs
) + (ToolRuntimeRoute(file_tool_ref, file_provider_ref, file.facade, file_results),)
runtime = RoutedToolRuntime(registry, office.ledger, routes, access=effective_agent_access)
```

此构造无register、权限授予、flag变更或send。缺原Invocation/Reader/access或store身份不同构造拒绝，不用另一个facade兜底。多个原ToolLedger可共享同records实例，不要求ledger本身同一对象；不同store仅连接同数据库仍拒绝。

## 输入输出和恢复顺序

- discover严格ToolToolsDiscoverInput；当前共享access先筛选、原registry小目录评分只接纳显式固定route，在排序/候选上限前排除未绑定工具。返回RuntimeToolruntimeDiscoverResult/DiscoveryResult，LLM选择。这里使用原小目录词法实现，不冒充语义；原retriever/embedding/索引和独立facade未改。
- invoke先冻结原JSON，再normalize选择唯一facade，原完整请求及同ctx/action/attempt委托原Invocation。仍由原权限/资源/config/审批/预算/一次发送链准入；不改用户模型，不额外创建attempt、reserve、dispatch或retry。
- reconcile严格ReconcileRequest，额外receipt_ref拒绝；从ledger原attempt/call/spec/ctx以及当前完整registry/provider唯一选源，委托原Lookup/Reconciler，返回RuntimeToolruntimeReconcileResult。
- read_outcome返回实际已接受且当前owning Reader可读的ToolReconciliationReceipt；read_result返回原ToolResults的RuntimeToolruntimeInvokeResult/ToolResult。读取失败抛DomainError；ToolResult绑定字段是call_ref，不能添加tool_ref公共字段。
- 三个恢复入口不snapshot新执行access；delegation前后都复核持久原绑定及当前注册，不承诺跨模块原子授权快照。最终正文权限/来源证据/用量仍由原Reader核对，不扫描其他provider，不使用旧审批当读取授权。

成功或原等待样例（审批仍交实际原service/HTTP，不能代码自报批准）：

```python
found = await runtime.discover({"query": "arithmetic.calculate file.read", "max_candidates": 8}, ctx)
result = await runtime.invoke(original_request, ctx)
# result.kind=waiting 时 wait_ref 是原实际ApprovalRequest；没有执行。
# 经本人真实审批并由原服务记录后，保持原request/ctx调用；检查ToolResult而非推断Task完成。
```

严格拒绝样例：

```python
from copy import deepcopy
bad = deepcopy(original_request)
bad["tool_ref"]["content_hash"] = "0" * 64
refused = await runtime.invoke(bad, ctx)  # stale/invalid，不fallback，不发送
extra = {"action_id": original_request["action_id"], "expected_revision": 0,
         "receipt_ref": original_request["tool_ref"]}
refused_reconcile = await runtime.reconcile(extra, ctx)  # invalid_arguments，未读ledger
```

原版本/CAS和重复恢复样例：

```python
action_id = original_request["action_id"]
effect = await original_ledger.effect(action_id, original_ctx)
observed = await runtime.reconcile(
    {"action_id": action_id, "expected_revision": effect["revision"]}, original_ctx,
)
# actual receipt未发布/不可读时保留missing/denied/unknown，不解释为not_applied或零费用。
outcome = await runtime.read_outcome(action_id, original_ctx)
result = await runtime.read_result(action_id, original_ctx)
# 原CAS/幂等与数据权限由所属组件处理；旧expected_revision冲突需读原状态，不新attempt。
```

办公executor已持久真实ProviderReceipt但发送回复丢失、source receipt尚未publish时，原ToolReceiptStore.find仍返回None，reconcile正确missing；路由器不会偷偷publish。原无executor facade.invoke对同request/ctx恢复已登记ProviderReceipt，经已有ToolResults.resume发布/核对/规范化，然后read_result可读；它不是新发送权。file所属source可从原journal恢复原实际证据并发布。未知/缺原响应始终unknown，不因missing自动重做或换attempt。不得让新调用绕过当前access。

正文撤销不阻断允许的独立原账务恢复：A以同原ledger/budget调用原recover_file_accounting，仅重放已接受Usage及固定费用计划，不读文件/Reader，不从not_applied/HTTP/Runner ok推断零费用。confirmed、reconcile ok、read_result ok与applied、工具业务成功、Task完成分别核验。

## 真实验证与历史失败

自身 `. ./ops/start-dev-db.ps1 -Session C`，loopback55434；锁定本venv `python -m alembic upgrade head` exit0，current `0003_attempt_identity (head)`。`uv sync --frozen --extra agent-engine --link-mode copy`，自身.cache/uv，91包锁定环境；没有复制A配置或凭据。

最终 **121不同单元＋48不同真实SQL** 通过，最终failure/error/skip均0。新36单元/42SQL，原受影响85单元/6SQL。不是一次121/48，也不把重试叠加。回执在ignored `tests/.artifacts/C/MS-T2i-b`，verification-index.json逐节点最终状态、所有XML原失败与SHA256由build_index.py生成并断言节点数量；scope-check.json验证C目录/公共锁契约组装/旧handoff原字节。

| 回执 | 实际结果 |
|---|---|
| M1-unit.xml | 新阶段28通过 |
| M4-unit-extra.xml | 32通过 |
| final-unit.xml | 118通过：原受影响85+新33 |
| final-router-unit.xml | 最终路由36通过；单元合并去重121 |
| M3-sql.xml | 首次漏注册间接fixture，8收集error，无SQL通过声明 |
| M3-sql-fixture-fixed.txt | 收集24后中断，无完成XML，不算通过 |
| resume-first.xml | 1失败：测试错读ToolResult.tool_ref；使用既有call_ref修正 |
| M4-sql.xml | 42节点中36通过/6失败，1414.50秒；原失败保留 |
| discovery-fixed.xml | 三种组合非空query定向修正后3通过，2.41秒 |
| loss-fixed.xml | 三种组合未publish办公回执正确missing，然后原无executor恢复；3通过，277.83秒 |
| affected-sql.xml | 原办公三工具和file原结果/丢回应/unknown，6通过，219.34秒 |

原XML共15失败/error记录保留：8fixture收集、1字段预期、3非法空query、3把尚未发布办公receipt预期为ok。mypy首次discover字典推断错误也保留，显式JsonObject后通过；自动审批审核曾因额度失败使新增诊断命令未执行，用户继续后恢复，未绕审批。未改运行语义来使测试通过。

实际命令：`python -m pytest tests/unit/tool/test_runtime_router.py tests/unit/tool/test_access_identity.py tests/unit/tool/test_registry_schema.py tests/unit/tool/test_recovery_facade.py --junitxml=<final-unit.xml>`；最终router补3类型边界以同模块复验。
SQL：`python -m pytest tests/integration/tool/test_runtime_router_postgres.py tests/integration/tool/test_runtime_router_recovery_postgres.py --require-postgres -vv -o faulthandler_timeout=120 --junitxml=<M4-sql.xml>`；仅上述6失败节点按两函数定向复验，不重新全量。
原6SQL明确选 `test_office_tools_postgres.py::test_office_approved_actual_result_fixed_receipt_fresh_objects`（3）及 `test_file_pipeline_postgres.py` 的 `test_actual_file_read_preserves_original_and_pending_fee_restart` / `test_original_journal_reply_loss_file_changed_cancel_recovers_old_bytes` / `test_no_original_journal_retains_unknown_hold_and_refuses_new_attempt`（各1）。完整stdout/txt与XML同目录。

ruff七文件、format七文件和两个受影响源码mypy通过；最后两测试修正再check/format通过；git diff --check通过。没有运行多资料包或目录全量，旧219SQL/历史节点均不冒充本轮复跑。

受控与真实严格分记：SQL、实际Decimal/JSON/text计算、临时根WindowsReadHandle、真实Ed25519签名、原SQL独立journal、真实子进程是本轮实际执行；Agent/role/provider/config flag决策、文件bridge/root/设备来源与“用户决定”是明确controlled fixtures。生产installed双进程/native本人确认、生产Agent有效access和真实模型/Artifact/Task链本轮0次验收，仍待A/D实际接线。无产品目录/flags/模型改动，默认缺真实源不可用。

无新共享DTO/依赖请求；原作用/费用、原attempt、固定费用计划及完整文件/片段/material hash语义未变。自身测试主体由原fixture清理；子进程正常退出，没有C后台executor/重试任务；独立DB供后续A验收保留。本包结束，不自动进入下一包或完整MS-T2。
