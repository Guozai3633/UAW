# API与账号入口 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [FastAPI](https://fastapi.tiangolo.com/features/) | `fastapi` | HTTP入口、依赖注入与ASGI适配 | 稳定版/Pydantic 2组合 / P0/P1 |
| [Uvicorn](https://github.com/Kludex/uvicorn) | `uvicorn` | ASGI进程入口 | 与FastAPI验证后锁定 / P0/P1 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |
| [Authlib/OIDC](https://github.com/authlib/authlib) | `authlib` | 账号登录协议适配 | 稳定版；IdP由管理员配置 / P5，开发身份先独立 |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | `sqlalchemy` | 领域Repository与事务适配 | 2.x异步API / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### HTTP、事件流与设备连接

FastAPI处理认证、输入、归属、配额和Run受理，返回既有业务Envelope；不在请求handler里跑完整长任务。InteractionItem/Event读当前授权后以SSE输出，断线用持久seq/cursor恢复。

Runner协议用受认证WSS双向长连接；配对/连接HTTP路由在实现轮加入契约源，现有设计消息契约不能当作已经部署路由。API不会执行任意本地路径或shell。

### 契约与运行路由

contracts/interface_catalog.py继续作为字段权威。优先实现实际任务所需DTO，Pydantic strict/extra=forbid与jsonschema在边界核验；特定JSON解析的宽松转换也要被统一schema约束。

运行OpenAPI从实际路由生成，并与设计契约中已实现子集做兼容检查。设计81个HTTP操作不自动注册81个成功占位handler。权限来自认证依赖生成TrustedExecutionContext，业务参数不能填admin/approved。

### 身份主选

账号接入选Authlib OIDC adapter，IdP部署/供应商仍由管理员确定。后端处理授权码、state/nonce/PKCE和回调校验，服务端会话cookie为HttpOnly/Secure，账户资源由主体条件限制。

Web与API同源部署，修改动作校验Origin和CSRF token。浏览器缓存不保存平台或第三方令牌。P0仅本机可达开发主体允许独立推进；公网试用前必须接真实身份，OIDC库不自动提供账户产品。

### 失败和限流

SSE慢消费者有界缓冲，超过保留窗口用授权快照续接；一次接收的事件重复不创建重复UI项。断开页面不代表取消Run，取消走明确控制接口。管理员接口单独验证角色，不暴露普通Agent调用。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `ingress` | FastAPI、Uvicorn、Pydantic、JSON Schema校验器、Authlib/OIDC | 认证依赖注入可信上下文，SSE/WSS适配；技术模块api | [设计](../../design/components/ingress.md) / [接口](../../api/nodes/ingress.md) |

## 4. 目录与依赖位置

- `src/uaw/api/`
- `src/uaw/infrastructure/identity/`
- `src/uaw/infrastructure/http/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P0-03 最小管理配置、凭据与功能旗标](../../plan/rounds/P0-03.md) | 从控制层向Runtime提供固定配置和当前撤销状态。 | accepted |
| [P1-10 最小API与真实聊天工作区](../../plan/rounds/P1-10.md) | 让用户从页面完成第一条任务和审阅。 | planned |
| [P2-08 角色与子任务页面](../../plan/rounds/P2-08.md) | 用户可查角色、修改配置并了解子任务结果。 | planned |
| [P4-09 草稿提示、用户控制与完整管理页面](../../plan/rounds/P4-09.md) | 完成实际能力的可理解交互，区分用户和管理员。 | planned |
| [P5-05 单用户工作区受控试用准备](../../plan/rounds/P5-05.md) | 把可用能力交给真实用户，保留账号和设备边界。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

