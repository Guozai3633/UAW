# 调用闸门与派发：开发设计

节点 `tool.invocation` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

统一参数、授权、审批复核、预算与适配器调用。

- 计划主文件：`src/uaw/tool/invocation/facade.py`。
- 统一业务入口：`invoke`；只允许所属 facade 或获准适配器调用。
- 上层归属：`tool`。该节点是逻辑组件，不默认独立服务。
- 硬约束：模型不能写入 approved/principal 等可信字段。

## 输入、输出与调用协议

输入请求 `ToolInvocationRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
tool_ref: Ref; arguments: Object; action_id: ID; trusted_context: ToolRuntimeContext
```

领域输出：标准 ToolResult。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. schema规范化与资源引用校验。
2. 当前权限/flag/预算/deadline预检。
3. 必要审批绑定参数hash和资源版本，由Run持久等待。
4. 批准后复核身份、撤销、参数与资源。
5. 持久调用意图再派发。
6. 结果规范化、账本对账与用量结算后反馈Agent。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

Tool拥有调用账本与效果记录；ApprovalRef指向Run权威决定，模型不能自填approved。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 参数错误可修复但不执行。
- 拒绝返回declined不能换工具绕过。
- timeout保持可能unknown。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

闸门与参数校验必经，发现可跳过；只读缓存命中仍生成当次调用Item。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 审批等待时不提前发请求。
- 参数修改旧批准失效。
- ToolResult能区分业务失败与基础设施失败。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/tool.invocation.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 参数与可信上下文 | [tool.invocation.schema](tool-invocation-schema.md) | `src/uaw/tool/invocation/schema.py` |
| 执行预检 | [tool.invocation.precheck](tool-invocation-precheck.md) | `src/uaw/tool/invocation/precheck.py` |
| 必要审批等待 | [tool.invocation.approval](tool-invocation-approval.md) | `src/uaw/tool/invocation/approval.py` |
| 执行前复核 | [tool.invocation.recheck](tool-invocation-recheck.md) | `src/uaw/tool/invocation/recheck.py` |
| 意图登记与执行 | [tool.invocation.dispatch](tool-invocation-dispatch.md) | `src/uaw/tool/invocation/dispatch.py` |
| 规范结果与结算 | [tool.invocation.result](tool-invocation-result.md) | `src/uaw/tool/invocation/result.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：LLM选择后调用 | [工具发现与筛选](tool-discovery.md) |
| 本节点 → 下游 | 状态/事件：执行前登记意图 | [调用与副作用账本](tool-effects.md) |
| 上游 → 本节点 | 调用：允许重试/等价切换 | [失败恢复与等价切换](tool-failure.md) |

## 参考与需要验证的选择

- [Tool · 调用/MCP/效果](https://app.notion.com/p/3e96ccd32c8780fab75dd0b4c21fe7fb)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · 审批/复核](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

