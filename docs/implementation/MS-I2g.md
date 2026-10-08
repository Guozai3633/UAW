# MS-I2g：三个最终组件接受与集成验收

日期：2026-10-08。A维护。**三个组件及受影响装配已接受；完整1077节点回归运行中，尚未记录为通过。** 上一完整运行版本仍是 ms-i2f2 / 841项。下一轮开发基线为 ms-i2h-start；它发布已经接受的组件供 worker 开工，不代表本里程碑全量通过。

## 1. 最终合入与范围

| 包 | 最终源码 / handoff | A合入 | 实际接受 |
| --- | --- | --- | --- |
| B / MS-C5 | 8cc445aa4a05a27c25311f9693b8df2bd2ea8c61 / 233a5c3d1bf5c2c3b939911d13c41dd56d609369 | b47fd81c2efd129b98f09377649030527f06c79c | 登记、当前authority/Reader/规则、快照/引用/ModelPrompt组件 |
| C / MS-T2d | 859f5d0f1ac90dc51e8500282b70d1acee924c06 / db09a698190057870911a9351f5f428bf9919050 | 5721ad42492a2547da491135a5fce9e9bd82a709 | 实际text.inspect、审批/预算/一次发送、独立结果核验与恢复组件 |
| D / MS-R2d | 7d946de7a8aa2321e32ee1af5bdb18610a09ead1 / 366c9165d3ea99707d18943534cc4d0245a97e82 | b73540771b891df44e76abd22c31e59f6d7c2f49 | OS控制签字、有期限实际根来源、适配器与journal组件 |

阶段版已分别提前合入，C/D最终组件此前已接受，本次只接 B最终增量。正常merge无冲突；worker分支、工作区、原handoff和固定开工基线未改写。A没有替worker同步或向聊天发送消息。

B最终增加登记 payload/owner 的 seal、原子撤销与固定Ref回执，校验工具验证器不改固定工具正文，并把 Reader/recipe 的重复全原文展开改为当前绑定前后复查。阶段诊断记录缺 seal，必须使用新 Run重新登记，不能补造证明；这不是生产数据迁移。

A已有三个内部组装入口均保留，B固定构造与GenericModelInputs签名兼容。当前 Run、固定用户模型、角色权限、非空ToolSet版本/权限验证、纯文本完整结果链、Runner独立owner/control签名装配见 [逐方法接线](../coordination/requests/A/MS-I2g-wiring.md)。生产登录真实性、外部LLM、可信IPC及用户原生确认未因此实现。

## 2. 验证证据

- B：**208单元＋85不同SQL=293不同节点通过**。85包含74 Context（39新登记链＋35原SQL）和11兼容SQL。最终首批有一个跨Run fixture准备错误，修复后定向通过；失败原始XML与修复XML均保留，不声称单次全部SQL通过。
- C：162单元＋100不同SQL=262不同节点，通过分批回执及当前测试名称去重；原初枚举失败保留。D：326项通过，真实Windows随机凭据验证通过且已清理。
- A在B最终合入后补跑 **2条当前组合链通过，274.16秒**：登记→snapshot→通用ModelPrompt→材料撤销复查；真实text.inspect→审批/预算/一次发送→独立输出核验→恢复→取消和role撤销。用实际A来源与当前worker最终实现；提供方配置/模型回复为受控协议fixture，没有外部LLM。
- 当前Ruff通过、格式188文件通过、Mypy117源码通过。全量实际收集1077节点，要求真实PostgreSQL且不允许缺库跳过，回执完成后再决定完整里程碑接受。
- 上一 A阶段的268个受影响节点属于 ms-i2g-a1；本页不把它们重复加到新2条或worker节点上，也不把旧841回执当作本轮全量。

[worker回执索引](evidence/ms-i2g-worker-receipts.json) 包含实际SHA、XML摘要、失败修复和OS清理证据；[当前2条组合回执](evidence/ms-i2g-final-wiring-tests.xml)。数据库仅使用 A自身55432；worker模块SQL分别在自身隔离数据库完成。

## 3. 后续开工与剩余边界

下一轮[四个能力包](../coordination/requests/A/MS-I2h-parallel-packages.md)分别是 A/MS-I2h 根实例/单Agent循环、B/MS-C6 多规则评估与读取测量、C/MS-T2e 混合检索/索引、D/MS-R2e file.read只读组件。输入输出、四里程碑、目录和验证边界已明确，固定基线发布后 worker可继续，A同时完成本轮全量；不要求全量结束才开始独立领域开发。

本次没有开启flags、开放通用Agent产品API、安装/写入/exec，没有替用户选择实际模型提供方或决定D01/D03/D06。多规则语义、真实embedding、真实file.read是下一包工作，不计作已实现。当前性能仍需实测，274.16秒的测试包含多步SQL/配置/审批，不能当作单次产品任务延迟。

回退代码不删除持久意图、真实费用、journal或用户成果，不声称撤销外部动作。默认空依赖继续明确不可用。下一轮不要再次派发旧包，转发入口见 [NEXT_WAVE](../coordination/NEXT_WAVE.md)。
