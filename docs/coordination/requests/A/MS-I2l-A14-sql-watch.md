# A14：等待时比较当前 SQL 来源

2026-10-12，继续原 MS-I2l-A9。父版本 `6ec7d0f5ea30d718efcdab29309f8c19c3436366`。
准确阶段源码由 DISPATCH 发布，不要求 D 中途同步，不移动旧标签或开新共同包。

## 实际改动

A13 的 wait_changed 每次轮询都会重新展开两遍完整命令/政策/审批/预算/目录/设备来源。
A14 保持 current 的完整校验和执行边界不变；只改变等待监控的 SQL 部分：

1. 冻结原 command Ref、原 channel Ref 和实际完整 actor。
2. 初次调用完整 current，记录其实际 SQL current/history/不存在输入；最后一次 fresh
   单 SQL witness 与清理必须完成。无实际 SQL 输入或已有外层读取 scope 时拒绝监控。
3. 等待时对同一组地址执行一条新的 SQL UNION 比较完整 schema/revision/payload/存在性。
   未变化时继续等，不重新调用 current，不输出“允许”。每轮连接释放后再睡眠。
4. 发现变化后进行 fresh current，报告具体 owning 拒绝；仍合法的变化也结束等待。
   这次返回只表示监控结束，消费者必须停止原工作，不能把它当执行许可。
5. 整次等待保留原绝对回复 deadline；初次 current 后将监控期限缩短到原 command
   到期时间与 reply deadline 中较早者，不能重新起计时。SQL 阻塞同样受该期限取消。

## 方法与对象边界

`PostgresRecordStore.wait_for_read_change(read, *, deadline, check) -> None` 为 A 内部可信入口。
read 是 owning 元数据校验 callback，不含文件、模型、工具执行或用户等待；check 只检查期限。
本次最多 256 个 current/history 输入，task 隔离；baseline 仅本次函数局部保存，
不返回、不跨调用缓存、不产生准入或 allowed。它用于“是否变化”，不能用于“可以执行”。

`RegisteredRunnerRechecks.wait_changed` 调用这一入口；原签名和输出不变。
`current` 仍执行原完整来源和最终 witness；production `checked_metadata=False` 不变。
没有修改 RunnerCommands.register/collect、发送流程或 D 源码，也不声称其成本已解决。

## 监控覆盖必须分开

| 来源 | A14 等待覆盖 | D 的责任 |
| --- | --- | --- |
| 同 PostgresRecordStore 实际读取的 Run、角色、配置、provider、审批、预算、lease、登记记录 | fresh current/history/墓碑/不存在单 SQL 比较 | effect 前 fresh current，原 CAS 内复核 |
| 原 command 到期与原 reply deadline | 保留较早期限，取消阻塞 I/O | 保留所有其他更早 owning 期限 |
| 当前双方 key、本机 native 根签名/状态、OS 实例/文件句柄、live pipe | 不由 SQL 比较证明 | 独立真实监控与效果边界复查，不能只挂 A wait_changed |

与 A13 相比，wait_changed 的实现范围现在明确为 SQL 变化。它不是通用“所有来源当前仍有效”接口。
D 消费方案须明确 SQL 监控与本机监控如何组合，缺后一部分仍 pending。
若监控 task 正常返回、抛错或到期，D 都应终止原执行；不据返回值恢复或重发 unknown command。
对旧 journal 的读取继续独立数据权限，不改用 active execution current。

50ms 只是轮询间隔，没有 50ms 总响应保证。初次完整 current 和变化后的诊断仍有成本。
单 SQL 查询缩减仅证明组件查询路径，不等于 10 秒内首次文件链通过。

## 实际回执

本阶段 107 节点原来源/取消/批读回归通过；随后最终 watch/current/witness 25 节点通过，
另有原 command 3 秒期限中断原 reply 8 秒内阻塞监控的 1 节点通过。
总去重 108，不是一次 108 或全量产品回归。210 源文件 Mypy、Ruff/格式及最终契约检查
以阶段实际报告为准。没有新的文件读、native 窗口、模型调用或本人成果接受。
旧首次文件失败、清理、原全量与费用保留；flags 不开放。
详细记录见 `docs/implementation/evidence/ms-i2l-a14.json`。
