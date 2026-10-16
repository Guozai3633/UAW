# MS-I2m A4：原队列唤醒与同 Run 接续的 A 侧装配

2026-10-16，Session A / integration。继续原 M2；准确固定 SHA/标签以 DISPATCH 为准。没有扩大 B/C/D 分工。

## 1. 当前范围

新增 `ConversationResumer`，用实际原作业、完整用户会话、原 Run/Task/Agent、当前固定模型/政策/角色与追加输入决定能否唤醒。只恢复仍在原期限内的任务；超过原墙钟期限时拒绝，长等待需要下一阶段可信执行段。没有更改原调用、审批、root 或 native 的期限。

当前默认没有 D 的真实时钟。缺失 `ConversationClockPort` 明确不可用，不修改作业、Run 或已受理输入。HTTP 仍为既有受理入口，本段没有自动调用新的恢复器，也没有部署新的 localhost 服务；不能把组件通过当作用户已经能完整续跑。

## 2. 准入和事务链路

```text
原作业中的完整用户/Context
  → 当前认证、固定模型、政策、角色绑定复查
  → 原 conversation 事务锁
  → 原 Run/输入版本 + 确实比原作业更新的 accepted 输入
  → 原问题已关闭 + 实际 Model/Tool/预算库存已结清
  → 原期限仍有效
  → Run preparing + 注入的 owning clock 变 active
  → 复查实际 clock/限额/修订/binding 与原 Run 未被改写
  → 同事务队列容量与 fence 更新
  → 等待后再次复查认证/固定模型/政策/角色
  → 持久 run.updated + 一次提交
```

此处的 `running → preparing` 仅用于新对话协议内、已有较新 accepted 输入的安全重新准备，不放宽旧 `RunFacade.advance` 的通用状态规则。终态、取消、开放问题、缺来源、未知效果和不一致版本不能恢复。

持锁顺序与原提交一致：原会话锁在先、队列锁在后。两个页面同时恢复只有一个改变作业；已恢复或状态已变返回未再次唤醒。时钟/Run/作业/事件任何一步失败全部回滚；不同用户会话不能接管原 Context。

## 3. 队列与 Agent

`RunJobs.wake(tx, original_job)` 只参加原事务，不另开事务。它检查当前 blocked 作业、容量和原完整字段，增加 fence，清除当前旧租约/旧 frame/旧 step_context/旧 proposal，使作业回到 prepared。原作业版本保留旧失败与引用，原 ModelInvocation/Output/费用不改。

`BackgroundAgent` 按新输入生成 TaskFrame/Context。复用原角色和根实例，重新读取有效绑定，不重复创建权限。原活跃操作只经既有 `discard_stale_unsent` 严格判断后失效；未结模型或 Tool 意图仍要求对账。下一调用编号取原作业/根实例已用步数之后，不复用原 attempt。

恢复到 running 的幂等键加入真实新 frame 版本。首轮回归发现复用旧幂等键会把合法恢复挡在 started，本段已修复；原初次 frame=1 的键保持。

## 4. 发布与时钟引用

`publish(..., clocks=...)` 在原消息/问题事务中消费注入的 owning clock：先写原 Run 状态，再调用 change，核对实际返回和当前 row、限额、修订、binding.clock_ref 以及原 Run 没被时钟组件修改。没有注入时，保留原部署兼容路径。

原兼容路径修复两处 ORM 引用计数：事务写入会原地增加 RecordRow.revision，必须冻结原 revision 再生成 clock_ref 和 run.updated 的 base/result。新写入不再出现 clock_ref 比实际 clock 多 1 的情况。既有本人服务/记录未热改或迁移；历史异常也不伪造为已修复。

## 5. 模块和目录

| 文件 | 职责 |
| --- | --- |
| `src/uaw/run/conversation_resume.py` | A 的完整准入与同事务恢复控制器 |
| `src/uaw/run/jobs.py` | 原队列容量、作业 CAS、旧 worker fence 隔离 |
| `src/uaw/run/background.py` | 来源复查、角色/Agent 复用、单调新 attempt、发布装配 |
| `src/uaw/run/conversation_entry.py` | 注入时钟的同事务消费与旧引用修订修复 |
| `tests/integration/agent/test_conversation_resume.py` | 实际 A SQL/库存/受控模型；明确受控的 clock seam |

## 6. 验证语义

精确逐节点结果、失败和源码摘要见 [回执](evidence/ms-i2m-a4.json)。测试使用随机开发用户和 A 开发库；模型为原 Gateway 的受控 HTTP 返回。clock seam 故意只提供字段状态，**不实现或证明 D 的计时、崩溃恢复、主动耗时和长期等待**。

最终 **28 个不同 SQL 节点通过，0 失败/错误/跳过**＝12 个新增＋4 个应用证据＋3 个纠正失败隔离＋9 个原对话节点；原首次 9 节点中的 2 个失败和定向复跑 2 节点均保留，不叠加计数。227 源码类型检查、5 文件 Ruff/格式通过；公共契约、A/D port 和依赖锁原字节不变。本段未增加独立单元批次，也不叠加 A3 的 81 或历史全量。

两条目标链路：回答澄清后同 Run 继续、运行中纠正后安全失效旧操作并继续。另验并发恢复/旧 worker/队列重建、unknown 不重发、缺时钟、事务失败、容量、等待后身份撤销、取消、新会话拒绝、原期限不续期及不一致组件返回拒绝。原聊天/工具审批/成果接受/权限撤销按受影响范围回归，不作为全仓新全量。

下一步仍是原 M2：收到 D 实际阶段后审阅/接线；构建超出原墙钟的可信剩余主动执行段，接生产恢复入口、后台重启扫描与取消/正式成果终态计时收尾，再给 B 实际新服务。C 真实候选导出、固定模型与正式成果/本人 H02 分别验。原 H01-v5、用户历史、费用、flags、旧标签和 last_full 保留。
