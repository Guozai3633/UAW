# 全局实施顺序与并行条件

[模块索引](README.md) · [阶段门槛](STAGES.md)

模块页按职责查找，实际开工按本页依赖交替推进。轮号是推荐阅读顺序，开工取决于前置证据；同阶段满足依赖的独立任务可以并行开发。下一阶段的正式验收以先前核心阶段门槛通过为前提。

当前已增加[4个session的组件分工](PARALLEL.md)与[开工/合并规则](PARALLEL_WORKFLOW.md)。组件开发依赖和整轮验收依赖分开记录，原50轮完整门槛保持有效。

## 关键依赖与可并行部分

| 范围 | 执行建议 |
| --- | --- |
| P0 | 工程→存储→配置→受理/账本→真实模型；先让开发环境和授权身份可靠 |
| P1 | 理解/上下文/工具→Runner/实际环境/变更→单循环/核验→用户控制/真实页面→闭环验收；页面草图和fixture准备可提前 |
| P2 | 文件→搜索与技能/定义→单子调用/Join；搜索P2-02与技能P2-03在P2-01后可独立推进，办公/学术汇合后验收 |
| P3 | steps→DAG校验/调度后，工具并发P3-03与子Agent并发P3-04可分开开发；写合并/审阅/多会话仍按依赖继续 |
| P4 | 内容依赖/检索/缓存/连接治理先接稳；P4-06后环境P4-07与Auto P4-08可独立推进，完整页面汇合 |
| P5 | 检查点→恢复→评测/试用资料；P5-04可与评测准备独立推进但不挡首次试用，推特设计继续后置 |

这里的并行是团队实施安排，不强制运行中多Agent。共同修改schema/配置/公共契约时要协调版本，不能因开发可并行就跳过Runtime资源隔离。

## 所有轮次与有效前置

有效前置包含显式工作包依赖和上一阶段核心门槛。

| 轮次/模块 | 本轮目标 | 有效前置 |
| --- | --- | --- |
| [P0-01 工程启动与最小契约](rounds/P0-01.md) / 工程与集成 | 建立能启动的Python应用和依赖组装，避免先实现全部未来DTO。 | 无 |
| [P0-02 持久化、CAS、blob与事件提交边界](rounds/P0-02.md) / 配置与共享设施 | 让受理/版本冲突和大内容存取有唯一权威。 | [P0-01](rounds/P0-01.md) |
| [P0-03 最小管理配置、凭据与功能旗标](rounds/P0-03.md) / 配置与共享设施 | 从控制层向Runtime提供固定配置和当前撤销状态。 | [P0-02](rounds/P0-02.md) |
| [P0-04 受理、原文、状态、事件与资源账本](rounds/P0-04.md) / Run Runtime | 保存原文并以真实状态和用量驱动后续执行。 | [P0-02](rounds/P0-02.md)、[P0-03](rounds/P0-03.md) |
| [P0-05 固定模型真实调用与协议恢复](rounds/P0-05.md) / Model Runtime | 完整执行用户选择的模型，不做静默模型替换。 | [P0-03](rounds/P0-03.md)、[P0-04](rounds/P0-04.md) |
| [P1-01 正式任务理解与原文溯源](rounds/P1-01.md) / Intent Runtime | 得到有版本、可纠正的TaskFrame。 | [P0-04](rounds/P0-04.md)、[P0-05](rounds/P0-05.md) |
| [P1-02 最小上下文、规则和引用](rounds/P1-02.md) / Context Runtime | 为当前调用提供必要且有来源的输入。 | [P0-02](rounds/P0-02.md)、[P0-05](rounds/P0-05.md)、[P1-01](rounds/P1-01.md) |
| [P1-03 工具目录与完整调用闸门](rounds/P1-03.md) / Tool Runtime | 使模型提出的动作经过参数、权限、审批和真实结果处理。 | [P0-03](rounds/P0-03.md)、[P0-04](rounds/P0-04.md)、[P1-02](rounds/P1-02.md)、[P0-05](rounds/P0-05.md) |
| [P1-04 Runner配对与项目授权](rounds/P1-04.md) / Workspace与本地Runner | 让本机项目访问来自真实用户选择和设备授权。 | [P0-03](rounds/P0-03.md)、[P1-03](rounds/P1-03.md)、[P0-05](rounds/P0-05.md) |
| [P1-05 输入快照、隔离、环境和真实进程](rounds/P1-05.md) / Workspace与本地Runner | 运行真实项目检查并保留用户已有修改。 | [P1-04](rounds/P1-04.md)、[P0-05](rounds/P0-05.md) |
| [P1-06 实际变更、成果与基础审阅](rounds/P1-06.md) / Workspace与本地Runner | 用户能看见这次工作改了什么并恢复文件。 | [P1-05](rounds/P1-05.md)、[P0-05](rounds/P0-05.md) |
| [P1-07 根实例、单Agent循环与工具接线](rounds/P1-07.md) / Agent Runtime | 由主Agent动态决定下一步并完成实际工作。 | [P1-01](rounds/P1-01.md)、[P1-02](rounds/P1-02.md)、[P1-03](rounds/P1-03.md)、[P1-05](rounds/P1-05.md)、[P1-06](rounds/P1-06.md)、[P0-05](rounds/P0-05.md) |
| [P1-08 交付契约、证据和完成提交](rounds/P1-08.md) / Agent Runtime | 以真实要求、实际检查和版本决定是否完成。 | [P1-07](rounds/P1-07.md)、[P0-05](rounds/P0-05.md) |
| [P1-09 人工审批、基础干预与取消](rounds/P1-09.md) / Run Runtime | 用户可停止或修正当前单Agent任务。 | [P1-07](rounds/P1-07.md)、[P1-08](rounds/P1-08.md)、[P0-05](rounds/P0-05.md) |
| [P1-10 最小API与真实聊天工作区](rounds/P1-10.md) / API与前端 | 让用户从页面完成第一条任务和审阅。 | [P1-09](rounds/P1-09.md)、[P0-05](rounds/P0-05.md) |
| [P1-11 第一条真实任务阶段验收](rounds/P1-11.md) / 工程与集成 | 证明从用户输入到检查、变更和接受完整可用。 | [P1-10](rounds/P1-10.md)、[P0-05](rounds/P0-05.md) |
| [P2-01 文件上传、摄取与索引发布](rounds/P2-01.md) / Context Runtime | 把用户办公材料和论文变成可定位、可删除的资料。 | [P1-11](rounds/P1-11.md) |
| [P2-02 联网搜索与网页读取](rounds/P2-02.md) / Tool Runtime | 通过管理员提供方获取可核验外部资料。 | [P2-01](rounds/P2-01.md)、[P0-03](rounds/P0-03.md)、[P1-11](rounds/P1-11.md) |
| [P2-03 技能加载与可复用任务模板](rounds/P2-03.md) / Agent Runtime | 让操作方法按需复用而不靠长主提示词。 | [P2-01](rounds/P2-01.md)、[P1-11](rounds/P1-11.md) |
| [P2-04 会话子Agent定义的设计和版本管理](rounds/P2-04.md) / Agent Runtime | 用户可用自然语言创建、修改和撤销角色。 | [P2-03](rounds/P2-03.md)、[P0-05](rounds/P0-05.md)、[P1-11](rounds/P1-11.md) |
| [P2-05 首次有界子Agent调用](rounds/P2-05.md) / Agent Runtime | 把定义转换为独立上下文和受限执行实例。 | [P2-04](rounds/P2-04.md)、[P1-09](rounds/P1-09.md)、[P1-11](rounds/P1-11.md) |
| [P2-06 共享结果板与Join](rounds/P2-06.md) / Agent Runtime | 父Agent可靠收集结果并保留最终交付责任。 | [P2-05](rounds/P2-05.md)、[P1-11](rounds/P1-11.md) |
| [P2-07 办公与学术方法和成果验收](rounds/P2-07.md) / Agent Runtime | 在通用架构上实现两个可复用工作场景。 | [P2-02](rounds/P2-02.md)、[P2-03](rounds/P2-03.md)、[P2-06](rounds/P2-06.md)、[P1-11](rounds/P1-11.md) |
| [P2-08 角色与子任务页面](rounds/P2-08.md) / API与前端 | 用户可查角色、修改配置并了解子任务结果。 | [P2-07](rounds/P2-07.md)、[P1-10](rounds/P1-10.md)、[P1-11](rounds/P1-11.md) |
| [P2-09 三类工作与单子任务验收](rounds/P2-09.md) / 工程与集成 | 形成独立UAW的基础产品证据。 | [P2-08](rounds/P2-08.md)、[P1-11](rounds/P1-11.md) |
| [P3-01 语义执行评估与步骤计划](rounds/P3-01.md) / Agent Runtime | 独立判断规划、委派、并发和信息缺口。 | [P2-09](rounds/P2-09.md) |
| [P3-02 DAG验证与有界调度](rounds/P3-02.md) / Agent Runtime | 以真实依赖和资源执行任务图。 | [P3-01](rounds/P3-01.md)、[P2-09](rounds/P2-09.md) |
| [P3-03 独立工具并发与回压](rounds/P3-03.md) / Tool Runtime | 只并发可证明独立的动作，并保持账本正确。 | [P3-02](rounds/P3-02.md)、[P2-09](rounds/P2-09.md) |
| [P3-04 多个子Agent并行与树级约束](rounds/P3-04.md) / Agent Runtime | 运行多个独立分工并控制父子深度、预算和取消。 | [P3-02](rounds/P3-02.md)、[P2-06](rounds/P2-06.md)、[P2-09](rounds/P2-09.md) |
| [P3-05 并行写隔离与三方合并](rounds/P3-05.md) / Workspace与本地Runner | 把子工作区修改安全纳入用户项目。 | [P3-04](rounds/P3-04.md)、[P1-06](rounds/P1-06.md)、[P2-09](rounds/P2-09.md) |
| [P3-06 块级审阅、局部应用与撤销](rounds/P3-06.md) / Workspace与本地Runner | 用户能选择具体改动和反馈位置。 | [P3-05](rounds/P3-05.md)、[P2-09](rounds/P2-09.md) |
| [P3-07 复杂运行干预与多会话任务](rounds/P3-07.md) / Run Runtime | 处理目标修订、排队、部分交付和同用户共享任务。 | [P3-04](rounds/P3-04.md)、[P3-06](rounds/P3-06.md)、[P2-09](rounds/P2-09.md) |
| [P3-08 规划与并行收益验收](rounds/P3-08.md) / 工程与集成 | 以真实结果证明复杂执行方式何时值得启用。 | [P3-03](rounds/P3-03.md)、[P3-07](rounds/P3-07.md)、[P2-09](rounds/P2-09.md) |
| [P4-01 记忆读写、冲突与遗忘](rounds/P4-01.md) / Context Runtime | 用户可控制任务是否读取或贡献记忆。 | [P3-08](rounds/P3-08.md) |
| [P4-02 语义压缩、裁剪与稳定前缀](rounds/P4-02.md) / Context Runtime | 在长任务中保留关键要求和真实执行状态。 | [P4-01](rounds/P4-01.md)、[P3-08](rounds/P3-08.md) |
| [P4-03 角色过滤与向量混合发现](rounds/P4-03.md) / Tool Runtime | 扩大工具目录而保留LLM最终选择。 | [P4-02](rounds/P4-02.md)、[P2-04](rounds/P2-04.md)、[P3-08](rounds/P3-08.md) |
| [P4-04 多层结果缓存与在途合并](rounds/P4-04.md) / 配置与共享设施 | 在不改变当前权限和结果语义的前提下减少重复工作。 | [P4-03](rounds/P4-03.md)、[P3-08](rounds/P3-08.md) |
| [P4-05 MCP与私人账号连接生命周期](rounds/P4-05.md) / Tool Runtime | 可安装接入能力，但授权由真实账户和政策决定。 | [P4-04](rounds/P4-04.md)、[P0-03](rounds/P0-03.md)、[P3-08](rounds/P3-08.md) |
| [P4-06 完整配置与能力包版本发布](rounds/P4-06.md) / 配置与共享设施 | 管理员可验证、发布、停用和恢复配置或插件。 | [P4-05](rounds/P4-05.md)、[P3-08](rounds/P3-08.md) |
| [P4-07 多语言环境、进程回收与可选云后端](rounds/P4-07.md) / Workspace与本地Runner | 增加真实环境能力并保持安装和执行范围受控。 | [P4-06](rounds/P4-06.md)、[P3-05](rounds/P3-05.md)、[P3-08](rounds/P3-08.md) |
| [P4-08 明确Auto授权与能力恢复](rounds/P4-08.md) / Model Runtime | 固定模型仍不变，Auto只能在用户授权范围内选择。 | [P4-06](rounds/P4-06.md)、[P3-08](rounds/P3-08.md) |
| [P4-09 草稿提示、用户控制与完整管理页面](rounds/P4-09.md) / API与前端 | 完成实际能力的可理解交互，区分用户和管理员。 | [P4-01](rounds/P4-01.md)、[P4-07](rounds/P4-07.md)、[P4-08](rounds/P4-08.md)、[P3-08](rounds/P3-08.md) |
| [P4-10 能力增强与撤销一致性验收](rounds/P4-10.md) / 工程与集成 | 验证效率增强不复活过期权限或影响成果质量。 | [P4-09](rounds/P4-09.md)、[P3-08](rounds/P3-08.md) |
| [P5-01 跨域检查点与一致提交边界](rounds/P5-01.md) / Run Runtime | 保存可核验的续跑位置和未决动作。 | [P4-10](rounds/P4-10.md) |
| [P5-02 租约、当前权限与安全续跑](rounds/P5-02.md) / Run Runtime | 恢复未完工作而不重复未知外部写。 | [P5-01](rounds/P5-01.md)、[P4-10](rounds/P4-10.md) |
| [P5-03 完整观测、版本评测与发布候选](rounds/P5-03.md) / 配置与共享设施 | 用真实结果和成本决定版本是否可试用。 | [P5-02](rounds/P5-02.md)、[P3-08](rounds/P3-08.md)、[P4-10](rounds/P4-10.md) |
| [P5-04 handoff与定时扩展实现](rounds/P5-04.md) / Agent Runtime | 完善已规划扩展，但独立UAW首个试用默认关闭。 | [P5-02](rounds/P5-02.md)、[P3-04](rounds/P3-04.md)、[P4-10](rounds/P4-10.md) |
| [P5-05 单用户工作区受控试用准备](rounds/P5-05.md) / API与前端 | 把可用能力交给真实用户，保留账号和设备边界。 | [P5-03](rounds/P5-03.md)、[P4-09](rounds/P4-09.md)、[P4-10](rounds/P4-10.md) |
| [P5-06 推特入口适配设计预留](rounds/P5-06.md) / 后续入口适配 | UAW独立完成后再确定如何包装到推特。 | [P5-03](rounds/P5-03.md)、[P4-10](rounds/P4-10.md) |
| [P5-07 交付盘点与开发移交](rounds/P5-07.md) / 工程与集成 | 把实际完成、未完成和默认关闭能力分别列清。 | [P5-05](rounds/P5-05.md)、[P4-10](rounds/P4-10.md) |

## 缺外部条件时怎样继续

- 缺提供方配置：可核对schema、适配器协议和受控fixture；实际调用门槛仍待配置。
- 未确定存储/前端/部署：可做ports、任务材料和独立职责代码；涉及权威数据、真实界面或执行环境的轮不能凭测试替身验收。
- 某轮失败：记录具体失败、保留已确认成果，只开放不依赖失败部分的工作包。
- 改范围或拆子轮：同时修catalog中的依赖、节点和验收，再重建计划；不要直接改生成文件让链路脱节。

