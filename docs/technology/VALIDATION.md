# 技术选型的兼容与接入验证

[技术总览](../../TECHNOLOGY_STACK.md) · [开发计划](../plan/README.md)

当前状态：P0工程、开发存储、管理配置、受理/账本及模型网关协议已验证，见[实施记录](../implementation/README.md)。真实LLM提供方尚未验收；Agent、Runner和后续阶段场景未通过。以下表格是完整目标门槛，文档链接/覆盖通过不算运行验证通过。

## 1. 各轮冻结什么

| 时点 | 要验证和锁定的组合 | 真实退出条件 |
| --- | --- | --- |
| P0-01 | Python/平台wheel、uv、FastAPI/Pydantic/jsonschema、SQLAlchemy/Psycopg；LangGraph基本API兼容 | 干净环境可构建；严格DTO与现有schema一致，启动/关闭和缺配置失败明确 |
| P0-02 | PostgreSQL、Alembic、BlobStore | 持久受理/CAS/Outbox/重启/备份基本回执；不是内存仓储 |
| P0-05 | 首个批准官方SDK、模型协议、usage | 用户指定模型真实连通，所有attempt与用量可查 |
| P1-04/05 | Runner平台、PySide、WSS、签名、SQLite、Job Objects/psutil、预装Python | 真目录选择、链接越界拒绝、真实测试/停止/断线账本，不把Job Objects或cwd当沙箱 |
| P1-07至P1-09；D11在P1-11前 | LangGraph/EnginePort/ToolBridge、PostgreSQL局部保存与Run审批组合 | 随引擎、人工审批实现完成下述三个最小案例，固定模型与operation身份不丢失 |
| P1-10 | Node/pnpm/React/Vite/Query/Ajv/客户端/Monaco | 实际后端提交、SSE、审批、取消、Diff，不以HTML蓝图代替 |
| P2 | PDF/按需Office解析、网页读取、Skills/子实例 | 实际材料定位、create/invoke区别、引用与单子任务证据 |
| P3 | DAG/工具并发/多个子实例、Git/副本与部分合并 | 资源与版本正确，保留用户修改，比较全部成本/耗时 |
| P4 | pgvector/embedding profile、缓存、MCP、Auto/环境模板 | 权限过滤/撤销/删除/索引失效，实际召回与净收益，真实连接回执 |
| P5 | LangGraph serializer/checkpointer迁移、复合RunCheckpoint、安装包、OIDC/Nginx部署 | 跨领域版本/进程重启恢复/未知效果、账号/设备边界与真实试用资料 |

Python 3.14为设计主线。若某个必须组件没有合适稳定发行版/目标OS wheel，记录具体失败与ADR后可选3.13兼容线，重新锁依赖并跑同样检查；不能把‘支持Python≥某版本’当作整个组合已经兼容。

## 2. LangGraph三个最小案例

### A. 单Agent工具调用

实际根实例使用用户指定模型，图节点只经Context/Model/Tool ports工作；工具参数/结果按契约校验。确认没有额外廉价判断模型、隐式memory或越权原生工具。

### B. 暂停等待批准

需要批准的动作暂停，用户批准存Run；参数/资源/政策revision在等待期间变化，则旧批准不能派发。重复批准和图resume不创建新operation。拒绝后不能换工具绕过。

### C. 实际写入后丢失回执

在提供方/Runner写入成功而图未获得回执时断开工具连接。当前执行在节点再次进入前查询同一operation/command，已成功不再派发；无法查明标unknown并等待。局部图位置、当前审批和文件版本共同验证。P1验证动作账本与节点重入；杀掉整个后端后重新取得租约并恢复复合检查点的场景在P5验证。

P1-07建立引擎和局部保存接线，P1-09接完整人工审批并完成三个案例，D11在P1-11阶段验收前收敛。若失败，保留可复查证据并评估EnginePort回退实现；不能只删检查后宣称框架适配完成。尚未实现完整Run恢复的阶段，服务重启后的未完任务不能自动从图位置继续。

## 3. 跨组件必须检查的风险

- Schema：JSON与Python输入的bool/int、字符串数字、oneOf、未知字段、format、缺省和Decimal处理一致。
- 图保存：只接受约定JSON数据与Ref，重入复用持久动作ID；不存在任意对象/Pickle载入入口。
- SQL：每工作单元独立Session；主体过滤、CAS、短claim和长期栅栏分工明确。
- 前端：cookie/CSRF、SSE去重/断线、草稿revision、账号切换清理；客户端类型不代替权限。
- 签名：JCS、Ed25519域标记/时间/重放/安全整数、双方同payload摘要；缺profile兼容即拒绝。
- 本机：路径/链接/Handle竞态，PID重用、进程组停止、设备撤销、原生权限限制。
- 检索/缓存：中文短查询、ANN过滤召回、embedding换版；撤销/遗忘后旧索引和缓存不能返还内容。
- 发布：依赖稳定版本/镜像digest、数据库/图格式迁移、所支持OS安装包；关闭能力和未实现能力分别报告。

只增加为解决上述具体风险必要的验证。性能上限、接受率和总成本按D08基线登记后比较，不填未经测量的QPS或节省比例。

## 4. 本轮文档校验范围

`python technology/build_stack.py`核对模块/组件ID、115节点映射、现有设计/接口/开发轮引用和本地文档链接；输出technology-check.json。它不会安装上述技术或探测机器能力。

实际兼容/运行证据写入 `docs/implementation/<轮次>.md`，冻结版本见uv.lock及环境记录，部署决定进入 `docs/decisions/`。当前证据覆盖P0-01、P0-02开发存储以及P0-03/04开发控制层；实际模型/Agent/Runner及最终部署尚未通过验收。
