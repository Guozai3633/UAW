# 开发计划当前状态

[总索引](README.md)

计划记录日期2026-10-07：已验收3轮、开发中6轮、待开发40轮、后续讨论1轮。已验收轮数：3。

Context/Tool/Runner首包已合入，Context理解接线已通过；Agent业务循环、apps/web与真实Runner配对/执行仍待建设。当前能力与启动方式见[实际实施入口](../implementation/README.md)。文档检查只核对引用/覆盖/依赖，不能替代运行证据。

| 轮次 | 当前状态 | 范围 | 实现证据 |
| --- | --- | --- | --- |
| [P0-01 工程启动与最小契约](rounds/P0-01.md) | 已验收 | 核心开发范围 | [docs/implementation/P0-01.md](../implementation/P0-01.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P0-02 持久化、CAS、blob与事件提交边界](rounds/P0-02.md) | 开发中 | 核心开发范围 | [docs/implementation/P0-02.md](../implementation/P0-02.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P0-03 最小管理配置、凭据与功能旗标](rounds/P0-03.md) | 已验收 | 核心开发范围 | [docs/implementation/P0-03.md](../implementation/P0-03.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P0-04 受理、原文、状态、事件与资源账本](rounds/P0-04.md) | 已验收 | 核心开发范围 | [docs/implementation/P0-04.md](../implementation/P0-04.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P0-05 固定模型真实调用与协议恢复](rounds/P0-05.md) | 开发中 | 核心开发范围 | [docs/implementation/P0-05.md](../implementation/P0-05.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P1-01 正式任务理解与原文溯源](rounds/P1-01.md) | 开发中 | 核心开发范围 | [docs/implementation/P1-01.md](../implementation/P1-01.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P1-02 最小上下文、规则和引用](rounds/P1-02.md) | 开发中 | 核心开发范围 | [docs/implementation/MS-I1.md](../implementation/MS-I1.md)、[docs/implementation/MS-C2-acceptance.md](../implementation/MS-C2-acceptance.md)、[docs/implementation/MS-I2b.md](../implementation/MS-I2b.md)、[docs/implementation/MS-I2c.md](../implementation/MS-I2c.md)、[docs/implementation/MS-I2d.md](../implementation/MS-I2d.md)、[docs/implementation/MS-I2e.md](../implementation/MS-I2e.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P1-03 工具目录与完整调用闸门](rounds/P1-03.md) | 开发中 | 核心开发范围 | [docs/implementation/MS-I1.md](../implementation/MS-I1.md)、[docs/implementation/MS-I2a.md](../implementation/MS-I2a.md)、[docs/implementation/MS-I2b.md](../implementation/MS-I2b.md)、[docs/implementation/MS-I2c.md](../implementation/MS-I2c.md)、[docs/implementation/MS-I2d.md](../implementation/MS-I2d.md)、[docs/implementation/MS-I2e.md](../implementation/MS-I2e.md)、[docs/implementation/MS-I2f1.md](../implementation/MS-I2f1.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P1-04 Runner配对与项目授权](rounds/P1-04.md) | 开发中 | 核心开发范围 | [docs/implementation/MS-I1.md](../implementation/MS-I1.md)、[docs/implementation/MS-I2a.md](../implementation/MS-I2a.md)、[docs/implementation/MS-I2b.md](../implementation/MS-I2b.md)、[docs/implementation/MS-I2c.md](../implementation/MS-I2c.md)、[docs/implementation/MS-I2d.md](../implementation/MS-I2d.md)、[docs/implementation/MS-I2e.md](../implementation/MS-I2e.md)、[docs/implementation/MS-I2f1.md](../implementation/MS-I2f1.md)、[docs/implementation/evidence/environment.json](../implementation/evidence/environment.json)、[docs/implementation/evidence/p0-tests.xml](../implementation/evidence/p0-tests.xml) |
| [P1-05 输入快照、隔离、环境和真实进程](rounds/P1-05.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P1-06 实际变更、成果与基础审阅](rounds/P1-06.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P1-07 根实例、单Agent循环与工具接线](rounds/P1-07.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P1-08 交付契约、证据和完成提交](rounds/P1-08.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P1-09 人工审批、基础干预与取消](rounds/P1-09.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P1-10 最小API与真实聊天工作区](rounds/P1-10.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P1-11 第一条真实任务阶段验收](rounds/P1-11.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-01 文件上传、摄取与索引发布](rounds/P2-01.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-02 联网搜索与网页读取](rounds/P2-02.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-03 技能加载与可复用任务模板](rounds/P2-03.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-04 会话子Agent定义的设计和版本管理](rounds/P2-04.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-05 首次有界子Agent调用](rounds/P2-05.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-06 共享结果板与Join](rounds/P2-06.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-07 办公与学术方法和成果验收](rounds/P2-07.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-08 角色与子任务页面](rounds/P2-08.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P2-09 三类工作与单子任务验收](rounds/P2-09.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P3-01 语义执行评估与步骤计划](rounds/P3-01.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P3-02 DAG验证与有界调度](rounds/P3-02.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P3-03 独立工具并发与回压](rounds/P3-03.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P3-04 多个子Agent并行与树级约束](rounds/P3-04.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P3-05 并行写隔离与三方合并](rounds/P3-05.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P3-06 块级审阅、局部应用与撤销](rounds/P3-06.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P3-07 复杂运行干预与多会话任务](rounds/P3-07.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P3-08 规划与并行收益验收](rounds/P3-08.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-01 记忆读写、冲突与遗忘](rounds/P4-01.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-02 语义压缩、裁剪与稳定前缀](rounds/P4-02.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-03 角色过滤与向量混合发现](rounds/P4-03.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-04 多层结果缓存与在途合并](rounds/P4-04.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-05 MCP与私人账号连接生命周期](rounds/P4-05.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-06 完整配置与能力包版本发布](rounds/P4-06.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-07 多语言环境、进程回收与可选云后端](rounds/P4-07.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-08 明确Auto授权与能力恢复](rounds/P4-08.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-09 草稿提示、用户控制与完整管理页面](rounds/P4-09.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P4-10 能力增强与撤销一致性验收](rounds/P4-10.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P5-01 跨域检查点与一致提交边界](rounds/P5-01.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P5-02 租约、当前权限与安全续跑](rounds/P5-02.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P5-03 完整观测、版本评测与发布候选](rounds/P5-03.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P5-04 handoff与定时扩展实现](rounds/P5-04.md) | 待开发 | 目标：实现后默认关闭；不挡首次试用 | 为空；没有实现完成声明 |
| [P5-05 单用户工作区受控试用准备](rounds/P5-05.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |
| [P5-06 推特入口适配设计预留](rounds/P5-06.md) | 后续讨论 | 后续适配设计；本次不排实现 | 为空；没有实现完成声明 |
| [P5-07 交付盘点与开发移交](rounds/P5-07.md) | 待开发 | 核心开发范围 | 为空；没有实现完成声明 |

P5-04的‘实现后默认关闭’是交付目标，目前同样未开发；P5-06为后续讨论的适配设计。云执行是否建设待定。核心试用资料的最后门槛是P5-07，完整扩展目标还需P5-04另行验收。

