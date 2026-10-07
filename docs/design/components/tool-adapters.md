# 领域与外部适配器：开发设计

节点 `tool.adapters` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

转发到 Workspace、控制工具或第三方 API。

- 计划主文件：`src/uaw/tool/adapters.py`。
- 统一业务入口：`dispatch`；只允许所属 facade 或获准适配器调用。
- 上层归属：`tool`。该节点是逻辑组件，不默认独立服务。
- 硬约束：平台凭据不进入任意任务代码。

## 输入、输出与调用协议

输入请求 `ToolAdaptersRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
provider_kind: local|runtime|mcp|api; validated_call: Ref; deadline: Timestamp
```

领域输出：原始结果及效果状态。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 按不可变ToolSpec选择适配器，不让模型指定任意服务地址。
2. 运行时控制工具进入目标Runtime公共facade。
3. Workspace动作进入受控Runner/沙箱路径。
4. 第三方调用由受控服务凭据与数据策略适配。
5. 保留原始返回与实际效果信息交Normalizer。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

适配器不拥有目标Runtime业务状态，只持调用/协议关联引用。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 不支持参数返回unsupported而非静默忽略。
- 提供方连接错误类型化。
- 反序列化失败保留原始受控引用。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

协议池并发有界；适配器超时不重置Run截止。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- agents.create确实进入Agent Registry。
- process.exec不在Runtime服务器环境执行。
- API密钥不进入命令参数。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/tool.adapters.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：准入后的调用 | [调用与副作用账本](tool-effects.md) |
| 本节点 → 下游 | 调用：MCP提供方路径 | [MCP 连接与适配](tool-mcp.md) |
| 本节点 → 下游 | 数据/引用：实际返回 | [结果规范化与分页](tool-results.md) |

## 参考与需要验证的选择

- [Tool · 调用/MCP/效果](https://app.notion.com/p/3e96ccd32c8780fab75dd0b4c21fe7fb)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · 审批/复核](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

