# 共享支撑与控制层：模块开发设计

节点 `support` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。

[开发设计索引](../README.md) · [目录设计](../../PROJECT_STRUCTURE.md) · [公共契约](../COMMON_CONTRACTS.md)

## 统一入口与状态所有权

计划包：`src/uaw/shared/`，入口：`src/uaw/shared/__init__.py`。

入口契约：`Configuration.publish、Extension.activate、Cache.get_or_compute、Observability.observe、Evaluation.evaluate`。

所有权：共享缓存派生项、平台配置/账号凭据、扩展包ReleaseManifest、诊断Trace与离线评测集/报告。

## 内部组织策略

提供独立支撑接口，领域通过ports消费；常规版本固定与当前撤销分开。缓存负责机械复用，语义有效性归领域；观测记录实际版本/attempt，评测固定初态/权限/fixtures对比发布候选。

各支撑设施通过独立公共入口接收可信请求；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。

## 数据与依赖接口

输入：版本配置、派生数据、诊断/评测请求。输出：有效配置、缓存、运行诊断、对比报告。

注入ports：`各领域的失效/诊断接口、CredentialStore、RepositoryAdapters、隔离评测执行器、人工作业入口`。

领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。

## 决策、权限与资源策略

共享设施不逐请求固定调用LLM；语义评分按评测配置调用且人工校准，不授予工具执行权限。

不成为第八个强制执行 Runtime；业务状态仍归领域。

每次提交绑定真实版本、当前scope、剩余deadline和预算。固定常规配置与当前撤销分开检查。多模块提交用本地事务或可恢复意图，不能承诺外部动作exactly-once。

## 失败与恢复策略

各设施入口保留失败发生阶段与原始受控引用。参数/依赖/版本冲突回调用者修复；拒绝不通过换工具绕过；副作用unknown先Tool对账。恢复先检查此领域schema/版本兼容，再恢复可继续边界，不用Trace重建权威状态。

## 文件组织规则

- `__init__.py`：导出各独立设施入口；不实现万能facade或固定支撑流水线。
- `contracts.py`：领域请求/结果/版本化对象。
- `ports.py`：存储、跨Runtime与执行器协议。
- 子组件文件/包：实现具体策略，分层节点有自己的facade/contracts/ports。
- `repository.py`：领域存储适配，实现CAS和幂等；业务规则仍在组件。
- `tests/unit/` 与 `tests/integration/`：实现阶段只验证具体风险/门槛，不复制实现。

## 实施与验收门槛

无凭据泄漏、缓存失效、诊断不替权威日志、发布不可变版本与真实写评测禁重放。

首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/support.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 配置与账号控制层 | [support.configuration](../components/support-configuration.md) | `src/uaw/shared/configuration.py` |
| 扩展包与版本发布 | [support.extensions](../components/support-extensions.md) | `src/uaw/shared/extensions.py` |
| 共享缓存设施 | [support.cache](../components/support-cache.md) | `src/uaw/shared/cache.py` |
| 运行观测 | [support.observability](../components/support-observability.md) | `src/uaw/shared/observability.py` |
| 离线质量评测 | [support.evaluation](../components/support-evaluation.md) | `src/uaw/shared/evaluation.py` |
| 存储适配与访问 | [support.stores](../components/support-stores.md) | `src/uaw/shared/stores.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 本节点 → 下游 | 权限/配置：提供方与当前撤销 | [工具执行 · Tool](tool.md) |
| 本节点 → 下游 | 权限/配置：模型目录与发布配置 | [模型调用 · Model](model.md) |
| 本节点 → 下游 | 权限/配置：技能/能力包与flag | [决策执行 · Agent](agent.md) |
| 本节点 → 下游 | 权限/配置：资料/记忆与保留政策 | [上下文 · Context](context.md) |
| 上游 → 本节点 | 数据/引用：关联诊断与评测输入 | [运行控制 · Run](run.md) |

## 参考与需要验证的选择

- [Cache · 在途合并/失效](https://app.notion.com/p/3ec6ccd32c87809fbf70ea46b440a3e3)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Evaluation · 样本/版本/Trace](https://app.notion.com/p/3ec6ccd32c87805596bad437d733ecf9)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

