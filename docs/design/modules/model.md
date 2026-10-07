# 模型调用 · Model：模块开发设计

节点 `model` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。

[开发设计索引](../README.md) · [目录设计](../../PROJECT_STRUCTURE.md) · [公共契约](../COMMON_CONTRACTS.md)

## 统一入口与状态所有权

计划包：`src/uaw/model/`，入口：`src/uaw/model/facade.py`。

入口契约：`ModelRuntime.resolve_policy(PolicyRequest)、list(CatalogRequest)、generate(ModelCall)`。

所有权：ResolvedModelPolicy、模型调用attempt/实际配置/usage；配置目录来源归控制层。

## 内部组织策略

先继承用户模型意图，再核对目录/能力，只有Auto授权才选择候选。Gateway预留预算并调用provider adapter，输出校验与usage结算覆盖失败attempt，Recovery遵守固定/Auto政策。

facade接收可信请求并协调子组件；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。

## 数据与依赖接口

输入：固定/Auto政策、prompt、能力需求。输出：模型动作输出、实际版本、用量。

注入ports：`ConfigurationReader、CredentialReader、RunBudgetPort、ProviderAdapters、CallRepository、TraceSink`。

领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。

## 决策、权限与资源策略

该模块执行模型调用，不要求额外模型来选模型。Auto策略可按受评测规则选择或请求语义建议，但不能覆盖固定模型。

用户指定模型优先；不可用不能静默换模型。

每次提交绑定真实版本、当前scope、剩余deadline和预算。固定常规配置与当前撤销分开检查。多模块提交用本地事务或可恢复意图，不能承诺外部动作exactly-once。

## 失败与恢复策略

facade保留失败发生阶段与原始受控引用。参数/依赖/版本冲突回调用者修复；拒绝不通过换工具绕过；副作用unknown先Tool对账。恢复先检查此领域schema/版本兼容，再恢复可继续边界，不用Trace重建权威状态。

## 文件组织规则

- `facade.py`：统一入口、依赖注入、调用编排。
- `contracts.py`：领域请求/结果/版本化对象。
- `ports.py`：存储、跨Runtime与执行器协议。
- 子组件文件/包：实现具体策略，分层节点有自己的facade/contracts/ports。
- `repository.py`：领域存储适配，实现CAS和幂等；业务规则仍在组件。
- `tests/unit/` 与 `tests/integration/`：实现阶段只验证具体风险/门槛，不复制实现。

## 实施与验收门槛

模型继承树、明确子模型缺失反馈、协议不支持、流式重试、usage去重与固定模型不暗换。

首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/model.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 可见模型目录 | [model.catalog](../components/model-catalog.md) | `src/uaw/model/catalog.py` |
| 选择与模型继承 | [model.policy](../components/model-policy.md) | `src/uaw/model/policy.py` |
| 兼容与Auto选择 | [model.capability](../components/model-capability.md) | `src/uaw/model/capability.py` |
| 调用网关 | [model.gateway](../components/model-gateway.md) | `src/uaw/model/gateway.py` |
| 供应商协议适配 | [model.adapters](../components/model-adapters.md) | `src/uaw/model/adapters.py` |
| 调用恢复 | [model.recovery](../components/model-recovery.md) | `src/uaw/model/recovery.py` |
| 计量与版本记录 | [model.usage](../components/model-usage.md) | `src/uaw/model/usage.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：需要语义理解生成时 | [任务理解 · Intent](intent.md) |
| 上游 → 本节点 | 调用：需要语义压缩/摘要时 | [上下文 · Context](context.md) |
| 上游 → 本节点 | 调用：提出下一步动作 | [决策执行 · Agent](agent.md) |
| 本节点 → 下游 | 状态/事件：模型预算预留与结算 | [运行控制 · Run](run.md) |
| 上游 → 本节点 | 权限/配置：模型目录与发布配置 | [共享支撑与控制层](support.md) |

## 参考与需要验证的选择

- [Model Strategy · 继承/能力/adapter/usage](https://app.notion.com/p/3ec6ccd32c87807bb032da89a48c45ae)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

