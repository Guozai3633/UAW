# Intent：用户问题加工 · 技术组件设计

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

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 技术怎样串起来

原文从Run读取 → 按目的向Context取资料 → 通过ModelGateway请求当前继承模型 → jsonschema验证结构 → 原文含义/引用/修订核验 → Repository按CAS提交TaskFrame。

模型输出只能作为理解提案。TaskFrame持久化与原文追加存储分别归Intent/Run；不引入另一个LangChain会话历史。语义解析、指代和歧义用当前模型，路径/版本/字段检查用Python。探查材料通过Tool facade。

### 子组件策略

- Preview：短延迟debounce、草稿revision、任务取消和有效期由自有控制器处理。服务端只读、低预算；模型仍继承用户选择。页面仅接受当前草稿revision。
- Original/Frame：不可变原文Ref、补充来源和框架revision可追溯，SQL更新带预期版本。不能覆盖用户原文。
- Semantic/References/Ambiguity：短模板按需加载。结构错误有界反馈，语义不确定明确记录；不靠词典或输入长度分档。
- Probe：只有确有信息缺口时发现并调用获准工具，不直接绕Tool访问文件或联网。

### 状态与替换边界

无框架专属状态。更换模型adapter或Agent执行引擎，不改变TaskFrame与原文协议。预览缓存只复用同草稿/相同配置依赖，不能拿草稿结果直接作为正式TaskFrame提交。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `intent` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 原文Ref/理解版本与CAS，自有facade | [设计](../../design/modules/intent.md) / [接口](../../api/nodes/intent.md) |
| `intent.preview` | Python、Pydantic、JSON Schema校验器 | 通过ModelGateway做语义提案，原文/版本/来源用代码校验 | [设计](../../design/components/intent-preview.md) / [接口](../../api/nodes/intent.preview.md) |
| `intent.original` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 原文Ref/理解版本与CAS，自有facade | [设计](../../design/components/intent-original.md) / [接口](../../api/nodes/intent.original.md) |
| `intent.semantic` | Python、Pydantic、JSON Schema校验器 | 通过ModelGateway做语义提案，原文/版本/来源用代码校验 | [设计](../../design/components/intent-semantic.md) / [接口](../../api/nodes/intent.semantic.md) |
| `intent.references` | Python、Pydantic、JSON Schema校验器 | 通过ModelGateway做语义提案，原文/版本/来源用代码校验 | [设计](../../design/components/intent-references.md) / [接口](../../api/nodes/intent.references.md) |
| `intent.probe` | Python、Pydantic | 通过Tool port按需探查，不能直接执行本地/网络动作 | [设计](../../design/components/intent-probe.md) / [接口](../../api/nodes/intent.probe.md) |
| `intent.ambiguity` | Python、Pydantic、JSON Schema校验器 | 通过ModelGateway做语义提案，原文/版本/来源用代码校验 | [设计](../../design/components/intent-ambiguity.md) / [接口](../../api/nodes/intent.ambiguity.md) |
| `intent.frame` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 原文Ref/理解版本与CAS，自有facade | [设计](../../design/components/intent-frame.md) / [接口](../../api/nodes/intent.frame.md) |

## 4. 目录与依赖位置

- `src/uaw/intent/`
- `prompts/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P1-01 正式任务理解与原文溯源](../../plan/rounds/P1-01.md) | 得到有版本、可纠正的TaskFrame。 | in_progress |
| [P3-01 语义执行评估与步骤计划](../../plan/rounds/P3-01.md) | 独立判断规划、委派、并发和信息缺口。 | planned |
| [P4-09 草稿提示、用户控制与完整管理页面](../../plan/rounds/P4-09.md) | 完成实际能力的可理解交互，区分用户和管理员。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

