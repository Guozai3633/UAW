# Tool Runtime · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

注册与发现、调用闸门、真实结果、失败恢复与MCP。

本分组主责5轮，另关联1轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P1 · 单Agent完整闭环

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P1-03 工具目录与完整调用闸门](../rounds/P1-03.md) | 使模型提出的动作经过参数、权限、审批和真实结果处理。 | [P0-03](../rounds/P0-03.md)、[P0-04](../rounds/P0-04.md)、[P1-02](../rounds/P1-02.md) | 本组主责；核心开发范围 / 待开发 |

### P2 · 角色、子Agent与工作成果

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P2-02 联网搜索与网页读取](../rounds/P2-02.md) | 通过管理员提供方获取可核验外部资料。 | [P2-01](../rounds/P2-01.md)、[P0-03](../rounds/P0-03.md) | 本组主责；核心开发范围 / 待开发 |

### P3 · 语义规划与并行协作

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P3-03 独立工具并发与回压](../rounds/P3-03.md) | 只并发可证明独立的动作，并保持账本正确。 | [P3-02](../rounds/P3-02.md) | 本组主责；核心开发范围 / 待开发 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-03 角色过滤与向量混合发现](../rounds/P4-03.md) | 扩大工具目录而保留LLM最终选择。 | [P4-02](../rounds/P4-02.md)、[P2-04](../rounds/P2-04.md) | 本组主责；核心开发范围 / 待开发 |
| [P4-05 MCP与私人账号连接生命周期](../rounds/P4-05.md) | 可安装接入能力，但授权由真实账户和政策决定。 | [P4-04](../rounds/P4-04.md)、[P0-03](../rounds/P0-03.md) | 本组主责；核心开发范围 / 待开发 |

### P5 · 恢复、评测与受控试用

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P5-02 租约、当前权限与安全续跑](../rounds/P5-02.md) | 恢复未完工作而不重复未知外部写。 | [P5-01](../rounds/P5-01.md) | 跨模块协同；核心开发范围 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `tool` | [工具执行 · Tool](../../design/modules/tool.md) | [逐接口定义](../../api/nodes/tool.md) |
| `tool.registry` | [工具注册与版本](../../design/components/tool-registry.md) | [逐接口定义](../../api/nodes/tool.registry.md) |
| `tool.discovery` | [工具发现与筛选](../../design/components/tool-discovery.md) | [逐接口定义](../../api/nodes/tool.discovery.md) |
| `tool.invocation` | [调用闸门与派发](../../design/components/tool-invocation.md) | [逐接口定义](../../api/nodes/tool.invocation.md) |
| `tool.invocation.schema` | [参数与可信上下文](../../design/components/tool-invocation-schema.md) | [逐接口定义](../../api/nodes/tool.invocation.schema.md) |
| `tool.invocation.precheck` | [执行预检](../../design/components/tool-invocation-precheck.md) | [逐接口定义](../../api/nodes/tool.invocation.precheck.md) |
| `tool.invocation.approval` | [必要审批等待](../../design/components/tool-invocation-approval.md) | [逐接口定义](../../api/nodes/tool.invocation.approval.md) |
| `tool.invocation.recheck` | [执行前复核](../../design/components/tool-invocation-recheck.md) | [逐接口定义](../../api/nodes/tool.invocation.recheck.md) |
| `tool.invocation.dispatch` | [意图登记与执行](../../design/components/tool-invocation-dispatch.md) | [逐接口定义](../../api/nodes/tool.invocation.dispatch.md) |
| `tool.invocation.result` | [规范结果与结算](../../design/components/tool-invocation-result.md) | [逐接口定义](../../api/nodes/tool.invocation.result.md) |
| `tool.adapters` | [领域与外部适配器](../../design/components/tool-adapters.md) | [逐接口定义](../../api/nodes/tool.adapters.md) |
| `tool.results` | [结果规范化与分页](../../design/components/tool-results.md) | [逐接口定义](../../api/nodes/tool.results.md) |
| `tool.effects` | [调用与副作用账本](../../design/components/tool-effects.md) | [逐接口定义](../../api/nodes/tool.effects.md) |
| `tool.audit` | [执行审计与指标](../../design/components/tool-audit.md) | [逐接口定义](../../api/nodes/tool.audit.md) |
| `tool.failure` | [失败恢复与等价切换](../../design/components/tool-failure.md) | [逐接口定义](../../api/nodes/tool.failure.md) |
| `context.references` | [引用登记与解析](../../design/components/context-references.md) | [逐接口定义](../../api/nodes/context.references.md) |
| `run.budget` | [预算与准入](../../design/components/run-budget.md) | [逐接口定义](../../api/nodes/run.budget.md) |
| `agent.definitions.discovery` | [会话Agent发现](../../design/components/agent-definitions-discovery.md) | [逐接口定义](../../api/nodes/agent.definitions.discovery.md) |
| `context.retrieval` | [资料检索与证据](../../design/components/context-retrieval.md) | [逐接口定义](../../api/nodes/context.retrieval.md) |
| `tool.mcp` | [MCP 连接与适配](../../design/components/tool-mcp.md) | [逐接口定义](../../api/nodes/tool.mcp.md) |
| `tool.mcp.provider` | [提供方绑定](../../design/components/tool-mcp-provider.md) | [逐接口定义](../../api/nodes/tool.mcp.provider.md) |
| `tool.mcp.session` | [协议会话](../../design/components/tool-mcp-session.md) | [逐接口定义](../../api/nodes/tool.mcp.session.md) |
| `tool.mcp.capabilities` | [能力规范化](../../design/components/tool-mcp-capabilities.md) | [逐接口定义](../../api/nodes/tool.mcp.capabilities.md) |
| `tool.mcp.invoke` | [闸门后调用](../../design/components/tool-mcp-invoke.md) | [逐接口定义](../../api/nodes/tool.mcp.invoke.md) |
| `tool.mcp.invalidate` | [变化与撤销](../../design/components/tool-mcp-invalidate.md) | [逐接口定义](../../api/nodes/tool.mcp.invalidate.md) |
| `support.configuration` | [配置与账号控制层](../../design/components/support-configuration.md) | [逐接口定义](../../api/nodes/support.configuration.md) |
| `run.resume` | [租约与执行恢复](../../design/components/run-resume.md) | [逐接口定义](../../api/nodes/run.resume.md) |
| `run.resume.lease` | [取得运行租约](../../design/components/run-resume-lease.md) | [逐接口定义](../../api/nodes/run.resume.lease.md) |
| `run.resume.versions` | [版本兼容检查](../../design/components/run-resume-versions.md) | [逐接口定义](../../api/nodes/run.resume.versions.md) |
| `run.resume.access` | [重建连接与核验](../../design/components/run-resume-access.md) | [逐接口定义](../../api/nodes/run.resume.access.md) |
| `run.resume.effects` | [Tool未决动作对账](../../design/components/run-resume-effects.md) | [逐接口定义](../../api/nodes/run.resume.effects.md) |
| `run.resume.workspace` | [工作区实际版本](../../design/components/run-resume-workspace.md) | [逐接口定义](../../api/nodes/run.resume.workspace.md) |
| `run.resume.continue` | [恢复可运行工作](../../design/components/run-resume-continue.md) | [逐接口定义](../../api/nodes/run.resume.continue.md) |
| `run.cancel` | [取消传播](../../design/components/run-cancel.md) | [逐接口定义](../../api/nodes/run.cancel.md) |

## 目标代码/验证目录

- `src/uaw/tool/facade.py`
- `src/uaw/tool/registry.py`
- `src/uaw/tool/discovery.py`
- `src/uaw/tool/invocation/facade.py`
- `src/uaw/tool/invocation/schema.py`
- `src/uaw/tool/invocation/precheck.py`
- `src/uaw/tool/invocation/approval.py`
- `src/uaw/tool/invocation/recheck.py`
- `src/uaw/tool/invocation/dispatch.py`
- `src/uaw/tool/invocation/result.py`
- `src/uaw/tool/adapters.py`
- `src/uaw/tool/results.py`
- `src/uaw/tool/effects.py`
- `src/uaw/tool/audit.py`
- `src/uaw/tool/failure.py`
- `src/uaw/tool/control/`
- `tests/integration/tool/`
- `src/uaw/context/references.py`
- `tests/integration/web_sources/`
- `src/uaw/run/budget.py`
- `tests/integration/tool_parallel/`
- `src/uaw/agent/definitions/discovery.py`
- `src/uaw/context/retrieval.py`
- `tests/evaluation/tool_discovery/`
- `src/uaw/tool/mcp/facade.py`
- `src/uaw/tool/mcp/provider.py`
- `src/uaw/tool/mcp/session.py`
- `src/uaw/tool/mcp/capabilities.py`
- `src/uaw/tool/mcp/invoke.py`
- `src/uaw/tool/mcp/invalidate.py`
- `src/uaw/shared/configuration.py`
- `tests/integration/mcp/`
- `apps/web/src/features/workspace/`
- `src/uaw/run/resume/facade.py`
- `src/uaw/run/resume/lease.py`
- `src/uaw/run/resume/versions.py`
- `src/uaw/run/resume/access.py`
- `src/uaw/run/resume/effects.py`
- `src/uaw/run/resume/workspace.py`
- `src/uaw/run/resume/continue_run.py`
- `src/uaw/run/cancel.py`
- `tests/integration/recovery/`
- `apps/local_runner/uaw_runner/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

