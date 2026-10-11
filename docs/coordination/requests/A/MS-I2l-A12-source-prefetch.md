# A12：按原来源标识批读最新记录

2026-10-12。继续 MS-I2l-A9 来源与预算工作，不建立新共同基线或自动扩 worker 包。
父版本 `d73349201a29ed3ba2bcf319aee539a636a75567`。准确阶段 SHA 由 DISPATCH 发布。

## 目的与边界

A11 只去除同一次 metadata pass 中重复读取同一行的 SELECT；不同来源仍逐条读。
A12 在显式内部 `checked_metadata=True` 时，让已完成检查的原来源记住所读行的标识。
下一次 pass 用一条新的 READ COMMITTED SELECT 读取这些行，然后执行完整原校验，
末尾再次用新的 SELECT 比较完整行。没有保存上一次的值、批准结论或执行权限。

production 默认仍为 `False`。新逻辑不能直接证明首次文件链或产品门槛通过。
本轮没有修改 D endpoint、session、admission、执行器；current/watch 的生产消费仍待接线。

## 输入、输出与生命周期

内部方法 `PostgresRecordStore.checked_read_batch(*, plan: tuple[str, ...] | None = None)`：

| 项目 | 具体约束 |
| --- | --- |
| plan | 1–4 个非空字符串，每项至多 256 字符；来源拥有者组装，不从 IPC 请求读取 |
| 命令来源 | `("runner-command", controller.id, original_command_id)` |
| 账号设备来源 | `("enrollment", original_enrollment_id, original_user.id, original_auth_session_id)` |
| 保存内容 | 最多 64 个 plan，每个至多 256 个 `(principal_id, namespace, resource_id)`；只保存标识 |
| 输出 | 无授权输出；上下文正常结束只表示本次记录 witness 一致 |
| 默认关闭 | 每个 get 仍查询当前 SQL；不学习 plan，不复用任何行输入 |
| 开启后的首次使用 | 当前 get 实际读取未知行；完整校验和最终 witness 成功后学习标识 |
| 开启后的再次使用 | 先批读当前完整行，再执行所有原校验；未预测的新来源仍实际 get |
| 末尾 | 再次批读所有本次行，比较存在性、schema、revision、完整 payload；不一致拒绝整次 pass |
| 历史版本 | 仍独立读取历史版本并检查当前墓碑，不由 plan 提供历史值 |
| 缺失行 | 不缓存不存在；原 get 实际查询并拒绝，不能把旧存在性当当前存在性 |
| 并发与嵌套 | 每个 task 独立 SQL/session/行输入；同 task 的嵌套源共享外层 witness |
| 失败与取消 | 清除本次行/session；失败不学习新 plan；既有 plan 也不提供下一次权限 |
| 容量 | plan LRU 超过 64 移除最旧标识；本次行超过 256 拒绝，不截断验收 |

每次 get 仍验证调用者 Principal 与标识。原来源拥有者继续检查完整用户、角色、设备、
workspace、Tool、政策、模型、审批、预算、lease/fence 和所有原期限。
OS 实例、当前双方 key、实际 native journal/签名、实际 root 和通道仍由原来源检查。
SQL 输入缩减不替代这些外部来源，也不允许跨文件执行、模型、native UI 或用户等待保留本次输入。

## A/D 接线状态

`RegisteredRunnerRechecks.recheck/wait_changed` 仍使用原 command Ref、完整认证 Principal、
原 channel Ref 和原响应 deadline；返回的 snapshot 是完整校验后的投影，不是授予权限的接口。
当前 implementation 仍展开全部校验；A12 不声称 50ms 轮询是 50ms 校验耗时。
D 原实现保持不动，也不要求 D 消费浮动 integration。需要改 D 消费时应先固定准确来源版、
具体输入和端点约束，再发布明确任务；本文件不是新 D 派发。

## 验证与失败记录

本阶段真实 SQL 与原权威/撤销定向批次 92 项通过：
`tests/.artifacts/A/MS-I2l/a12-prefetch-regression.xml`。
首批 2 项失败来自错误地对异常展示文案匹配错误码；已改为检查实际 `failure.code`，
未改变拒绝要求，原 XML 保留。一次命令使用不存在的测试文件、一次 Mypy 未纳入本机包源码，
都保留原输出；正确范围 Mypy 已检查 210 源文件通过。

新测试验证批读获取已更新值、末尾更新/删除拒绝、旧标识删除不授予存在性、plan 容量与失败不学习。
原取消、命令、角色 key、原会话、native journal、通道、最终 SQL 等待后 key 撤销回归仍保留。
受控测量对照相同 actual SQL/registered snapshot；channel/root/gate 输入为受控来源，
SELECT 数量与耗时不能替代完整 Windows 链性能或真人授权。

一次实际 Windows 候选使用原临时文件和双进程 OS/SQL/签名/IPC，native 决策为明确受控输入。
测试启动前保存候选三处源码摘要；结束恢复 production 默认关闭。
结果、原 command 次数/open 次数与清理记录在本阶段验收报告中单独记录。
不点击真人窗口，不读用户材料，不调用新模型；unknown 不重发。

实际结果：87.92 秒后失败，`invocation_interrupted`；原 command 1 次、open 0 次，
结果 unresolved/unknown，未重发。4 临时凭据缺失、2 角色 key 撤销、child 退出和 proof pipe 关闭
均已核对。默认关闭已恢复后 18 项批读/同权威测量回归通过。
相同受控 snapshot 的 SELECT 为原 42、冷批读 29、已学标识的新鲜批读 24；
单次耗时 0.231/0.226/0.218 秒，只是组件样本，不说明生产性能提升。

子进程原 `runner_current` 在取消前已耗时 6.37 秒；实际 pipe 等待到原约 10 秒上限。
session 检查累计 145 次、约 23.14 秒，覆盖握手/根 callback/读取等多个阶段，
各阶段存在重叠，不能相加当净耗时。SQL 标识批读不足以解决首次原响应预算。
后续重点是 A 当前来源与 D 执行/等待边界的消费策略，不继续把新的 SELECT 样本当整链完成。
92 个不同本阶段节点通过；历史组件并集 250，历史节点并非都在本版重跑。
完整验收记录：`docs/implementation/evidence/ms-i2l-a12.json`。
