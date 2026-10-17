# MS-I2m A7：B/C/D 最终交付审阅与验收边界

2026-10-17，A / integration。本页按组件、跨模块联调和本人体验分别记录；正式固定源码以 DISPATCH 发布的 A7 准确标签为准。

## 1. 交付、审阅与合入

| 包 | 准确原源码 | 独立交接 | A 处理 |
| --- | --- | --- | --- |
| B / MS-U4 | `5e0b37d90d12641d20e3acf4b704cf79bca3a13d` | `f37265a5d4fc7f5545a0591ab91057e45b29d84c` | 原 M1 及最终交付普通合入，原提交保留；五个0.2接口、实际schema生成、原Run/CAS/身份、受理与生效、刷新只查原请求已审阅 |
| C / MS-E1 M1–M3 | `c8dba72e3a5dc707911c841e3cf6c3bf781d9ac3` | `565bb82daa87dec389af73f4f8f39cf944f4030b` | 普通合入；严格四文件、全attempt/费用、人工与模型建议区分、独占报告发布及版本比较已审阅 |
| D / MS-K1 | `d836bad6cf5b8d2ed04aba3811c5296f33fb0f3b` | `35c43c1d4642fb0c2a2c9183a0e1f7fafb2d6ddf` | 普通合入；原事务clock/binding CAS、主动/等待计量、实际Idle库存与历史上限已审阅 |
| D / 干净目录定向修复 | `f3b3b8c9b984dcafc4fff683663532da3aa0f94b` | `df1b8e6c800bfc04cc6e8aca036f1625f254df77` | 用户明确授权后直接发给D；单行父目录建立修复和独立handoff已普通合入 |

没有操作 worker 分支、同步其工作区或代改其业务文件。B/C/D 原包交付点停止；本页不派发新包，也不把 C 评测范围扩大为 Tool。

## 2. A 的实际复验

- **C：72 个离线节点通过。** 16条候选仍 needs_human_review；没有真实模型输出或人审，不是事实正确率通过。
- **D：8 个单元、47 个 SQL 节点通过。** 47包含原46组件节点及原先 A6 严格跨墙钟失败的实际队列节点；A7恢复入口修复后该原节点通过。
- **A/D额外汇合：3 个真实 SQL 节点通过。** 实际 D 算法接 A 原队列、Model Gateway、补充协议，覆盖原Run完成/停止、两次等待、外层回滚；服务时间和provider回复受控，没有实际 elapsed wait 或DeepSeek质量声明。
- **B：96 个单元＋53个受控Chromium、类型、生成一致性、构建通过。** 原53个Chromium启动错误保留，独立缓存补齐后复跑全过；不能把受控页面验证当实际认证/模型联调。
- **A此前：21个SQL＋14个代理单元最终通过。** 原复现、夹具修复、准备错误回执保留，旧阶段累计不作新全仓。

SQL第一汇合批82通过/1失败/47准备错误：A二次澄清fixture只tick一次，在prepared后尚未生成问题，改为最多四轮、实际问题到达即停；没有修改运行时。D的47准备错误来自干净目录缺ignored回执父目录，由D修复，不改变计时业务。复跑原受影响48节点全部通过。

实际D清理fixture在全新隔离根中核验父目录初始不存在、正常创建、两次append保留原字节；没有删除旧回执。A数据库47个随机fixture用户及原domain派生的platform/admin共141个owner，五张所属表只读检查均0行，未执行清理SQL或访问其他会话数据库。见 `ms-i2m-a7-D-clean-fixture.json`、`ms-i2m-a7-A-cleanup.json`。

## 3. 仍未接受的产品门槛

| 门槛 | 状态与所需来源 |
| --- | --- |
| B M4实际认证联调 | pending；A尚未发布独立新服务和原拥有者Page，不能拿H01-v5代替 |
| C M4真实质量比较 | pending；A需导出固定候选/基线完整attempt、失败、用量与pending费用；真正人工核对另提供 |
| D生产计时/实际长等待 | 组件及受控A整链已验证；独立实际新服务、真实elapsed wait和固定用户模型仍pending |
| Tool跨墙钟动作 | 原claim尚未消费A的内部时间port；新审批还保留原ledger上界，继续保守拒绝 |
| H02本人体验/成果接受 | pending；不能代本人提交、确认本机授权或点击成果接受 |
| 本机首次签名文件链 | 保持原独立未通过结论 |

原快通路及文本成果目标保留。普通回复仍是聊天消息；正式文本/Markdown成果继续实际Artifact、逐项Verification和合同要求的用户接受。原模型、权限、费用上限、旧调用/审批/native期限、unknown对账不重发仍独立检查。

## 4. A 后续顺序

1. 314个不同节点及33文件静态格式、240源码类型均已通过，发布准确A7源码/标签；worker无需为了取元数据合浮动integration。
2. 在独立新实例显式装配 `ExecutionClocks(records,effects=RunIdleEffects())` 与 `ExecutionSegments(records)`，保持H01-v5。
3. 提供同源实际入口和原Page，验证回答、纠正、刷新/取消及文本成果，记录实际固定模型全部失败/费用。
4. 导出C要求的四类文件并准备真正人工核对；没有人审时报告如实incomplete，不给虚假passed。
5. 完整产品门槛汇合后再执行约定的里程碑全量；本页定向复验不更新last_full。
