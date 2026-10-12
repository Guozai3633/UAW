# A19：审批复查不在会话锁内等待外部权威

2026-10-12，继续 Session A / integration，父发布
`a1cd7f048953d47ad455d88eaec03f6a8f0fe1aa`。准确源码由 DISPATCH 随后发布。
只改 A 的 `src/uaw/run/approval.py` 和 A 定向验证；不修改 worker 业务或分支。

## 问题与处理顺序

原 `ApprovalService.recheck` 在持有会话 PostgreSQL advisory transaction lock 时，
调用整个 `authority.check`。真实文件 authority 会等待工具来源、目录、账号、设备与本机 key。
执行与监控同时复查时，后一方无法进入；同会话的取消也要等待这段外部工作。

本次将只读复查改为：

1. 持锁读取当前审批、原 binding、grant，并执行完整 SQL/政策/权限/期限谓词。
2. 释放事务和会话锁，再调用原 authority，一次实际等待，不复用 allowed。
3. 新事务再次持锁，重新读取并验证相同来源；比较前后完整 payload、schema 和 revision。
4. 等待后检查调用方较短期限与 authority 对象，任何变化拒绝；返回最后实际 grant。

比较包含 Run、预算账本、Run 配置 binding、会话、固定及当前配置、审批政策和权限 snapshot。
审批与 binding 必须仍与原完整内容、原 revision 相同；grant 内容或 revision 变化也拒绝。
两次事务各自新鲜；SQL观察器仍看到实际 load，原外层 witness 与 Runner 两轮来源检查保持。
这不提供跨 SQL/OS/native 的原子性；执行器原关键 await 前后复核和效果 CAS 仍必要。

`_authorization_records` 是内部 SQL 谓词，不是独立批准入口，不存许可。
`request/decide` 仍在原写事务内调用完整 `_authorize`，写入/CAS/事件/人工决定保持。
公共 DTO、端口、认证、管理员配置与 flags 不变。原回复、lease、root、启动期限均不延长。

## 验证与实际范围

- 两个真实 SQL 复查能同时进入外部等待；独立连接确实取得同一会话 advisory lock。
- 外部等待期间，真实 Run 取消可提交；等待后拒绝旧授权。
- 等待期间修改权限政策、审批 binding、grant、会话模式或账本期限，均拒绝。
- authority 拒绝与取消不生成新 grant；后续新调用仍重新核对实际来源。
- 调用方较短期限跨越等待后仍拒绝，原批准期限不会覆盖调用期限。

首次审批批次 39 通过、1 失败：测试误用不存在的 `auto_review` 枚举。
修为既有 `automatic` 后，同一批 40 通过。初次 Mypy 的返回 Any 注解错误已修复。
原失败、中断和最终定向回执均保留；追加来源回归与静态结果以 A19 JSON 为准。

追加23项原registered current/工具审批来源和调用方短期限通过；两批不同节点63，
411历史并集未全部重跑。212源码Mypy、2文件Ruff/格式通过，467源码摘要固定。

原完整 Windows 文件链单独运行 **103.49秒、1失败**：command1/open0，无签名回执。
原10秒 IPC reply 期限结束，unknown 不重发；4随机凭据、2keys、child/proof清理完成。
3 composite 累计10.062秒包含监控与执行并行；不能与墙钟相加。
本次墙钟负载和之前不同，不能用不同轮样本声称整体提速或回归比例。
这只证明审批锁外等待及等待后拒绝正确，不能证明首次材料读取、签名 journal 或恢复成功。

## 后续与归属

B/C/D保留交付点，无新包、不自动同步浮动 integration。
A继续处理执行边界的重复来源图；本次未消除完整工具/角色/Run/账号/设备图的重复展开。
后续首先定位每次 current 内的重复节点与真实查询/native次数，再定义有界单次观察和等待后失效检查，
不能通过缓存批准、移走期限或减少撤销检查换取通过。业务缺陷交原 worker。

实际首次文件、固定模型材料引用/成果、本人页面/接受与汇合全量仍 pending。
本次没有模型调用、用户文件访问或本人确认操作；不开放子Agent/DAG/本机写入安装exec。
旧1691全量、旧标签、模型失败/费用和所有首次链失败保持。
