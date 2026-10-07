# Context Runtime · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

规则、资料、引用、预算装配、记忆和压缩。

本分组主责4轮，另关联5轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P1 · 单Agent完整闭环

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P1-02 最小上下文、规则和引用](../rounds/P1-02.md) | 为当前调用提供必要且有来源的输入。 | [P0-02](../rounds/P0-02.md)、[P0-05](../rounds/P0-05.md)、[P1-01](../rounds/P1-01.md) | 本组主责；核心开发范围 / 开发中 |

### P2 · 角色、子Agent与工作成果

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P2-01 文件上传、摄取与索引发布](../rounds/P2-01.md) | 把用户办公材料和论文变成可定位、可删除的资料。 | [P1-11](../rounds/P1-11.md) | 本组主责；核心开发范围 / 待开发 |
| [P2-02 联网搜索与网页读取](../rounds/P2-02.md) | 通过管理员提供方获取可核验外部资料。 | [P2-01](../rounds/P2-01.md)、[P0-03](../rounds/P0-03.md) | 跨模块协同；核心开发范围 / 待开发 |
| [P2-03 技能加载与可复用任务模板](../rounds/P2-03.md) | 让操作方法按需复用而不靠长主提示词。 | [P2-01](../rounds/P2-01.md) | 跨模块协同；核心开发范围 / 待开发 |
| [P2-07 办公与学术方法和成果验收](../rounds/P2-07.md) | 在通用架构上实现两个可复用工作场景。 | [P2-02](../rounds/P2-02.md)、[P2-03](../rounds/P2-03.md)、[P2-06](../rounds/P2-06.md) | 跨模块协同；核心开发范围 / 待开发 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-01 记忆读写、冲突与遗忘](../rounds/P4-01.md) | 用户可控制任务是否读取或贡献记忆。 | [P3-08](../rounds/P3-08.md) | 本组主责；核心开发范围 / 待开发 |
| [P4-02 语义压缩、裁剪与稳定前缀](../rounds/P4-02.md) | 在长任务中保留关键要求和真实执行状态。 | [P4-01](../rounds/P4-01.md) | 本组主责；核心开发范围 / 待开发 |
| [P4-03 角色过滤与向量混合发现](../rounds/P4-03.md) | 扩大工具目录而保留LLM最终选择。 | [P4-02](../rounds/P4-02.md)、[P2-04](../rounds/P2-04.md) | 跨模块协同；核心开发范围 / 待开发 |
| [P4-04 多层结果缓存与在途合并](../rounds/P4-04.md) | 在不改变当前权限和结果语义的前提下减少重复工作。 | [P4-03](../rounds/P4-03.md) | 跨模块协同；核心开发范围 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `context` | [上下文 · Context](../../design/modules/context.md) | [逐接口定义](../../api/nodes/context.md) |
| `context.sources` | [来源解析](../../design/components/context-sources.md) | [逐接口定义](../../api/nodes/context.sources.md) |
| `context.rules` | [规则与信任装配](../../design/components/context-rules.md) | [逐接口定义](../../api/nodes/context.rules.md) |
| `context.selection` | [选择与上下文预算](../../design/components/context-selection.md) | [逐接口定义](../../api/nodes/context.selection.md) |
| `context.composer` | [装配与快照](../../design/components/context-composer.md) | [逐接口定义](../../api/nodes/context.composer.md) |
| `context.references` | [引用登记与解析](../../design/components/context-references.md) | [逐接口定义](../../api/nodes/context.references.md) |
| `context.ingestion` | [摄取与索引发布](../../design/components/context-ingestion.md) | [逐接口定义](../../api/nodes/context.ingestion.md) |
| `context.retrieval` | [资料检索与证据](../../design/components/context-retrieval.md) | [逐接口定义](../../api/nodes/context.retrieval.md) |
| `tool.adapters` | [领域与外部适配器](../../design/components/tool-adapters.md) | [逐接口定义](../../api/nodes/tool.adapters.md) |
| `tool.results` | [结果规范化与分页](../../design/components/tool-results.md) | [逐接口定义](../../api/nodes/tool.results.md) |
| `agent.skills` | [技能与任务模板](../../design/components/agent-skills.md) | [逐接口定义](../../api/nodes/agent.skills.md) |
| `agent.completion.semantic` | [语义核对](../../design/components/agent-completion-semantic.md) | [逐接口定义](../../api/nodes/agent.completion.semantic.md) |
| `context.memory` | [记忆生命周期](../../design/components/context-memory.md) | [逐接口定义](../../api/nodes/context.memory.md) |
| `context.memory.candidate` | [记忆候选](../../design/components/context-memory-candidate.md) | [逐接口定义](../../api/nodes/context.memory.candidate.md) |
| `context.memory.policy` | [范围与写入政策](../../design/components/context-memory-policy.md) | [逐接口定义](../../api/nodes/context.memory.policy.md) |
| `context.memory.conflict` | [查重与冲突](../../design/components/context-memory-conflict.md) | [逐接口定义](../../api/nodes/context.memory.conflict.md) |
| `context.memory.store` | [提交与召回](../../design/components/context-memory-store.md) | [逐接口定义](../../api/nodes/context.memory.store.md) |
| `context.memory.forget` | [遗忘与删除传播](../../design/components/context-memory-forget.md) | [逐接口定义](../../api/nodes/context.memory.forget.md) |
| `context.compression` | [压缩与关键项保护](../../design/components/context-compression.md) | [逐接口定义](../../api/nodes/context.compression.md) |
| `tool.registry` | [工具注册与版本](../../design/components/tool-registry.md) | [逐接口定义](../../api/nodes/tool.registry.md) |
| `tool.discovery` | [工具发现与筛选](../../design/components/tool-discovery.md) | [逐接口定义](../../api/nodes/tool.discovery.md) |
| `agent.definitions.discovery` | [会话Agent发现](../../design/components/agent-definitions-discovery.md) | [逐接口定义](../../api/nodes/agent.definitions.discovery.md) |
| `support.cache` | [共享缓存设施](../../design/components/support-cache.md) | [逐接口定义](../../api/nodes/support.cache.md) |
| `model.usage` | [计量与版本记录](../../design/components/model-usage.md) | [逐接口定义](../../api/nodes/model.usage.md) |

## 目标代码/验证目录

- `src/uaw/context/facade.py`
- `src/uaw/context/sources.py`
- `src/uaw/context/rules.py`
- `src/uaw/context/selection.py`
- `src/uaw/context/composer.py`
- `src/uaw/context/references.py`
- `tests/integration/context/`
- `src/uaw/context/ingestion.py`
- `src/uaw/context/retrieval.py`
- `src/uaw/context/`
- `tests/fixtures/materials/`
- `src/uaw/tool/adapters.py`
- `src/uaw/tool/results.py`
- `tests/integration/web_sources/`
- `src/uaw/agent/skills.py`
- `capabilities/builtin/`
- `tests/integration/skills/`
- `src/uaw/agent/completion/semantic.py`
- `capabilities/builtin/office_report/`
- `capabilities/builtin/academic_discussion/`
- `tests/fixtures/scenarios/`
- `src/uaw/context/memory/facade.py`
- `src/uaw/context/memory/candidate.py`
- `src/uaw/context/memory/policy.py`
- `src/uaw/context/memory/conflict.py`
- `src/uaw/context/memory/store.py`
- `src/uaw/context/memory/forget.py`
- `apps/web/src/features/workspace/`
- `tests/integration/memory/`
- `src/uaw/context/compression.py`
- `tests/fixtures/long_context/`
- `tests/integration/compression/`
- `src/uaw/tool/registry.py`
- `src/uaw/tool/discovery.py`
- `src/uaw/agent/definitions/discovery.py`
- `tests/evaluation/tool_discovery/`
- `src/uaw/shared/cache.py`
- `src/uaw/model/usage.py`
- `tests/integration/cache/`
- `tests/evaluation/cache/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

