# MS-I2e：下一轮三个独立组件包

日期：2026-10-08。共同开工标签：`ms-i2e`。本文件规定下一轮范围与消费约束；实际提交、接受和标签 SHA 以 [DISPATCH](../../DISPATCH.md) 为准。

## 1. 为什么可以并行

MS-C3、MS-T2b、MS-R2b 已进入集成分支。下一轮各包只依赖这份已合入代码和既有公开对象，不读取其他 worker 开发中的源码。A 继续建设真实设备归属、登记命令和 Runner authority；以下组件可以先交付，真实组装仍由 A 完成。

| Session / 包 | 本包目标 | 主要目录 | 交付后由谁接线 |
| --- | --- | --- | --- |
| B / MS-C4 | 上下文纯计算的有界缓存 | `src/uaw/context/cache.py`、`model_input.py`、`selection.py`、B 的测试目录 | A 接 Model/Context，默认不开启产品缓存 |
| C / MS-T2c | 统一工具核对入口和明确效果结论读取 | `src/uaw/tool/facade.py`、`reconciliation.py`、可新增 `receipt_lookup.py` | A 接真实回执查找/Reader，再决定 Runtime 挂载 |
| D / MS-R2c | 已签名终态回执的持久保存与恢复读取 | `apps/local_runner/uaw_runner/receipts.py`、D 的 workspace ports/contracts 与测试目录 | A 提供真实登记命令 Reader 和可信通道 |
| A / MS-I2f | 设备/通道归属、不可变命令登记及当前权威 | A 保留的 `src/uaw/run/`、`shared/`、composition 和独立集成测试 | A 集成；实际 IPC/执行仍按原门槛开放 |

B 的工作是 P1-02 上下文组件的局部优化，参考 P4-04 的缓存边界；不提前宣称整套多层缓存完成。C/D 的工作分别补齐 P1-03/04 的恢复组件，不提前验收完整 MS-T2/MS-R2。

## 2. B / MS-C4：只缓存已经校验过的数据的纯计算

### 输入与输出

- 保持 `GenericModelInputs.resolve(ref, ctx) -> ModelPrompt` 和 `TokenCounter.count(reading) -> int` 的既有签名、语义与结果。
- 可选缓存通过内部构造参数注入；新增 `context/cache.py` 属于 B，不修改 `shared/cache.py`、公共 DTO、配置或 Model provider。
- 缓存对象仅包含可重建的格式化文本、序列化或 token **估算**。原文、快照、权限、审批、费用、模型输出仍由原所有者保存。
- 内部条目/统计可用 dataclass；不向公开 schema 加私有字段，不新增隐藏的持久 `Object` 状态。

### 必须实现的策略

1. 先执行现有快照、当前 authority、Reader、scope、epoch、规则/工具、来源版本、窗口和取消检查，之后才允许使用缓存。所有原有 await 后复查与最终复查保留。
2. 缓存键包含稳定主体与完整 scope、Run、固定模型/权限、purpose、快照及 epoch、实际完整 Reading 内容与元数据、规则/工具 schema、窗口/预留和算法版本。影响某项纯计算的字段都必须参与键。token counter 的缓存至少包含 counter 身份/版本与完整 Reading。
3. 不缓存 Reader 返回的访问许可、CompositionBinding、旧 `Reading` 或旧 `ModelPrompt` 的授权结论。每次仍读取当前来源和分类；相同正文的 trust/required/requirement_ids 变化不能复用错误结果。
4. 第一版只做进程内、主体隔离、条目数/字节数有上限的可淘汰缓存；不做跨主体共享、Redis、语义相似命中、模型响应缓存、负权限缓存或在途模型调用合并。
5. 不把同 ID/版本、不同内容视为合法命中；原校验应先拒绝。无 hash 或无法形成完整键时绕过缓存。返回内容复制或保持不可变，调用方不能修改后续命中。
6. miss、淘汰或缓存自身故障可以重新计算；权限/来源/取消/窗口失败必须原样失败，不能用缓存吞掉异常或回退到理解模板。缓存容量零等价于关闭。

### 验证与交付

覆盖相同输入的纯计算调用次数减少、文本/工具/元数据/模型窗口改变失效、跨主体/Run隔离、撤销/取消后即使命中也拒绝、容量/字节上限和结果变异隔离。复跑现有 Context 单元和 SQL；SQL 用例使用不同于单元测试的模块名。只报告实际节省的本地计算次数，不宣称提供方 prompt cache 命中、Token 减少或真实延迟收益。交接给出可选注入例子和默认关闭分支。

## 3. C / MS-T2c：由可信来源找到原尝试的回执

### 本轮批准的内部 port

在 C 所有目录定义 `ActionReceiptLookupPort.find(action_id: str, ctx: TrustedExecutionContext) -> Ref | None`。这是内部注入接口，无新 wire 字段：

- 从 owning domain 的已登记动作/原 attempt 和实际来源查找固定回执；独立检查主体、Run、action/attempt/provider 和当前恢复读取权限。
- 返回实际固定版本 Ref，不能接受模型附加的 `receipt_ref`，不能把任意 Ref 或超时推断作为来源。
- `None` 只表示本次未找到可读回执，保留 unknown 与已有结论/额度。没有 port 则明确 dependency_unavailable。
- 生产实现由 A 接入；受控 SQL fixture 只算组件来源。Tool 不读取 Run 的私有预算/政策表，也不直接查询未来 Runner 私有账本。

### 入口与策略

1. 增加 `ToolFacade.reconcile(request, ctx)`，输入严格使用现有 `ReconcileRequest`，返回现有 `RuntimeToolruntimeReconcileResult`。仅传 `action_id/expected_revision`；额外参数拒绝。构造时显式注入 lookup 与现有 `ToolReconciler`，默认都不可用。
2. request/action 必须匹配真实原 attempt 的 ToolLedger 绑定；lookup 的结果仍交 `ToolReconciler` 做 Reader、签名/来源、精确 Ref、证据和费用核对。查找不能赋予执行权限，也不能生成新 attempt、reserve、dispatch、retry。
3. 缺口、CAS、同版本变化、来源撤销、取消后的原尝试核算保持 MS-T2b 语义。核对不经过用于**新执行**的 `_access` 准入；由恢复 Reader 校验当下数据访问，不能因此绕过来源权限。
4. 提供内部 `read_outcome(action_id, ctx) -> ToolReconciliationReceipt` 消费方法，读取该动作已接受的真实回执并再次校验当前来源/证据/绑定。无已接受回执不可推断 outcome。
5. `EffectRecord.confirmed` 表示结论确定；必须查看 receipt 的 `applied/not_applied/unknown`。核对 `ok` 不等于工具成功、Task 完成或获准重试。费用是否完成独立保留，不能用费用回执替代效果证明。
6. 不新增 HTTP、实际 dispatch、工具目录或 feature flag；不扩 `EffectRecord` 字段。若需要公开结果结构调整，提案交 A 后另发版本。

### 验证与交付

真实 SQL 验证已绑定动作查找、无回执/缺 port、跨主体/原 attempt/provider 拒绝、重复与重启、已接受回执读取、确定未应用与费用独立、撤销/取消后的恢复。断言没有新 reserve/dispatch 或 attempt。保留原 43 项 SQL，并将新 SQL 文件命名为 `test_*_postgres.py` 等独立名称。交接提供 facade 接线与返回示例，不把受控 lookup 登记为产品来源。

## 4. D / MS-R2c：保存真实终态回执，供后续恢复

### 本轮批准的内部边界

在 D 所有目录定义 `ReceiptCommandReaderPort.resolve(command_ref: Ref, *, authenticated_principal: Principal) -> RegisteredReceiptCommand`。内部不可变 `RegisteredReceiptCommand` 只含 `command: RunnerCommand`、`device_id: str`、`owner: Principal`；不新增公开 wire DTO。

Reader 从独立登记命令源及当前通道/主体归属取得这些值，校验固定 Ref 版本/摘要及当前恢复读取权限。传入的 command_ref 不是授权；不能从待保存 receipt 或请求体构造 command/owner。实际 Reader 由 A 接线，缺失默认不可用。恢复读取与新执行权限分开，原 Run 取消/过期不自动禁止费用数据恢复；设备/key/数据读取撤销仍须执行。

### 内部服务输入与输出

- `publish(command_ref, receipt_data, *, authenticated_principal) -> Ref`：保存实际收到的 `RunnerReceipt` 原始数据，经严格解析/签名/绑定验证后返回真实 `runner_receipt` 固定 Ref。
- `read(receipt_ref, *, authenticated_principal) -> RunnerReceipt`：读取实际已保存版本，再核验当前命令源、主体/设备归属和 device key；不伪造或重新签署结果。
- `authenticated_principal` 只能由可信适配器传入；本包不新增网络接口。

### 必须实现的策略

1. 使用既有真实 Ed25519 verifier 和 receipt domain/device key 角色；比较登记 command_id、原 attempt、usage.attempt_id、action 和资源/版本，复用 `RunnerProtocol.verify_receipt` 的既有检查。
2. 独立绑定 command 的完整 owner 与 device，不以 command/receipt 自报主体当依据。关键 await/外部检查后重读登记源；内部线程处理不得阻塞事件循环。
3. 第一版仅保存 `ok/failed/cancelled` 终态；`waiting` 返回明确不支持，未来进度序列另立版本。按 owner kind/id、device、command、attempt 建唯一键；实际首个终态 revision=1，相同已验证内容重放返回原 Ref，同键不同内容冲突，不覆盖历史。
4. 用开发期 SQLite 持久 journal，配置到独立临时/私有目录；不决定 D01 正式权威。只保存已验证公开 RunnerReceipt、固定命令 Ref 和必要索引/摘要，不保存私钥或认证凭据，不用任意 `Object` 增补签字字段。
5. 即使已保存，也要在每次读取时复核当前签名 key、源数据授权和版本/摘要；同 Ref 内容变化拒绝。来源不可读时保留本地记录，不新建“未执行”回执。
6. `ok` 是具体 Runner 操作回执，不能直接映射 `ToolReconciliationReceipt.outcome=applied`；`failed/cancelled` 也不能推断 not_applied 或零费用。费用和未知维度保留原 Usage。不得从 admission 记录合成回执。
7. 不发送命令、不执行文件/进程、不接可信 IPC/配对 V2、不选择 D03、不改变授权根或功能开关。

### 验证与交付

真实签名、当前 key 撤销/角色错误、跨设备/owner/attempt/action/资源绑定、相同回执去重、冲突回执、实例/进程重建与并发唯一提交、固定 Ref 摘要、源撤销、取消后恢复、waiting 不支持。测试仅使用本 session 临时 SQLite、真实密钥原语和明确受控的登记源。交接列出 SQLite 故障与中断恢复语义，不声称已经收到真实 Runner 执行结果。

## 5. A / MS-I2f 与合入顺序

A 负责实际设备归属/通道状态与不可变请求/命令登记，先发布对象、来源和方法约束，再提供异步当前 authority，组合真实政策、配置/开关、预算/审批、根绑定、lease/fence 和撤销。生产 authority 不从 command 声明拼出；缺配对/通道/资源来源拒绝。可信 IPC、OS 凭据实连和 D03 执行模式仍是后续门槛。

三个 worker 的完成顺序不固定。A 收到一个包即可审阅、合入和回归，发布版本；开发中的 worker 保持自己的固定 `ms-i2e`，不在中途混入别人的新接口。下一轮仍沿用现有三个 worktree，A 不代为切换或改写 worker 分支。共享修改只由 A 发布。

各包交接必须包含源码提交、单独 handoff 提交、实际基线、修改清单、输入/输出示例、实际检查回执和缺失依赖；默认关闭或未挂载不算完整能力交付。SQL 未配置时照实记录，由 A 在实际 PostgreSQL 重跑。以上安排不会跳过原 50 轮的真实场景验收门槛。
