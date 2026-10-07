# 配置与共享设施 · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

配置、仓储、凭据边界、缓存、观测、评测及能力包。

本分组主责5轮，另关联4轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P0 · 工程起步与基础边界

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P0-01 工程启动与最小契约](../rounds/P0-01.md) | 建立能启动的Python应用和依赖组装，避免先实现全部未来DTO。 | 无 | 跨模块协同；核心开发范围 / 已验收 |
| [P0-02 持久化、CAS、blob与事件提交边界](../rounds/P0-02.md) | 让受理/版本冲突和大内容存取有唯一权威。 | [P0-01](../rounds/P0-01.md) | 本组主责；核心开发范围 / 开发中 |
| [P0-03 最小管理配置、凭据与功能旗标](../rounds/P0-03.md) | 从控制层向Runtime提供固定配置和当前撤销状态。 | [P0-02](../rounds/P0-02.md) | 本组主责；核心开发范围 / 已验收 |
| [P0-04 受理、原文、状态、事件与资源账本](../rounds/P0-04.md) | 保存原文并以真实状态和用量驱动后续执行。 | [P0-02](../rounds/P0-02.md)、[P0-03](../rounds/P0-03.md) | 跨模块协同；核心开发范围 / 已验收 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-04 多层结果缓存与在途合并](../rounds/P4-04.md) | 在不改变当前权限和结果语义的前提下减少重复工作。 | [P4-03](../rounds/P4-03.md) | 本组主责；核心开发范围 / 待开发 |
| [P4-05 MCP与私人账号连接生命周期](../rounds/P4-05.md) | 可安装接入能力，但授权由真实账户和政策决定。 | [P4-04](../rounds/P4-04.md)、[P0-03](../rounds/P0-03.md) | 跨模块协同；核心开发范围 / 待开发 |
| [P4-06 完整配置与能力包版本发布](../rounds/P4-06.md) | 管理员可验证、发布、停用和恢复配置或插件。 | [P4-05](../rounds/P4-05.md) | 本组主责；核心开发范围 / 待开发 |

### P5 · 恢复、评测与受控试用

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P5-03 完整观测、版本评测与发布候选](../rounds/P5-03.md) | 用真实结果和成本决定版本是否可试用。 | [P5-02](../rounds/P5-02.md)、[P3-08](../rounds/P3-08.md) | 本组主责；核心开发范围 / 待开发 |
| [P5-05 单用户工作区受控试用准备](../rounds/P5-05.md) | 把可用能力交给真实用户，保留账号和设备边界。 | [P5-03](../rounds/P5-03.md)、[P4-09](../rounds/P4-09.md) | 跨模块协同；核心开发范围 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `support` | [共享支撑与控制层](../../design/modules/support.md) | [逐接口定义](../../api/nodes/support.md) |
| `support.stores` | [存储适配与访问](../../design/components/support-stores.md) | [逐接口定义](../../api/nodes/support.stores.md) |
| `support.configuration` | [配置与账号控制层](../../design/components/support-configuration.md) | [逐接口定义](../../api/nodes/support.configuration.md) |
| `run` | [运行控制 · Run](../../design/modules/run.md) | [逐接口定义](../../api/nodes/run.md) |
| `run.history` | [历史与输入权威](../../design/components/run-history.md) | [逐接口定义](../../api/nodes/run.history.md) |
| `run.state` | [Run 与交互项](../../design/components/run-state.md) | [逐接口定义](../../api/nodes/run.state.md) |
| `run.events` | [事件与重连](../../design/components/run-events.md) | [逐接口定义](../../api/nodes/run.events.md) |
| `run.budget` | [预算与准入](../../design/components/run-budget.md) | [逐接口定义](../../api/nodes/run.budget.md) |
| `support.observability` | [运行观测](../../design/components/support-observability.md) | [逐接口定义](../../api/nodes/support.observability.md) |
| `support.cache` | [共享缓存设施](../../design/components/support-cache.md) | [逐接口定义](../../api/nodes/support.cache.md) |
| `context.sources` | [来源解析](../../design/components/context-sources.md) | [逐接口定义](../../api/nodes/context.sources.md) |
| `context.retrieval` | [资料检索与证据](../../design/components/context-retrieval.md) | [逐接口定义](../../api/nodes/context.retrieval.md) |
| `model.usage` | [计量与版本记录](../../design/components/model-usage.md) | [逐接口定义](../../api/nodes/model.usage.md) |
| `tool.mcp` | [MCP 连接与适配](../../design/components/tool-mcp.md) | [逐接口定义](../../api/nodes/tool.mcp.md) |
| `tool.mcp.provider` | [提供方绑定](../../design/components/tool-mcp-provider.md) | [逐接口定义](../../api/nodes/tool.mcp.provider.md) |
| `tool.mcp.session` | [协议会话](../../design/components/tool-mcp-session.md) | [逐接口定义](../../api/nodes/tool.mcp.session.md) |
| `tool.mcp.capabilities` | [能力规范化](../../design/components/tool-mcp-capabilities.md) | [逐接口定义](../../api/nodes/tool.mcp.capabilities.md) |
| `tool.mcp.invoke` | [闸门后调用](../../design/components/tool-mcp-invoke.md) | [逐接口定义](../../api/nodes/tool.mcp.invoke.md) |
| `tool.mcp.invalidate` | [变化与撤销](../../design/components/tool-mcp-invalidate.md) | [逐接口定义](../../api/nodes/tool.mcp.invalidate.md) |
| `tool.failure` | [失败恢复与等价切换](../../design/components/tool-failure.md) | [逐接口定义](../../api/nodes/tool.failure.md) |
| `support.extensions` | [扩展包与版本发布](../../design/components/support-extensions.md) | [逐接口定义](../../api/nodes/support.extensions.md) |
| `support.evaluation` | [离线质量评测](../../design/components/support-evaluation.md) | [逐接口定义](../../api/nodes/support.evaluation.md) |
| `ingress` | [产品入口](../../design/components/ingress.md) | [逐接口定义](../../api/nodes/ingress.md) |
| `ui` | [交互页面](../../design/components/ui.md) | [逐接口定义](../../api/nodes/ui.md) |
| `workspace.binding` | [项目绑定与本地授权](../../design/components/workspace-binding.md) | [逐接口定义](../../api/nodes/workspace.binding.md) |

## 目标代码/验证目录

- `src/uaw/shared/__init__.py`
- `src/uaw/`
- `src/uaw/shared/`
- `tests/fixtures/`
- `docs/decisions/`
- `ops/`
- `src/uaw/shared/stores.py`
- `tests/integration/persistence/`
- `src/uaw/shared/configuration.py`
- `src/uaw/api/`
- `tests/integration/configuration/`
- `src/uaw/run/facade.py`
- `src/uaw/run/history.py`
- `src/uaw/run/state.py`
- `src/uaw/run/events.py`
- `src/uaw/run/budget.py`
- `src/uaw/shared/observability.py`
- `tests/integration/run/`
- `src/uaw/shared/cache.py`
- `src/uaw/context/sources.py`
- `src/uaw/context/retrieval.py`
- `src/uaw/model/usage.py`
- `tests/integration/cache/`
- `tests/evaluation/cache/`
- `src/uaw/tool/mcp/facade.py`
- `src/uaw/tool/mcp/provider.py`
- `src/uaw/tool/mcp/session.py`
- `src/uaw/tool/mcp/capabilities.py`
- `src/uaw/tool/mcp/invoke.py`
- `src/uaw/tool/mcp/invalidate.py`
- `src/uaw/tool/failure.py`
- `tests/integration/mcp/`
- `apps/web/src/features/workspace/`
- `src/uaw/shared/extensions.py`
- `capabilities/`
- `tests/integration/extensions/`
- `src/uaw/shared/evaluation.py`
- `tests/evaluation/`
- `docs/implementation/`
- `src/uaw/api/ingress.py`
- `src/uaw/workspace/binding.py`
- `apps/web/`
- `apps/local_runner/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

