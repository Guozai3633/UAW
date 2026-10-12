# A15：合入 D 消费端，补齐 SQL 监控的事务来源

2026-10-12，继续原 MS-I2l-A9。上一发布为 A14 元数据
`3213f8dfd4888a21d9b83ca54c851b002ac7637d`。准确源码 SHA 由 DISPATCH 正式公布；
不移动旧标签，不建立新共同 start，worker 不消费浮动 integration。

## 本阶段改动与上一阶段修正

1. 精确合入 D 的 M1、测量 wrapper 修复和 M2 最终源码/handoff，保留原提交历史。
   A 的 InstalledReadOnlyHelper 现在通过 super 显式传入同一个 current_source，
   由 D runtime/endpoint/runner 消费，原默认不注入分支保持。
2. A14 只观察 PostgresRecordStore.get，**没有覆盖 RecordTransaction.load**。
   因此 A14 表格对事务读取的 lease、设备来源描述过宽；本阶段才补齐并实测。
3. Database 增加 owning-task 元数据读取 observer。current_witness 在本次 scope 注册 observer；
   同 Database 的 RecordStore.get 和 TransactionalStore.inspect/execute 内 load 都加入同一份观察。
   子 task 不能借用父观察，退出、取消后恢复原 scope。观察保存完整值用于变化比较，不输出许可。
4. installed helper 验证原 principal mapping、bootstrap.registration、root.mapping、
   enrollment service、RecordStore 与 current_source 来源同对象。已有装配还验证账号认证函数
   等于原 browser_sessions.principal，没有从 IPC 文本创建身份或替代权限来源。

RecordTransaction 的可选 Database 参数保持旧调用兼容。事务锁、写入、幂等与 CAS 行为未改。
这里没有启用 checked_metadata 输入优化或缓存 allowed。

## 接口与消费位置

公开 RunnerReadCurrentPort 签名不变：

```python
state = await current_source.current(
    original_command_ref,
    authenticated_principal=original_actor,
    channel_ref=original_channel_ref,
    deadline=original_reply_deadline,
)
await current_source.wait_changed(
    original_command_ref,
    authenticated_principal=original_actor,
    channel_ref=original_channel_ref,
    deadline=original_reply_deadline,
)
```

current 仍完整校验原命令与两轮 owning 来源，最后 fresh SQL witness；D 在实际效果边界消费。
wait_changed 初次完整 current 并捕获实际输入，未变化时每轮一条 fresh SQL UNION；
变化后 fresh current 诊断，合法变化也结束等待。返回、拒绝、期限终止都要求停止原工作，
不能用于准入、恢复执行或重发 unknown。初次校验有实际成本，不能把它视为零成本通知。

底层 A 内部入口 PostgresRecordStore.wait_for_read_change(read, *, deadline, check) -> None
只允许 owning 元数据 callback，无文件/模型/工具效果；最多 256 个地址、task 隔离，
局部 baseline 不跨调用返回或复用，原绝对 deadline 与更早 command 期限保持。
Database observer 不观察 arbitrary raw SQL、list/range 查询或未绑定 Database 的手工 RecordTransaction。
新增生产来源若绕过已审计路径，需要单独证明，不能据“使用同一个数据库”推断覆盖。

## 注册身份覆盖与本机边界

真实 installed 双角色 peer 测试捕获了以下 SQL namespaces：

| SQL 来源 | 对应实际输入 | 核对方式 |
| --- | --- | --- |
| web.sessions | 原用户 Web 会话 | 原 browser_sessions.principal |
| runner.enrollments | 原双角色登记、proof、owner、到期 | 原 EnrolledPeerRegistry 与 enrollment service |
| runner.enrollment.launcher.candidates | 原受保护 launcher 候选 | 原候选读取和拥有者绑定 |
| runner.enrollment.native.decisions | 原账号确认 journal | 原 SQL journal 与签名证据读取 |

此处**账号确认 journal 是 SQL**；目录选择 Ticket/grant/签名 journal 则有本机 SQLite 来源，不能混同。
测试初次 owning read 1 次、fresh SQL 比较 4 次，删除原账号确认记录后监控结束，fresh peer 读取拒绝。
实际 control/device peer、原 OS 双进程、双方密钥与 ACL 使用真实 Windows 来源；native 选择与审批明确受控。
该测试 command0/open0，不是实际首次文件读取或真人确认。

原命令 current 的 registry.session 仍经过完整 session.check；其 EnrolledPeerRegistry 使用同一个
enrollment service/RecordStore，因而通过同 Database observer 进入该次 SQL 捕获。
D 接入时仍须验证实际命令捕获集合与这组 owning 来源对应，不从单独 peer 测试推断任意适配器覆盖。

SQL 监控不能证明当前双方 key、公私钥持有、OS PID/创建时间/SID/logon SID、live pipe、
native SQLite Ticket/grant/目录身份或文件句柄没有变化。D 必须保留独立真实监控和效果前后复查。
双方 peer/public key/proof 原值只用于比较本来的身份，不是 allowed 缓存。

## D 接受范围与失败

| 交付 | 精确 SHA |
| --- | --- |
| M1 源码 | bb24f69761429a110e5906063ed4333220f35f53 |
| M1 文档 | 2748a5524fd22722ad9aab13b831b0d07356e947 |
| 测量 wrapper 修复 | 68c665cf7baea2361b99ba8fb6805e8356384cfe |
| M2 最终源码 | 13ecd4bd44a896f51ec9c736eef0b4d6a8789be2 |
| 最终文档 | 9f8d0f157da36449834b542bc25bfe4aa1dec02b |
| 独立 handoff | cde9ecab1f0c674663d440659bf0bfed26d019f4 |

按组件和接口范围接受。D 自己报告 243 个不同定向节点通过，A 合入后实跑新消费/endpoint 46 节点。
D 原首次链最后仍失败：command1/open0，4 composite 共 7.954 秒，原回复期限终止；
没有 signed journal，原 unknown 不重发。不能将 D 独立原生组件一次 open 成功视为完整生产链成功。
D 当前仍保留每 50ms 完整 session.check 监控，SQL 变化监控尚未消费，本阶段不擅自改 D 源码。

## A 实际回执与后续

本阶段去重 **163** 节点：115 受影响 SQL/source、46 D consumer/endpoint、2 Windows 装配/peer。
这是分批去重，非一次全量；321 历史并集未全部在本源码重跑。已替换的旧单项 lease 测试仍保留
在原 XML，但不与新增 lease/device 参数用例重复计数。首次新测试错误期望、静态格式修复记录保留。
211 源文件 Mypy、15 受影响文件 Ruff/格式通过；452 源码摘要与契约检查见阶段报告。
Windows 两次装配均 command0/open0，随机 4 凭据、2 keys、child、proof 清理检查完成。

准确来源发布后，D 继续原预算修复的监控消费；A 继续原注册/发送/生产来源成本与接线。
首次文件链、固定用户模型文件交付、原本人浏览器接受和汇合全量仍 pending。
flags、子 Agent、DAG、写入/安装/exec 不开放，没有新模型调用或用户正文访问。
实际证据见 docs/implementation/evidence/ms-i2l-a15.json；D 续项见 MS-I2l-A15-D-watch-consumer.md。

## 发布后的实际首次链补验

在准确 `ms-i2l-a15-source` / `1af0a8967ada3b92870c15151f73b31ab09b27e0` 上，
原 A PostgreSQL/Web/Windows 双角色实际链新临时实例运行 50.62 秒失败。native/审批和模型连接元数据受控，
没有访问用户材料或触发本人窗口。完整断言未放宽，新增失败单独记录，不计入163通过节点。

本次 command1/**实际 open1**，原一次执行行1；signed_data 与 published_ref 均不存在。
工具返回 invocation_interrupted，原效果 unknown，不重发；原 journal 恢复断言尚未执行。
5 次 composite 共8.076秒、3次 runner.current 共8.169秒，后一次读后复查取消；
所有原 composite reply deadline 相等。嵌套累计与 startup lifetime 不等于回复段墙钟。
仍保留后台完整 session.check 监控，D 已正式接续 SQL/本机监控修复，不能提前宣称预算达标。
4随机凭据、2 keys、child/proof清理完成。详见 docs/implementation/evidence/ms-i2l-a15-first-chain.json。
