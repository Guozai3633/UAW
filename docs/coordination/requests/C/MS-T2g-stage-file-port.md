# MS-T2g M1：file.read 固定端口与证据

- 分支：dev/tool；实际基线：abb4590f2bfe53c601e0f6a4a3b65447ba4ec502（ms-i2j-start）。
- M1 源码：c8b5676d4cb65a65a38391b304095600b0ffed54。
- 范围：C Tool/测试；不注册产品工具，不开放 file_access，不改公共 DTO 或用户模型。

## C → A 注入接口

`uaw.tool.providers.file_read.file_read_spec(provider_ref)` 固定 file.read@1、read、workspace.process、file_access、无自动重试。
`ToolFileReadBridgePort.ready()` 检查实际控制端、当前权限、命令登记、签名与 journal 来源；缺任一来源须 unavailable。
`resolve(call, spec, ctx) -> tuple[Ref, ...]` 读取当前工作区/root/项目权限与版本，不能发送。
`execute(call, spec, ctx) -> FileReadEvidence` 仅由原 Tool dispatch CAS 胜者调用；发送前登记固定命令；一次发送，不透明重连/重发。记录固定 command_ref、receipt_ref 和 journal 后再返回。
`recover(call, spec, ctx) -> FileReadEvidence | None` 重新检查当前数据权限，查原登记/原 journal/原快照，不能调用 execute。None 为未知，没有零费用或未执行含义。

内部 FileReadEvidence 包含固定 content Ref、RegisteredReceiptCommand（完整 owner/device/RunnerCommand）、实际 RunnerReceipt、原始完整文件 bytes、登记 selection 与 next_cursor。不是公共请求 DTO，也不接受模型传入证据。A 提供实际 bridge 和 SignaturePort；C 不读取 OS 文件或调用 D 开发分支。

命令 request_ref 固定到原 action_key 和原 ValidatedCall 摘要，parameters 精确为 file.read 参数；完整 ctx/spec/attempt/provider 由原 Tool 账本绑定。回执引用按既有 Runner journal ID 和实际签名回执摘要核对。Runner ok 之后仍需核对实际内容。

## 内容与恢复边界

严格 UTF-8；原完整快照上限 1MiB，返回片段上限 64KiB UTF-8，不规范化原文/换行。FileContent.content_hash 是完整原文件摘要；片段必须由真实原快照和登记范围重新计算。cursor 来自独立可信登记，绑定原请求/工作区/路径/原摘要/范围；恢复禁止重新读取变化后的文件冒充原结果。

file.read 参数和普通 Tool 输入仍采用原 64KiB 规范化边界；仅具名 FileContent/ToolResult 的输出信封显式有界至 512KiB，容纳完整 64KiB 原文及 JSON 转义。

Usage 消费原 RunnerReceipt（可能 pending 且未知维度缺省），不推导免费。file_estimates 只是显式准入上限样例；A 必须按实际本地计费来源提供 reservation 计划，不能作为已确认收费证据。

## 公共最小缺口 / A 消费方影响

1. 当前 ToolLedger.bind 和 RunExecutionSources.data 拒绝非空 project_id。C 保留拒绝，不能单方面解除项目校验。若生产 file.read 要用非空项目，A 需发布统一项目准入/当前恢复数据权限契约并处理两个入口；没有发布前该场景不可用。
2. 基线 ReadOnlyRunner 尚拒绝 cursor/lines，支持 whole/text_span。C 接口可核对独立注入的真实分页登记；生产分页/lines 须 A/D 接线并验证，不能把受控测试 Reader 注册为产品能力。
3. FileContent 没有独立片段摘要；A 控制端需提供原 immutable snapshot Reader 与登记 selection/cursor，固定到原 command/receipt。没有原快照不能从返回片段验证整体摘要，拒绝而非新读替代。
4. A 负责实际控制端/当前工作区权限/合法 provider/角色/目录/组装；D 负责本机确认。恢复 Reader 与新执行权限分开，撤销数据权限立即阻断读取，取消/过期不新建 attempt 或发送。

## 阶段验证

27 项 file evidence 单元通过（真实 Ed25519 验签；受控 keys/回执来源，不声明真实 Runner dispatch）。ruff format/check 与 mypy file_read/schema 通过。独立 C 数据库 55434 已 dot-source ops/start-dev-db.ps1 -Session C 并 alembic upgrade head。
首轮失败（严格嵌套 JSON fixture 导入及 Windows 超长参数测试 ID）及修复后回执保存在 ignored tests/.artifacts/C/MS-T2g/m1-unit*；M2–M4 和真实 SQL 尚待完成。阶段交付后继续本包，不等最终集成。

## M2 已交源码与构造样例

M2 源码 SHA：6abd666262df449a7e6d3c374613a7326944250b。FileReceiptStore(ledger, blobs, provider_ref=..., provider=..., access=actual_current_data_access, bridge=actual_bridge, signatures=actual_signatures)；source.verifier = FileReadVerifier(source)；executor = FileReadExecutor(source, provider=...)。

使用原 ToolExecutorRouter 的 ToolExecutorBinding(完整注册 ToolRef, provider_ref, executor, executor.check)，verifier 路由使用 ToolOutputVerifierBinding(相同完整 ToolRef, provider_ref, source.verifier)。ToolResults(source, 原 ToolReconciler(..., receipts=source, evidence=source))；ToolFacade(..., lookup=source, reconciler=...)。FileResourceReader(provider_ref, bridge) 注入原 ApprovalAuthority 资源 Reader；恢复 access 是当前数据权限，不能复用新执行 gate 或审批作为读取授权。

ToolInvocation 使用原 ledger/ApprovalService/BudgetService、完整 estimates 和 prepare=router.check。bridge.ready/signatures 缺失发送前 503。命名 RunnerCommand/RunnerReceipt/Principal/Ref/Location/FileContent、原完整快照及实际片段 Blob 持久化；不扩 EffectRecord。35 项文件单元通过，Tool mypy/ruff 通过。M2 首次 8 个 fixture Principal 缺 auth_session_id 的失败已保留并修复；继续 M3/M4 真实 SQL，不声称生产接线完成。

最终契约复核：FileContent.location 核对实际登记页/行 selection，原call.location仍固定请求范围；未分页 whole/text_span 兼容。file_estimates(currency="USD", money_ceiling=actual_bound) 最终要求显式货币预留上限，省略返回dependency_unavailable，不允许未知Runner费用取得默认零金额预算。A已有实际估算向量可直接注入ToolInvocation，受控SQL数值不当产品费率。固定Spec字段/哈希未改变。最终源码以final-wiring和handoff记录为准。
