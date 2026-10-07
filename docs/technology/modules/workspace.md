# Workspace：项目、环境与交付 · 技术组件设计

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
| FSBlobStore | `UAW自有Python适配器` | 私有数据卷中的不可变大内容 | BlobStorePort v0.1 / P0 |
| [websockets](https://websockets.readthedocs.io/en/stable/) | `websockets` | Runner向后端发起WSS长连接 | 稳定版asyncio API / P1/P5 |
| [Git CLI](https://git-scm.com/docs/git-worktree) | `系统Git` | worktree、差异、三方合并 | 探测实际版本并记录 / P3 |
| [Docker/Compose](https://docs.docker.com/engine/security/) | `系统Docker Engine和Compose插件` | 开发服务编排；可选受控Linux执行模板 | 稳定版/镜像digest固定 / P0部署，任务执行按D03/D09 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 后端和真实能力

LocalBackend主选经签名Runner协议执行；isolated_copy用于非Git基础隔离，P3加入Git CLI worktree/三方合并。native模式和受控Linux容器模式分别报告实际范围；权限来自本机批准。副本/worktree隔离写冲突，不提供OS访问隔离。

Python Runtime服务不执行任务代码。Docker用于开发服务编排与可选执行模板时分别配置；任务容器不挂控制面凭据或Docker socket。云执行后端只保留port，D09选定供应商并真实验收后启用。

### 数据与环境

Binding元数据、BaseState、Environment、ChangeSet、Artifact和ReviewSet在SQL；获准本机路径映射和执行账本在Runner。基础快照包含用户未提交文件、排除规则和Hash，不能只从HEAD启动。

环境先inspect用户现有Python/Go/Node工具链，再按批准模板ensure。Runtime用uv锁自己的依赖；任务项目依赖按它自己的锁文件/venv/go.mod处理，环境安装与系统权限单独审批。系统apt/nvm等不是无约束通用安装工具。

### 差异、合并和撤销

实际前后字节Hash与shell造成的修改构成ChangeSet。文本差异可用difflib/Git CLI，UI用Monaco；二进制按文件处理。持久review unit由UAW生成，不能把编辑器临时行号当稳定改动ID。

合并按base/候选/当前三方比较，原子写前再次校验文件Handle/Hash，必要时在同根暂存后替换。并行writer有独立工作区和租约。局部接受和revert只处理选择的unit，保留后续用户编辑；影响证据失效并重验。

下载/预览通过Artifact/Reference resolver，不把模型输出路径直接拼成可读URL。文档/表格格式适配按output contract注册；存在或能打开不等于专业质量已过。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `workspace` | Python、Pydantic、PostgreSQL、websockets | LocalBackend通过签名Runner协议；绑定只来自真实选择 | [设计](../../design/modules/workspace.md) / [接口](../../api/nodes/workspace.md) |
| `workspace.binding` | Python、Pydantic、PostgreSQL、websockets | LocalBackend通过签名Runner协议；绑定只来自真实选择 | [设计](../../design/components/workspace-binding.md) / [接口](../../api/nodes/workspace.binding.md) |
| `workspace.base` | Python、PostgreSQL、FSBlobStore、Git CLI、Docker/Compose | 输入快照/独立副本/worktree；可选受控OS后端报告真实能力 | [设计](../../design/components/workspace-base.md) / [接口](../../api/nodes/workspace.base.md) |
| `workspace.isolation` | Python、PostgreSQL、FSBlobStore、Git CLI、Docker/Compose | 输入快照/独立副本/worktree；可选受控OS后端报告真实能力 | [设计](../../design/components/workspace-isolation.md) / [接口](../../api/nodes/workspace.isolation.md) |
| `workspace.environment` | Python、Pydantic、websockets | Runner进程/模板inspect/ensure，实际工具链和回执 | [设计](../../design/components/workspace-environment.md) / [接口](../../api/nodes/workspace.environment.md) |
| `workspace.process` | Python、Pydantic、websockets | Runner进程/模板inspect/ensure，实际工具链和回执 | [设计](../../design/components/workspace-process.md) / [接口](../../api/nodes/workspace.process.md) |
| `workspace.changes` | Python、PostgreSQL、Git CLI | 实际字节Hash、三方合并、稳定review units、局部接受/撤销 | [设计](../../design/components/workspace-changes.md) / [接口](../../api/nodes/workspace.changes.md) |
| `workspace.artifacts` | Python、Pydantic、PostgreSQL、FSBlobStore、S3 Blob适配 | 产物版本/保留/授权resolver；可选S3 adapter | [设计](../../design/components/workspace-artifacts.md) / [接口](../../api/nodes/workspace.artifacts.md) |
| `workspace.review` | Python、PostgreSQL、Git CLI | 实际字节Hash、三方合并、稳定review units、局部接受/撤销 | [设计](../../design/components/workspace-review.md) / [接口](../../api/nodes/workspace.review.md) |

## 4. 目录与依赖位置

- `src/uaw/workspace/`
- `src/uaw/workspace/backends/`
- `apps/local_runner/uaw_runner/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P1-04 Runner配对与项目授权](../../plan/rounds/P1-04.md) | 让本机项目访问来自真实用户选择和设备授权。 | planned |
| [P1-05 输入快照、隔离、环境和真实进程](../../plan/rounds/P1-05.md) | 运行真实项目检查并保留用户已有修改。 | planned |
| [P1-06 实际变更、成果与基础审阅](../../plan/rounds/P1-06.md) | 用户能看见这次工作改了什么并恢复文件。 | planned |
| [P3-05 并行写隔离与三方合并](../../plan/rounds/P3-05.md) | 把子工作区修改安全纳入用户项目。 | planned |
| [P3-06 块级审阅、局部应用与撤销](../../plan/rounds/P3-06.md) | 用户能选择具体改动和反馈位置。 | planned |
| [P4-07 多语言环境、进程回收与可选云后端](../../plan/rounds/P4-07.md) | 增加真实环境能力并保持安装和执行范围受控。 | planned |
| [P5-05 单用户工作区受控试用准备](../../plan/rounds/P5-05.md) | 把可用能力交给真实用户，保留账号和设备边界。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

