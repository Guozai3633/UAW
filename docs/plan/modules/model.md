# Model Runtime · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

用户模型政策、实际调用、协议能力、恢复和真实用量。

本分组主责2轮，另关联1轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P0 · 工程起步与基础边界

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P0-05 固定模型真实调用与协议恢复](../rounds/P0-05.md) | 完整执行用户选择的模型，不做静默模型替换。 | [P0-03](../rounds/P0-03.md)、[P0-04](../rounds/P0-04.md) | 本组主责；核心开发范围 / 开发中 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-04 多层结果缓存与在途合并](../rounds/P4-04.md) | 在不改变当前权限和结果语义的前提下减少重复工作。 | [P4-03](../rounds/P4-03.md) | 跨模块协同；核心开发范围 / 待开发 |
| [P4-08 明确Auto授权与能力恢复](../rounds/P4-08.md) | 固定模型仍不变，Auto只能在用户授权范围内选择。 | [P4-06](../rounds/P4-06.md)、[P3-08](../rounds/P3-08.md) | 本组主责；核心开发范围 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `model` | [模型调用 · Model](../../design/modules/model.md) | [逐接口定义](../../api/nodes/model.md) |
| `model.catalog` | [可见模型目录](../../design/components/model-catalog.md) | [逐接口定义](../../api/nodes/model.catalog.md) |
| `model.policy` | [选择与模型继承](../../design/components/model-policy.md) | [逐接口定义](../../api/nodes/model.policy.md) |
| `model.capability` | [兼容与Auto选择](../../design/components/model-capability.md) | [逐接口定义](../../api/nodes/model.capability.md) |
| `model.gateway` | [调用网关](../../design/components/model-gateway.md) | [逐接口定义](../../api/nodes/model.gateway.md) |
| `model.adapters` | [供应商协议适配](../../design/components/model-adapters.md) | [逐接口定义](../../api/nodes/model.adapters.md) |
| `model.recovery` | [调用恢复](../../design/components/model-recovery.md) | [逐接口定义](../../api/nodes/model.recovery.md) |
| `model.usage` | [计量与版本记录](../../design/components/model-usage.md) | [逐接口定义](../../api/nodes/model.usage.md) |
| `support.cache` | [共享缓存设施](../../design/components/support-cache.md) | [逐接口定义](../../api/nodes/support.cache.md) |
| `context.sources` | [来源解析](../../design/components/context-sources.md) | [逐接口定义](../../api/nodes/context.sources.md) |
| `context.retrieval` | [资料检索与证据](../../design/components/context-retrieval.md) | [逐接口定义](../../api/nodes/context.retrieval.md) |
| `agent.definitions.model_intent` | [模型意图解析](../../design/components/agent-definitions-model_intent.md) | [逐接口定义](../../api/nodes/agent.definitions.model_intent.md) |

## 目标代码/验证目录

- `src/uaw/model/facade.py`
- `src/uaw/model/catalog.py`
- `src/uaw/model/policy.py`
- `src/uaw/model/capability.py`
- `src/uaw/model/gateway.py`
- `src/uaw/model/adapters.py`
- `src/uaw/model/recovery.py`
- `src/uaw/model/usage.py`
- `tests/integration/model/`
- `src/uaw/shared/cache.py`
- `src/uaw/context/sources.py`
- `src/uaw/context/retrieval.py`
- `tests/integration/cache/`
- `tests/evaluation/cache/`
- `src/uaw/agent/definitions/model_intent.py`
- `tests/integration/model_policy/`
- `tests/evaluation/model_selection/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

