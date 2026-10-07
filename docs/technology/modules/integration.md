# 后续推特包装 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [FastAPI](https://fastapi.tiangolo.com/features/) | `fastapi` | HTTP入口、依赖注入与ASGI适配 | 稳定版/Pydantic 2组合 / P0/P1 |
| [HTTPX](https://www.python-httpx.org/async/) | `httpx` | 异步联网与连接池 | 稳定版 / P0/P2 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 接入边界

先复用UAW受理、会话、控制、成果和审批API，再确定X是请求渠道还是社媒业务产品。平台SDK/API配额、授权和发布协议需届时核对官方资料，当前不选择或调用真实X账户。

渠道adapter将外部事件映射到既有原文/主体/任务请求，明确来源与幂等键；业务发布必须走ToolRuntime效果账本。产品flag关闭不适用的代码/本地能力，不能改变UAW固定模型、权限或完成判断。

P5-06仍是后续设计范围，暂无推特实现、自动发布或运营流水线；核心UAW交付不等待此适配。

## 3. 架构子节点的具体技术落点

这是架构边界之外的配套实现分组，按上面的组件分工与相关轮次接入；不创建第八个Runtime或新的任务状态所有者。

## 4. 目录与依赖位置

- `extensions/twitter/`
- `docs/integrations/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P5-06 推特入口适配设计预留](../../plan/rounds/P5-06.md) | UAW独立完成后再确定如何包装到推特。 | deferred |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

