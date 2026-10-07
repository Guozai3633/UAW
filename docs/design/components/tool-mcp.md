# MCP 连接与适配：开发设计

节点 `tool.mcp` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

协商、能力发现、会话生命周期和结果规范化。

- 计划主文件：`src/uaw/tool/mcp/facade.py`。
- 统一业务入口：`connect/discover/call/close`；只允许所属 facade 或获准适配器调用。
- 上层归属：`tool`。该节点是逻辑组件，不默认独立服务。
- 硬约束：连接不授信，重连不重放未知写调用。

## 输入、输出与调用协议

输入请求 `ToolMcpRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
provider_ref: Ref; connection_revision: int; transport_config_ref: Ref; session_id: ID?
```

领域输出：命名空间能力与协议结果。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 读取有效账号/提供方引用，不加载凭据进模型。
2. 建立协议会话并发现能力。
3. 工具名放provider命名空间，能力schema与版本入Registry。
4. 远端调用通过统一Tool闸门与结果规范化。
5. 健康变化有限重连并更新能力revision。
6. 撤销关闭会话和失效绑定，未知写不重放。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

Tool持有协议Session，控制层持有账号授权；连接状态不能充当动作批准。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 协商不支持返回protocol_mismatch。
- 掉线写结果可能unknown。
- 能力变更让旧绑定stale。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

会话复用有TTL/并发/健康限制；远端大结果受控分页。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 不同provider同名工具不混淆。
- 撤销后旧session不可调用。
- 远端描述不会变系统指令。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/tool.mcp.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 提供方绑定 | [tool.mcp.provider](tool-mcp-provider.md) | `src/uaw/tool/mcp/provider.py` |
| 协议会话 | [tool.mcp.session](tool-mcp-session.md) | `src/uaw/tool/mcp/session.py` |
| 能力规范化 | [tool.mcp.capabilities](tool-mcp-capabilities.md) | `src/uaw/tool/mcp/capabilities.py` |
| 闸门后调用 | [tool.mcp.invoke](tool-mcp-invoke.md) | `src/uaw/tool/mcp/invoke.py` |
| 变化与撤销 | [tool.mcp.invalidate](tool-mcp-invalidate.md) | `src/uaw/tool/mcp/invalidate.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：MCP提供方路径 | [领域与外部适配器](tool-adapters.md) |
| 本节点 → 下游 | 数据/引用：能力及schema版本 | [工具注册与版本](tool-registry.md) |

## 参考与需要验证的选择

- [Tool · 调用/MCP/效果](https://app.notion.com/p/3e96ccd32c8780fab75dd0b4c21fe7fb)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · 审批/复核](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

