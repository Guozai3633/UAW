# MS-I2g：完整能力包与四 session 并行安排

日期：2026-10-08。共同代码基线从 `ms-i2f2 / eee46a2` 推进到固定准备标签 **ms-i2g-start**；SHA 见 [DISPATCH](../../DISPATCH.md)。此前 B/C/D 已同步 ms-i2f2，先接收本次环境和分工更新，再开始新包。

## 1. 调整原因和共同规则

上轮 worker 包是小型组件增量；数据库未在各 worktree 准备，SQL 检查集中到 A。A 又承担接口、接线和全量回归，形成持续等待。上轮两批测试累计 1443.84 秒，另有重复运行和修正成本；这不是四 session 同时推进的有效安排。

本轮按一个完整能力划分一个包，每包四个连续里程碑。完成前两个里程碑可以先提交可审阅版本和接口样例，报告实际 SHA；继续同包后两个里程碑，无须等待 A 最终接受。A 可以读取已提交接口提前接线，正式合入仍逐包操作。禁止读取其他 worker 开发分支或未经版本发布的公共文件。

这两个交付点表示开发交接；不表示整包或产品验收。无法实现的依赖必须明示，不回显调用参数作为权限。公共 schema/锁/迁移/composition/API 归 A；局部 Python 构造接口可按本页实现，新增公共对象先提案。发现公共缺口时继续同包独立工作，A 优先处理提案。

| Session | 包 | 完整目标 | 与其他包的开发依赖 |
| --- | --- | --- | --- |
| B | MS-C5 | 通用上下文的真实登记、当前权威、来源读取到模型输入 | 只消费已合入的 SQL/blob/Run/policy/model ports |
| C | MS-T2d | 只读工具调用的持久编排、真实本地适配器及恢复来源 | 通过内部 executor/Reader ports；不依赖 D 新实现 |
| D | MS-R2d | 实际控制密钥签名、本机授权根来源和恢复适配装配 | 只消费已发布 RunnerRoot/Signing/Mapping ports |
| A | MS-I2g | 独立验证环境、原 Run/政策来源、接线和跨模块验收 | 准备与接线可提前；最终接受等待三个实际交付 |

## 2. B / MS-C5：通用 Context 完整来源链

### 目录和入口

新增 `src/uaw/context/registered.py`、`authority.py`、`readers.py` 归 B；既有 facade/contracts/ports/repository/composer/model_input 及 B 测试可修改。`seed.py`、`intent.py`、Model/Run/shared/composition 仍归 A。

采用已有 `ContextRequest`、`InternalContextRulesRequest`、`InstructionRule`、`ModelToolSet`、`ContextBlock`、`PreservationSpec`、`TrustedExecutionContext` 和 Ref；可用多条明确 schema 的记录保存配方/绑定，文本进入已有主体隔离 blob。不要把对象塞入无约束 Object，也不新增永久业务表或迁移。

建议主对象 `RegisteredContextInputs` 负责登记和修订；`RegisteredCompositionAuthority` 实现现有 `CompositionAuthority`；`RegisteredContextReader` 和 RuleProvider 读取这些实际记录。可在本领域调整类名，但提交阶段必须给出固定接线签名和实例样例。

内部登记签名固定为：

```python
await inputs.register_material(text: str, ctx: TrustedExecutionContext,
    *, authenticated_service: Principal, expected_revision: int, meta: RequestMeta) -> Ref
await inputs.register_rule(rule: InstructionRule, ctx: TrustedExecutionContext,
    *, authenticated_service: Principal, expected_revision: int, meta: RequestMeta) -> Ref
await inputs.register_recipe(request: ContextRequest, rules: RulesRequest,
    tools: ModelToolSet, ctx: TrustedExecutionContext,
    *, authenticated_service: Principal, expected_revision: int, meta: RequestMeta) -> Ref
```

构造时显式注入完整 controller Principal、records、blob、当前 Run/政策来源；没有可信认证 adapter 时不向 HTTP/模型暴露登记入口。`register_material` 始终登记 material/external，不能由正文或 caller trust 字段升格。`register_rule` 只接受可信控制入口和本 Run/conversation 作用域；平台规则不是用户材料登记的副产物。文本/条目/单次请求容量要有界。

ctx 的当前 Run/完整主体/session/固定模型/范围由实际来源核对；body 不接受额外 owner、approved、trusted_context。原文通过已有 Run input Reader 读取，不能改写或把理解摘要替代原文。配方限定已实现 purpose（至少既有 `agent_step`），其他目的明确 unavailable，不新增 `agent_loop` 枚举。epoch 取实际登记 revision 并在修订时推进，不接受模型凭空指定当前纪元。

空工具集可以显式登记；非空工具集必须经过注入的当前工具验证来源及固定版本检查，缺该来源不能放行。技能/记忆/Board/本机文件尚未接入时不生成伪记录或默认规则。取消、删除、策略/材料/规则/工具版本变化均在 resolve/verify/read 和快照提交后复查。

### 四个里程碑

1. **登记链**：主体隔离 blob＋命名 SQL 记录，CAS/幂等/修订/撤销，可信入口与材料分类；提供小型真实登记脚本或接线样例。
2. **当前权威和 Reader**：实际配方 epoch、规则、原文保护和工具集来源；接现有 CompositionAuthority/Reader/RuleProvider，结束测试目录 fixture authority 的依赖。提交阶段版及构造签名。
3. **完整输入链**：真实登记→Context.build→固定 snapshot/ref→GenericModelInputs/引用解析；缓存开关均可运行，理解链兼容。Model 实际网络调用仍待 D06，不能替换用户模型。
4. **整包验证**：真实 PostgreSQL＋blob 重启、主体隔离、修订失效、并发 CAS、撤销/取消、注入材料、引用定位与原文保护；保留原 Context 回归。至少一条办公/分析材料输入的可审阅组装示例，不宣称真实 LLM 成果质量。

## 3. C / MS-T2d：只读调用编排和持久结果源

目录仍为 `src/uaw/tool/`、C 单元/SQL测试、requests 和 handoff。建议新增 `invocation/dispatch.py`、`results.py`、`receipt_store.py`、`providers/text.py`。不依赖 D 开发中的 IPC/执行器，也不提前建设安装/写入/exec。

实现可选内部 `ToolExecutorPort`，签名：

```python
await executor.execute(call: JsonObject, spec: JsonObject,
    ctx: TrustedExecutionContext) -> JsonObject  # 严格 ProviderReceipt
```

executor 只接固定 ValidatedCall/ToolSpec/可信 ctx；构造绑定 adapter，不接受模型自报 provider、owner、已批准或效果。ProviderReceipt.raw_result_ref 指向实际保存的响应；另由当前 Reader/规范器核对业务 output_schema 和固定内容，不能直接把 ProviderReceipt 当 ToolResult。

内部持久结果源的方法：

```python
await source.publish(receipt: JsonObject, ctx: TrustedExecutionContext,
    *, authenticated_provider: Principal) -> Ref  # ToolReconciliationReceipt
await source.find(action_id: str, ctx: TrustedExecutionContext) -> Ref | None
await source.read(receipt_ref: Ref, ctx: TrustedExecutionContext) -> JsonObject
```

源从已登记 action/attempt/provider 和真实保存内容核对绑定；provider 身份取可信 adapter，完整 Principal/当前恢复数据授权要复查。source 可实现既有 Lookup/ToolReceiptReaderPort，不默认挂载生产。回执使用已有具体 schema；复用原账本、固定费用计划和 CAS，不改变公共 ReconcileRequest。缺真实权限/原数据/验证器明确不可用。

### 四个里程碑

1. **调用编排**：串联 normalize/固定目录与 access→审批 waiting/批准后 recheck→ledger 原尝试→预算 reserve→当前闸门→持久 dispatch 意图。send owner 必须持久 CAS；重放不能获得第二次发送权，外部 await 不在 SQL 锁内。缺 executor 在任何发送前拒绝。
2. **实际只读 adapter**：提供一个受控内部 `text.inspect`（纯文本长度、行数、SHA256 等，参数/输出 schema 明确、容量有界）；真实计算和实际结果保存，不联网、不读取用户目录。提交阶段版的 executor/result source 接线样例。该工具不是模型复杂度/语义判断的替代，也不擅自注册为产品目录。
3. **结果和恢复链**：严格规范 ProviderReceipt→业务 ToolResult，实际证据/Usage/固定 Ref 保存；效果与费用分别恢复，接既有 reconcile/read_outcome。发送后超时/取消/响应丢失保留 unknown，不推断未执行或零费用，不自动换 attempt 重发。成功只读结果也须校验实际输出。
4. **整包验证**：独立真实 SQL 覆盖批准/拒绝、预留前拒绝、发送一次、并发/重启重复、输出不合规、取消、失联、费用结算中断和旧结果当前权限；保留原 70 项 SQL。通过实际 text adapter 完成一条 invoke→结果→重新读取链，不使用合成 Runner 回执证明执行。

公开 Tool Runtime 接线、实际 ToolAccess/资源 Reader 和产品启用由 A 集成接受；完整 MS-T2/P1-03不因局部通过而自动验收。

## 4. D / MS-R2d：控制签名和授权根适配

目录仍为 `apps/local_runner/uaw_runner/`、D workspace/binding/contracts/ports/repository、D 单元/本机集成测试。建议新增 `control_signing.py`、`root_source.py`、`assembly.py`；不修改 shared/公共 schema/锁/composition。

实现现有 `RunnerCommandSigningPort.sign/verify` 和 `RunnerRootSourcePort.current`；准确签名见 shared/ports，输出分别是 RunnerCommand、None、RunnerRootSnapshot。接真实 `ProtectedSigner`、CurrentKeyDirectory、CredentialStorePort、本机 RootRepository/原选择记录以及独立 `RunnerPrincipalMappingPort`。缺任何身份或授权来源明确 unavailable。

### 四个里程碑

1. **控制签名 adapter**：控制服务的 key→device→credential_handle 映射在可信构造/登记源固定，不取自命令 body；control/device role 分离。严格验证 RunnerCommandDraft，只增加 signature，不改正文；verify 实查当前控制 key、撤销和密码学结果。取消/期限/异步密钥读取后的变化要处理。
2. **真实 OS 密钥验证**：复用现有 WindowsCredentialStore，无 JSON/明文文件回退。仅在本包随机测试 namespace/handle 中生成、签名、读取并 finally 清理；不操作已有用户凭据，不输出秘密。真实 OS 后端不可用时如实记录，其他原语测试不能代替 OS 回执。提交阶段版构造接口。
3. **授权根来源**：从真实已消费选择及持久 grant/本机目录身份取得 root/workspace/revision/有效期；经独立 owner/session 映射与当前 key/撤销校验，返回 opaque RunnerRootSnapshot，不暴露本机路径。旧记录缺证明/有效期时明确拒绝，不能补无限期限。平台通道和选择仍缺时不从命令 ctx 自证授权。
4. **装配与本机验证**：给出 RootBindings＋签名 adapter＋现有 authority/ReceiptReader 的装配样例；临时根验证重启、替换/链接逃逸、过期、撤销、跨主体/密钥和签名域错误。journal/admission 保留回归。可信 IPC/真实用户确认尚未完成的部分列明，不自制批准回执。

本包不实现文件动作、安装、写入、exec 或配对 V2；这些需要 D03 和实际 IPC/用户确认。它完成签名和本机根两个实质后端，避免 A 再单独重写这些领域适配器。

## 5. A / MS-I2g 与验收方式

A准备独立数据库环境、既有 Run/固定模型/当前政策服务实例和组装位置，及时审阅阶段版接口及公共提案，推进可信 channel/动作资源来源；不承揽 B/C/D 领域实现。C 的只读 adapter先用于跨模块诊断任务，实际用户调用仍需当前权限和产品开关验收。

收到阶段版后 A可写接线，不等三个最终包齐才启动。worker本包继续固定 ms-i2g-start，公共更新只在明确兼容点发布消费版本。最终逐包合入；模块 SQL 在 worker 独立库完成，A复查真实回执及关键链路，受影响模块＋跨模块回归优先，全量在集成里程碑执行一次。有具体失败/公共契约变化时扩大回归，不复制上一轮所有耗时检查作为每个小提交的默认动作。

## 6. 独立数据库和交付

在各自 worktree 的 PowerShell 中运行（将 B 替换为 C 或 D）：

```powershell
. ./ops/start-dev-db.ps1 -Session B
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m pytest tests/unit/context tests/integration/context -q --require-postgres --junitxml=.data/MS-C5.xml
```

Session A/B/C/D 各使用 loopback 55432/55433/55434/55435；Docker project/volume分别隔离，秘密只生成在当前 worktree `.data/dev-db.env`，不复制 A 配置、不提交、不打印 URL。worker只迁移和测试自己的数据库，不执行 down -v 或清空其他库。D不用SQL的本机用例无需启动PG。

交付需记录实际源码/阶段版/最终 SHA、模块文件清单、构造与输入输出样例、真实用例数/0错误跳过或明确未验证原因、原用例回归、A接线要求。测试回执写自己的 ignored `.data` 或 `.artifacts`；不要改共享 environment/JUnit/生成文档。最后工作区干净，提交 handoff；不自动进入包外能力。
