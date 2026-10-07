# UAW 功能接口总入口

版本：0.1；日期：2026-10-07；对齐架构 0.10。**实现范围逐接口记录；开发协议验证不等于产品闭环或生产部署。**

## 从这里开始

1. [统一规则](CONVENTIONS.md)：信任边界、HTTP状态、幂等、CAS、等待/取消、分页/SSE、字段单位。
2. [关键调用链与实例](FLOWS.md)：创建/调用子Agent、运行代码测试、审批、撤销、完成核验、缓存与恢复。
3. 按类别找到接口；每页均含入口、字段表、返回结构、约束、错误、示例和代码位置。
4. [对象总字典](OBJECTS.md)：所有对象、请求、返回和动作分支逐字段定义。
5. [架构→接口→设计→代码](COVERAGE.md)：核对自己负责模块的契约范围。
6. [Runner消息协议](RUNNER_PROTOCOL.md)与[早期字段迁移](MIGRATION.md)：执行信封、断线对账和旧schema对齐。

## 五类契约

| 类别 | 条目数 | 访问方式 |
| --- | --- | --- |
| [用户与管理端 HTTP API](HTTP.md) | 83 | 用户/管理员认证 |
| [模型可调用工具](TOOL.md) | 35 | 仅暴露业务参数给LLM |
| [本地 Runner 协议](RUNNER.md) | 18 | 可信协议/内部调用 |
| [Runtime 公共入口](RUNTIME.md) | 29 | 可信协议/内部调用 |
| [细分组件私有接口](COMPONENT.md) | 107 | 可信协议/内部调用 |

共 272 条接口契约，1257 个命名schema（含自动生成DTO/互斥分支/严格返回类型），覆盖 115 个当前架构节点。图中的每个小模块是内部组件，不会都变成公网HTTP接口或模型工具。

## 机器文件与维护

| 文件 | 作用 |
| --- | --- |
| [uaw.schema.json](../../contracts/uaw.schema.json) | JSON Schema 2020-12统一对象字典 |
| [openapi.json](../../contracts/openapi.json) | OpenAPI 3.1.1 HTTP路径/参数/响应/认证 |
| [tools.json](../../contracts/tools.json) | 模型工具目录与参数/返回schema引用 |
| [interfaces.json](../../contracts/interfaces.json) | 五类接口、Owner、节点、类型、效果及约束 |
| [interface-map.json](../../contracts/interface-map.json) | 节点到接口/策略/代码目录 |
| [examples.json](../../contracts/examples.json) | 结构示例，不是可直接发出的实际请求 |
| [接口检查结果](contract-check.json) | schema/示例/反例/链接与覆盖检查，运行测试另行标记 |
| [interface_catalog.py](../../contracts/interface_catalog.py) | 人工维护对象、操作和约束的唯一契约源 |
| [build_interfaces.py](../../contracts/build_interfaces.py) | 生成机器契约、逐接口和逐对象文档 |
| [check_interfaces.py](../../contracts/check_interfaces.py) | 验证schema、正反示例、引用、链接和节点覆盖 |

改变接口先改catalog，再生成和验证；不能只编辑生成Markdown/OpenAPI造成字段漂移。详细算法仍由design/catalog.py负责；schema写字段与硬结构约束，策略文档写处理过程。

## 待确认的产品项

- 历史的权威存储位置仍为云端/本地两个部署选项，契约不替用户决定。
- assisted/manual/automatic的产品文案需确认；目前按审批专项文档的暂定语义对接。
- 前端框架、云沙箱提供方与身份登录提供方没有在这些契约中锁定。
