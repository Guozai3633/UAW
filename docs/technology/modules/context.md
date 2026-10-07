# Context：资料、上下文与记忆 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | `sqlalchemy` | 领域Repository与事务适配 | 2.x异步API / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |
| [pgvector](https://github.com/pgvector/pgvector) | `PostgreSQL扩展＋pgvector Python适配` | 工具/资料/记忆向量索引 | 0.8或更高稳定线；冻结匹配PG版本 / P4 |
| [pg_trgm/全文检索](https://www.postgresql.org/docs/17/pgtrgm.html) | `PostgreSQL扩展/内置功能` | 关键词、名称与模糊召回 | 与PostgreSQL主版本一致 / P2/P4 |
| [pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) | `pypdf` | 文本型PDF摄取与页定位 | 稳定版 / P2，格式范围待D05 |
| [python-docx](https://python-docx.readthedocs.io/en/latest/) | `python-docx` | DOCX内容/报告适配 | 稳定版 / 按格式需求启用 |
| [openpyxl](https://openpyxl.readthedocs.io/en/stable/) | `openpyxl` | XLSX读写与公式保留 | 稳定版 / 按格式需求启用 |
| FSBlobStore | `UAW自有Python适配器` | 私有数据卷中的不可变大内容 | BlobStorePort v0.1 / P0 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 摄取与引用

Reader port读取获准历史、Board、Workspace及外部资料；本地内容来自Runner。先校验真实格式/大小/范围，再在受限parser进程解析；产出内容Hash、提取器版本、片段位置和原始Ref。

首批建议TXT/Markdown和文本型PDF，最终格式范围依D05。pypdf保留页及提取文本偏移；版面行号和扫描件OCR能力另报告，不用猜测补全文本。python-docx/openpyxl为DOCX/XLSX适配主选，按实际格式启用。openpyxl不负责公式计算；需要重算时另接获准执行环境并留下真实检查回执。

对象、片段、Reference和索引版本在PostgreSQL；大内容入BlobStore。文件摄取事务提交成功后才发布可检索修订，故障留下可清理的未引用blob。

### 召回与上下文装配

小资料集先精确/关键词召回，P4用pgvector结合关键词结果做RRF融合。embedding由批准profile配置，记录模型/维度/归一化/内容版本，不同profile不混算距离。embedding服务是检索能力，不成为额外回答/审批Agent；语义判断仍继承用户LLM。

英语正文可用PostgreSQL FTS；中文工具描述/短文本用规范化名称、精确/子串、字符n-gram召回适配，再融合向量。默认英语分词不能宣称覆盖中文；短词检索做有界候选查询。扩大资料规模前按中文/英文样例评测。

Composer保留来源/优先级、硬约束、真实执行状态和输出空间；工具schema只来自当前可用目录。TokenCounter通过提供方adapter估算或查询，不能用一个tokenizer精确代表所有模型。

### 记忆与压缩

MemoryCandidate经当前模型提议，policy/conflict/version由Python与SQL落实；读、贡献、删除分别控制。删除立刻阻断后续取用并失效派生缓存/摘要，物理清理按回执处理。

语义压缩通过ModelGateway，依赖Manifest记录来源版本；自有核验保留数字/路径/要求/未决动作。LangChain/LangGraph自动memory或自动摘要不独立接管Context。模型输入由此唯一装配后交Model。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `context` | Python、Pydantic、SQLAlchemy、PostgreSQL | 获准Reader/指令优先级/TokenCounter/Manifest，自有上下文入口 | [设计](../../design/modules/context.md) / [接口](../../api/nodes/context.md) |
| `context.sources` | Python、Pydantic、SQLAlchemy、PostgreSQL | 获准Reader/指令优先级/TokenCounter/Manifest，自有上下文入口 | [设计](../../design/components/context-sources.md) / [接口](../../api/nodes/context.sources.md) |
| `context.rules` | Python、Pydantic、SQLAlchemy、PostgreSQL | 获准Reader/指令优先级/TokenCounter/Manifest，自有上下文入口 | [设计](../../design/components/context-rules.md) / [接口](../../api/nodes/context.rules.md) |
| `context.ingestion` | Python、pypdf、python-docx、openpyxl、FSBlobStore、PostgreSQL | 受限解析器输出版本与位置；格式按D05启用 | [设计](../../design/components/context-ingestion.md) / [接口](../../api/nodes/context.ingestion.md) |
| `context.retrieval` | Python、PostgreSQL、pgvector、pg_trgm/全文检索 | 访问范围内关键词＋向量RRF召回，embedding版本分区 | [设计](../../design/components/context-retrieval.md) / [接口](../../api/nodes/context.retrieval.md) |
| `context.memory` | Python、Pydantic、SQLAlchemy、PostgreSQL、pgvector | 记忆读写/版本/冲突/删除，索引及缓存依赖失效 | [设计](../../design/components/context-memory.md) / [接口](../../api/nodes/context.memory.md) |
| `context.selection` | Python、Pydantic、SQLAlchemy、PostgreSQL | 获准Reader/指令优先级/TokenCounter/Manifest，自有上下文入口 | [设计](../../design/components/context-selection.md) / [接口](../../api/nodes/context.selection.md) |
| `context.compression` | Python、Pydantic、JSON Schema校验器 | 经ModelGateway提案，保护关键约束/来源/未决动作 | [设计](../../design/components/context-compression.md) / [接口](../../api/nodes/context.compression.md) |
| `context.composer` | Python、Pydantic、SQLAlchemy、PostgreSQL | 获准Reader/指令优先级/TokenCounter/Manifest，自有上下文入口 | [设计](../../design/components/context-composer.md) / [接口](../../api/nodes/context.composer.md) |
| `context.references` | Python、Pydantic、SQLAlchemy、PostgreSQL | 获准Reader/指令优先级/TokenCounter/Manifest，自有上下文入口 | [设计](../../design/components/context-references.md) / [接口](../../api/nodes/context.references.md) |
| `context.memory.candidate` | Python、Pydantic、JSON Schema校验器 | 经ModelGateway提案，保护关键约束/来源/未决动作 | [设计](../../design/components/context-memory-candidate.md) / [接口](../../api/nodes/context.memory.candidate.md) |
| `context.memory.policy` | Python、Pydantic、SQLAlchemy、PostgreSQL、pgvector | 记忆读写/版本/冲突/删除，索引及缓存依赖失效 | [设计](../../design/components/context-memory-policy.md) / [接口](../../api/nodes/context.memory.policy.md) |
| `context.memory.conflict` | Python、Pydantic、SQLAlchemy、PostgreSQL、pgvector | 记忆读写/版本/冲突/删除，索引及缓存依赖失效 | [设计](../../design/components/context-memory-conflict.md) / [接口](../../api/nodes/context.memory.conflict.md) |
| `context.memory.store` | Python、Pydantic、SQLAlchemy、PostgreSQL、pgvector | 记忆读写/版本/冲突/删除，索引及缓存依赖失效 | [设计](../../design/components/context-memory-store.md) / [接口](../../api/nodes/context.memory.store.md) |
| `context.memory.forget` | Python、Pydantic、SQLAlchemy、PostgreSQL、pgvector | 记忆读写/版本/冲突/删除，索引及缓存依赖失效 | [设计](../../design/components/context-memory-forget.md) / [接口](../../api/nodes/context.memory.forget.md) |

## 4. 目录与依赖位置

- `src/uaw/context/`
- `src/uaw/context/readers/`
- `src/uaw/context/parsers/`
- `src/uaw/context/indexes/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P1-02 最小上下文、规则和引用](../../plan/rounds/P1-02.md) | 为当前调用提供必要且有来源的输入。 | planned |
| [P2-01 文件上传、摄取与索引发布](../../plan/rounds/P2-01.md) | 把用户办公材料和论文变成可定位、可删除的资料。 | planned |
| [P2-02 联网搜索与网页读取](../../plan/rounds/P2-02.md) | 通过管理员提供方获取可核验外部资料。 | planned |
| [P2-03 技能加载与可复用任务模板](../../plan/rounds/P2-03.md) | 让操作方法按需复用而不靠长主提示词。 | planned |
| [P2-07 办公与学术方法和成果验收](../../plan/rounds/P2-07.md) | 在通用架构上实现两个可复用工作场景。 | planned |
| [P4-01 记忆读写、冲突与遗忘](../../plan/rounds/P4-01.md) | 用户可控制任务是否读取或贡献记忆。 | planned |
| [P4-02 语义压缩、裁剪与稳定前缀](../../plan/rounds/P4-02.md) | 在长任务中保留关键要求和真实执行状态。 | planned |
| [P4-03 角色过滤与向量混合发现](../../plan/rounds/P4-03.md) | 扩大工具目录而保留LLM最终选择。 | planned |
| [P4-04 多层结果缓存与在途合并](../../plan/rounds/P4-04.md) | 在不改变当前权限和结果语义的前提下减少重复工作。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

