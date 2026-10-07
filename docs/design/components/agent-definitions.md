# 子Agent定义与发现：开发设计

节点 `agent.definitions` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

持久会话角色的设计、创建、发现与配置版本。

- 计划主文件：`src/uaw/agent/definitions/facade.py`。
- 统一业务入口：`define_agent/discover_agents`；只允许所属 facade 或获准适配器调用。
- 上层归属：`agent`。该节点是逻辑组件，不默认独立服务。
- 硬约束：创建角色不自动启动任务；定义修改可撤销。

## 输入、输出与调用协议

输入请求 `AgentDefinitionsRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
definitions: list[AgentDefinitionDraft]; batch_policy: atomic|independent; source_input_ref: Ref; expected_version: int?
```

领域输出：AgentDefinitionVersion / CandidateSummary。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 主Agent识别用户创建/修改意图，按需加载agent_definition短方法。
2. 通过agents.create/update提交职责、use_when、avoid_when、技能工具边界和模型意图。
3. Tool注入主体/会话与幂等键。
4. Agent Registry检查作用域、名称冲突、依赖与用户授权，Model解析inherit/explicit/auto。
5. 按整组或独立项策略提交不可变定义版本。
6. 定义成功后返回可发现摘要，实际执行另走agents.invoke。

### 模型参与方式

需要语义判断时，由当前继承模型提出建议；可复用当前主调用或按需发起，不强制专门判断 Agent。技术验证与状态提交仍由代码执行。

## 状态、并发与提交

唯一name约束绑定owner/conversation；每项client_definition_key保持重试幂等。更新CAS，停用/撤销产生新版本；工厂固定定义版本。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 模型不存在返回当前LLM且不启用。
- 同名返回conflict，不覆盖。
- 原子批量任何一项失败全组不提交。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

常驻只提供摘要，长指令/技能按需加载；配置创建不预留子执行预算。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 创建两个角色不启动两个任务。
- 重复请求不重复创建。
- 未显式指定的模型均inherit。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/agent.definitions.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 角色设计方法 | [agent.definitions.designer](agent-definitions-designer.md) | `src/uaw/agent/definitions/designer.py` |
| 定义与授权校验 | [agent.definitions.validator](agent-definitions-validator.md) | `src/uaw/agent/definitions/validator.py` |
| 模型意图解析 | [agent.definitions.model_intent](agent-definitions-model_intent.md) | `src/uaw/agent/definitions/model_intent.py` |
| 定义提交与版本 | [agent.definitions.repository](agent-definitions-repository.md) | `src/uaw/agent/definitions/repository.py` |
| 会话Agent发现 | [agent.definitions.discovery](agent-definitions-discovery.md) | `src/uaw/agent/definitions/discovery.py` |
| 配置变更与撤销 | [agent.definitions.change_service](agent-definitions-change_service.md) | `src/uaw/agent/definitions/change_service.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 本节点 → 下游 | 数据/引用：读取启用定义版本 | [统一实例工厂](agent-factory.md) |
| 本节点 → 下游 | 数据/引用：Context提供会话候选，非自动调用 | [Agent 决策循环](agent-loop.md) |

## 参考与需要验证的选择

- [Multi-Agent · 角色/路由/委派/上下文](https://app.notion.com/p/3ec6ccd32c8780d6b4f9d357a257bfd9)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Planning · 分解/依赖/修订](https://app.notion.com/p/3ec6ccd32c8780cb836cce28bd809d12)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Skills · 发现/加载/权限](https://app.notion.com/p/3ec6ccd32c87807bb032da89a48c45ae)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

