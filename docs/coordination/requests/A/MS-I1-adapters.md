# A 对第一波提案的处理与 MS-C2 消费说明

日期：2026-10-07。实际发布版本只以 [DISPATCH](../../DISPATCH.md) 的固定标签/SHA 为准。

## B / MS-C1-wiring：已按限定范围采用

组装函数是 `uaw.composition.compose_understanding_context(records, policies)`，返回 `IntentContexts`，其 `.components` 为 B 的 ContextComponents。生产组装根与真实 SQL fixture 使用同一函数。A 的适配文件为 `run/context.py`、`model/context.py`、`context/intent.py`；均归 A，B 不改这些文件。

| port | 实际适配器 | 当前可用范围 |
| --- | --- | --- |
| Reader / input | RunContextSources | 已受理 Run 的原文与补充固定版本；whole/text_span |
| Cancellation | RunContextSources | 活动 Run 当前取消账本/状态；未受理预览不可用 |
| Reader / rule | UnderstandingRules | 唯一包内理解指令，固定版本与实际内容 hash |
| RuleProvider | UnderstandingRules | 唯一平台指令；多规则/技能/项目继承不可用 |
| ModelWindowProvider | FixedModelWindow | 用户固定政策/目录窗口；当前权限和提供方复核 |
| ModelInputPort | StoredModelInputs | 使用注入的 IntentContexts 解析 understanding；缺注入则失败 |

输入 raw text 和真实来源 Ref 由 adapter 决定，调用方不能赋予平台信任。数字版本仍代表 SQL 修订；未提供 hash 可由 Reader 加入实际 hash。text_span 使用 Python Unicode 字符偏移，hash 只覆盖返回片段；无 strip/NFKC/换行转换。`latest_required` 尚无该 Run 的刷新语义，明确不可用；不要默默解释为 pinned。

`ctx.model_policy_ref` 存在时必须匹配 Run 的固定政策；理解专用 builder 在其缺省时只从持久 Run binding 补充到内部副本，不改调用方对象。通用 Selector 仍要求可信上下文明确包含该 Ref。B 不得从模型建议或无来源的字符串构造政策。

模型窗口多余 512 的空间只是 envelope 估算。ModelProviderPort 新增 `estimate_input_tokens(ProviderRequest) -> int`，唯一批准 adapter 计算真实原生 JSON 字节数；最终 Gateway 复核完整 schema/tools。B 的 Composer 也要保留输出空间并显式传入完整 ContextRequest.preserve，不能只依赖候选被选择。

现有 understanding 专用存储由 A 保持。B 的 MS-C2 新建通用 composer/repository/references，消费已有 PostgresRecordStore/TransactionalStore/Ref/ContextSnapshot 契约；自有 integration/context 测试使用 root database/principal fixture，SQL运行由 A安排。来源/规则/能力集合必须来自实际依赖；缺任一依赖仍返回不可用。不能为通用 agent_step 默认套用理解指令；规则来源没有提供时不得假装已装配。

公共 schema、shared ports/contracts、uv.lock、提示词不变。通用 build 不在 MS-I1 绑定；B 若需要 composition、迁移或 DTO 变更仍提交提案，由 A 发布真实新基线后消费。

## C / C-001：组件与接口采用，MS-I2 接线待继续

- 采用 ToolRegistry 的固定版本/CAS、安全 schema 子集和内部 Access/Precheck/Recheck port；目录命名空间约定为工具配置，不能与平台 ConfigurationSnapshot 互相解析。未来持久目录需独立记录命名空间，不将 configuration Ref 视为任意读权。
- Model 输出工具建议的 Ref 已改为 configuration；真实模型响应的受控协议例子能经过 C 的 normalize。产品目录仍空。
- 预检、审批等待、复核、持久 dispatch/effect/settle 的状态所有者仍是 Run/Tool 的既定边界。A 尚未提供生产适配器，不以 facade 绑定或伪 wait_ref 声称完成。
- EffectState 不新增“未发生”状态；写恢复仍拒绝盲重试。对账证据与批准的恢复契约在 MS-I2 决定并发布，MS-T2 当前不派发。

## D / R1-001：组件采用，真实协议决定待 MS-I2

- 采用独立权威上下文、固定 workspace 版本/根映射、lease/fence 和原命令回执复核约束。测试替身及内存仓储不接生产，根 path 不传给模型。
- 回执结果分支互斥已由 D consumer 拒绝；公共 schema 收紧的提案保留，MS-I1 未修改公共 schema，不能认为已统一到所有消费者。
- 签名算法/域分离、可信 IPC/公钥持有证明、nonce/根选择原子消费及持久 tombstone 的真实实现尚未发布。不因为组件已接受就开放配对/执行。
- 检查后路径替换必须由执行器在实际文件句柄上再次校验；当前路径组件没有消除 TOCTOU，也不是 OS 沙箱。
- MS-R2 尚未派发；D01/D03 未自行定案。
