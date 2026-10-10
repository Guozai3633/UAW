# MS-T2g 最终接线要求

实际分支 dev/tool，worktree E:/UAW/.worktrees/tool。固定基线 ms-i2j-start = abb4590f2bfe53c601e0f6a4a3b65447ba4ec502；按锁同步独立环境。M1 源码 c8b5676d4cb65a65a38391b304095600b0ffed54 / 阶段说明 9195a2e；M2 源码 6abd666262df449a7e6d3c374613a7326944250b / 接线样例 f9b661c。最终源码 5b7749d0e80f7576362dd5736e0d89ac779e01a5（包含M3 a9847f9及最后范围/额度修正）；358单元与219不同真实SQL最终通过，0最终失败/错误/跳过。组件结果不代表生产整链验收。

## 固定构造及 C → A 接口

```python
from uaw.tool.providers.file_read import file_read_spec, ToolFileReadBridgePort
from uaw.tool.providers.file_store import (
    FileReceiptStore, FileReadExecutor, FileReadVerifier, FileResourceReader,
    recover_file_accounting,
)

spec = file_read_spec(actual_provider_ref)  # 完整不可变 file.read@1
source = FileReceiptStore(
    ledger, blobs, provider_ref=actual_provider_ref, provider=actual_provider_identity,
    access=current_file_data_authority, bridge=registered_file_bridge,
    signatures=current_registered_signatures,
)
source.verifier = FileReadVerifier(source)
executor = FileReadExecutor(source, provider=actual_provider_identity)
resources = FileResourceReader(actual_provider_ref, registered_file_bridge)
# 原 ToolRegistry 显式注册；原 ToolExecutorBinding/ToolOutputVerifierBinding 绑定完整 ToolRef
# 原 ApprovalAuthority(resources=resources)、ApprovalService、BudgetService、ToolInvocation
# ToolResults(source, reconciler)，ToolFacade(..., lookup=source, reconciler=reconciler)
```

原有限 executor/verifier 路由可组合不同工具实现；file.read 必须用专用 FileReceiptStore/ToolResults，text/算术/JSON 继续用原 ToolReceiptStore。即使 provider 相同，也不能把 FileReceiptStore 接成所有工具的共用结果源。A 按完整原 ToolRef/hash/provider 选对应 invocation/results/source/reconciler bundle；恢复先查原 ledger.attempt 的固定 ToolRef，再选 owning Lookup/Reader，不按模型报告的 name、额外 receipt_ref 或 Provider ID 猜来源。C 固定 Spec 的 categories=["file"]，角色须消费该完整 Spec 分类；静态公共目录的 workspace 分类不自动变成权限别名。A 的实际角色/environment/provider、当前 scope 和 file_access 必须满足原权限链；file.read 不需要 process_exec/code_execution。受控组件不得作为生产绑定。reservation estimates 须依据实际计费来源，C 样例不是确认免费。`file_estimates(currency="USD", money_ceiling=actual_bound)` 必须显式给真实准入金额上限；省略上限 503，不默认零费用预算。受控 SQL 明确预留0.05，pending Usage 未知 money 保留该额度。

Bridge 的 ready / resolve / execute / recover 签名见 MS-T2g-stage-file-port.md。输入原完整 call/spec/ctx，execute 仅原 dispatch CAS 所有者一次调用。A 控制端负责先登记固定命令，再在实际发送前复核当前 root/设备/审批/取消/期限，传输不透明重发。恢复只有当前数据权限与原登记/journal Reader，不调用新执行入口、不新建 attempt、不 reserve/dispatch/retry。

输出 FileReadEvidence 包含完整原 command_ref/receipt_ref、RegisteredReceiptCommand、实际 RunnerReceipt、原 immutable 完整 snapshot bytes、独立登记 selection/next_cursor。C 在 await 前复制严格 wire 嵌套数据，防止 port 修改原 Usage 或内容；核对 command 请求摘要/action/attempt/owner/ctx/参数，验真实 SignaturePort，再核对 UTF-8、范围/游标、64KiB、完整文件摘要和实际片段。

`FileReceiptStore.read_observation(action_id, ctx) -> FileReadEvidence` 提供经当前数据权限和原来源再核对的内部观察；A 的 Artifact/Verification 使用此 owning Reader，不能直接拿 SQL 行、Ref 或旧审批当读取授权。`read_raw` 也经 owning verifier，不把 Blob 校验当文件来源权限。read_observation 的完整 snapshot 是内部核验证据；不得直接暴露给模型/HTTP，Agent/Artifact 正文仍消费已核对 FileContent 的实际 selection。原 `find/read/check/publish` 接 Reconciler 与 `ToolFacade.read_outcome`，返回真实 applied 观察；confirmed/ok 不等于 Task 完成。

## 持久证据与恢复

只用已有具名 DTO：tool.file.command.refs / commands / owners / receipt.refs / runner.receipts / snapshot.refs / selections / fragment.refs / contents / observation.refs，各为 Ref/RunnerCommand/Principal/RunnerReceipt/Location/FileContent。原 Usage 随 RunnerReceipt/ProviderReceipt 保存；原 publish/费用计划/ToolResult 不换版本或 attempt。

FileContent.location 必须是独立登记的实际页/行范围 selection；它不把已分页片段标成请求的 whole。原 call.location 是请求上限，实际页仍必须在该上限内，完整 call 参数和哈希不变。

完整快照与实际片段 Blob 分开；FileContent.content_hash 是完整文件 SHA256，fragment Ref.content_hash 是精确返回 UTF-8 字节 SHA256，Ref.location 固定实际 selection。原观察 Ref 固定命令/回执/owner/device/完整快照/selection，短 SQL CAS 去重；事务锁内无外部 Reader/签名/Blob/BudgetService 调用。普通输入规范化仍 64KiB；具名 FileContent/ToolResult 才使用 512KiB 有界输出信封，容纳转义后的 64KiB 原文。

响应丢失后若 C ProviderReceipt 尚未保存，recover 查独立原 journal，验证原证据后保存原 Usage；原文件变化/删除也不能新开文件。没有原回执为 unknown；有旧 SQL 结果但原 Reader/密钥/根权限不可用则拒绝。pending Usage 省略未知维度，原额度继续 held，不从 ok/读取成功推导 money=0。

`recover_file_accounting(ledger, budgets, ctx) -> UsageSettlement` 只重放已接受原观察的已有账务计划。它严格核对原 call/spec/ctx/attempt/provider、active/accepted Receipt、send intent 和原 Usage，消费当前 BudgetStatePort/BudgetPort 的账务权限。无原计划明确不可用；不读文件正文/root/journal、不用旧数据授权、不产生新 bill 观察或发送，不对缺少的数据推断费用。数据/root/key 撤销与取消之后可以完成原账务回执恢复，文件正文读取仍拒绝；pending 额度仍保留。A 可将此内部入口接到原尝试清理，不作为公开正文读取或工具执行 API。

## A 公共依赖 / 缺口

- 真实注册控制端/传输/Runner journal、当前 owner/session/project/root/device/key 权限、原快照与 cursor registry 由 A 注入，默认缺失 503。D 的真人本机确认仍须整链验收。
- 基线 Runner 只支持 whole/text_span，cursor/lines 的真实生产桥接尚缺；C 数值核验/独立分页登记测试不冒充此生产能力。原 snapshot 必须来自同一原执行，不从局部文本计算整体 hash，不重新读变化文件。
- 当前 ToolLedger.bind 和 A RunExecutionSources.data 均拒绝非空 project_id；C 保留边界。A 要支持项目，需发布统一当前项目准入/恢复数据权限，处理两处入口，不能让 C 自行放宽。跨项目当前拒绝。
- 原费用恢复与新准入分开；数据撤销不能发新执行。C 已提供原固定费用计划不读正文的重放入口；新的确认费用观察仍需 A 的独立当前账务权限/费用 Reader，不复用正文读取授权或自报零费。pending 增量预算及 orphan 协调继续由 A 管理。
- 不改 shared/schema、composition/API/uv.lock、产品目录/flags/模型；没有真实 sources 保持不可用。整链由 A 合入并验收，完整 MS-T2 尚待整链接受。

## 验证

源码：5b7749d0e80f7576362dd5736e0d89ac779e01a5。

- final-unit-ceiling.xml：358单元通过，21.71秒，0失败/错误/跳过。
- m4-sql-resumed.xml：完整新增38节点第一次完成36通过/2分页fixture失败，658.38秒；首轮失败保留。
- page-diagnostic.xml：复现审批幂等request_id冲突1失败，28 deselected；page-fixed.xml：2通过，114.88秒。
- mutation-sql.xml：嵌套证据/Usage异步变更1通过，30.55秒。
- accounting-sql.xml：原费用撤销恢复首次1通过/1断言失败（取消本身修改ledger字段）；accounting-sql-fixed.xml：2通过，16.61秒。
- 最后页范围复验page-range-final.xml：2通过，105.61秒；最后显式金额及页范围final-ceiling-sql.xml：6通过，197.91秒，0失败/错误/跳过。
- 新 SQL 最新回执去重41节点全通过；合原178共219不同SQL节点。verification-index.json索引原XML及每节点最后回执，不声称一次219全通过。真实 OS读取/Ed25519/SQL/Blob/ApprovalService/BudgetService；当前角色/root/控制端/provider元数据/分页/key目录为明确受控来源。
- 原 SQL original-sql.xml：178通过，1368.03秒，0失败/错误/跳过。原text/算术/JSON、检索/索引、70原SQL包含其中，未删改原SQL模块。
- Ruff/Mypy32源文件/format-check71文件通过，diff-check通过；final-ruff/final-mypy/final-format.txt保存。

命令：`. ./ops/start-dev-db.ps1 -Session C`；`.venv/Scripts/python.exe -m alembic upgrade head`；单元 `-m pytest tests/unit/tool -q -p no:cacheprovider`；SQL `-m pytest tests/integration/tool --require-postgres -v -p no:cacheprovider`（原模块与新模块独立basetemp/XML；修复仅选择失败或新增节点，不虚构一次全通过）。独立环境 `uv sync --frozen --extra agent-engine --link-mode copy` 消费原uv.lock，不改锁。

本 Session 独立 55434；所有首次失败、修复、运行中断及最终 XML 保留在 ignored tests/.artifacts/C/MS-T2g，不复制其他 session 凭据或共享 evidence。


## 可消费例子与重复/拒绝

成功：审批引用实际Approval记录；`await facade.invoke(original_request, original_ctx)` 的 kind=ok，payload 为既有 ToolResult，data 为实际 FileContent（实际 selection、整体摘要）；usage_ref 可以引用 pending 结算，仍保持未知额度。`await source.read_observation(action_id, ctx)` 返回当前可读原证据。

拒绝：缺bridge/signatures/current data authority/verifier/executor，发送前 dependency_unavailable；没有实际金额预留上限也明确不可用。原 root/key/data 读取撤销后，invoke恢复/read_raw/read_outcome均不能返回原正文。跨主体/project/provider/attempt、旧摘要或原签名/页范围不符拒绝，不补发。

重复：同原call/ctx恢复引用相同ToolResult/原receipt/原Usage，源桥不再execute/open。改参数/Spec hash/provider/version不选路；unknown原attempt无journal时保留unknown/held，新attempt拒绝。只有既有原费用计划的recover_file_accounting可在当前账务权限下独立重放，不授予读取/执行权。

原共享契约版本0.1、uv.lock未改；摘要见本session verification-index.json和handoff。默认生产端口缺失保持不可用；不开放flags或注册受控组件，不自动进入下一包。
