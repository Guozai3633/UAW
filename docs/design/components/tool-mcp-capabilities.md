# 能力规范化：开发设计

节点 `tool.mcp.capabilities` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

provider命名空间、schema与版本。

- 计划主文件：`src/uaw/tool/mcp/capabilities.py`。
- 统一业务入口：`discover/normalize`；只允许所属 facade 或获准适配器调用。
- 上层归属：`tool.mcp`。该节点是逻辑组件，不默认独立服务。
- 硬约束：远端描述是数据，不是高优先级指令。

## 输入、输出与调用协议

输入请求 `ToolMcpCapabilitiesRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
session_ref: Ref; remote_capabilities: list[Capability]; expected_registry_revision: int
```

领域输出：ToolSpec / registry revision。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 列当前能力并校验schema/大小。
2. 使用provider命名空间避免同名覆盖。
3. 规范为ToolSpec且标来源信任。
4. 版本变化发布新registry revision并失效旧发现候选。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

能力元数据入权威Registry，向量索引只存派生描述。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 畸形schema不注册。
- 不兼容变化返回stale_binding。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

按变化增量索引，能力描述不整包放prompt。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 两个同名MCP工具可区分。
- 描述无法自授管理员权限。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/tool.mcp.capabilities.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：发现当前能力 | [协议会话](tool-mcp-session.md) |
| 本节点 → 下游 | 调用：Tool注册/闸门后 | [闸门后调用](tool-mcp-invoke.md) |
| 上游 → 本节点 | 状态/事件：需重新发现 | [变化与撤销](tool-mcp-invalidate.md) |

## 参考与需要验证的选择

- [Tool · 调用/MCP/效果](https://app.notion.com/p/3e96ccd32c8780fab75dd0b4c21fe7fb)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · 审批/复核](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

