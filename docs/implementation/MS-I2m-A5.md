# MS-I2m A5：后台恢复入口、失败反馈与终态计时消费

2026-10-16，Session A / integration。继续原 M2，未新拆 worker 包。准确阶段 SHA/标签见 DISPATCH；D 的实际 MS-K1 组件尚未交付，以下 SQL 使用明确受控 clock seam。

## 1. 用户提交补充后的链路

```text
原 HTTP 认证、Origin/CSRF、原 Run/问题/输入 CAS
  → ConversationControls 保存不可变原回答/纠正
  → 返回真实 accepted 回执，同时只发后台扫描信号
  → 原队列空闲时扫描有 accepted 补充的 blocked 原作业
  → A4 原身份/固定模型/角色/预算/效果/期限/时钟准入
  → 安全唤醒原 Run
  → 原 Agent 新步骤实际消费输入后提交 applied
```

HTTP 信号不调用模型、不领取预算或新权限，不为每次请求创建后台任务。即使受理后通知代码失败，原回执仍成功返回；进程在保存补充后崩溃、通知丢失，重启扫描也从实际数据库找到它。普通读取、刷新和重复提交不直接执行模型；同一 request_id 仍读当前原回执。

## 2. 有界恢复与未知效果

`ConversationRecovery.scan()` 只读取原账号的实际 Run、blocked 作业和 accepted patch，终态/已取消补充不选中；每次默认最多 8 项，可配 1–16。用原作业中的完整 session，不从输入文本或当前页面重造身份。恢复前后仍由 A4 准入复查，不持有授权缓存。

常规扫描间隔为 2 秒；原请求信号可提示下一轮提前扫描。每个 session/Run/输入版本负向退避从 2 秒增长到最多 30 秒；最多 256 条内存记录、8 个同时在途恢复，每次准入限 15 秒。进程重启不依赖这些内存记录，它们不证明任何授权或已执行状态。

扫描按实际作业 ID 游标轮转，前一个受阻任务不会永久挡住后续任务。unknown 先核对原账本，不重发 Model/Tool；未开始或正在工作的作业不被扫描当成新的任务执行。

## 3. 具体停点与前端反馈

恢复失败保留原 `Failure` 在 `run.continuation.recovery.failures`；正常记录版本保留历史原因。每个 Run/输入版本使用稳定 `user_control` Item，在原会话事务写入可读停点及 `item.updated`，包括待对账、权限变化、额度/期限不足、组件缺失。

同样反馈不重复追加 Item 或事件。恢复后更新原提示为已接续；这不是 applied、完成、核验通过或用户接受。旧输入版本的失败不会更新较新补充的提示；其他 session 不能写原恢复反馈。保存提示本身失败也不删除原 accepted 输入，后续仍可由原库存恢复。

## 4. 取消、失败与正式成果的计时收尾

新增 A 的 `conversation_clock_commit.stop_clock`，由独立 RunTerminationController 和 RunCompletionController 在原终态事务内消费**注入**的 D clock。

- 取消/失败仍先检查原模型、Tool、可执行预留和未知效果。存在 unknown 时保持原非终态，不假装停表已完成。
- 正式成果仍先验证实际成果、逐项报告、当前输入/版本/预算/权限，以及合同要求的本人接受，才能提交 completed 和 stopped。
- 时钟只更新 clock/binding，不准改写 Run、增加限额或丢掉原在途引用；实际返回与当前 row、修订和固定 binding 必须一致。clock 失败时 Run/Task/事件一同回滚。
- 已终态的重入只读原 stopped，重复收尾不重复计时。原等待恢复提示随实际终态关闭，不把未消费补充标成 applied。
- 缺时钟时保留旧部署行为；无新协议的旧文件 Run 不迁移或伪造暂停来源。

## 5. 装配和代码目录

| 位置 | 本段职责 |
| --- | --- |
| `src/uaw/run/conversation_recovery.py` | 实际恢复扫描、退避、并发限制、受阻原因与稳定提示 |
| `src/uaw/run/conversation_clock_commit.py` | 终态事务消费 clock，复核实际结果与 Run 未被改写 |
| `src/uaw/run/jobs.py` | 队列空闲时执行注入的扫描，不另建调度线程 |
| `src/uaw/run/background.py` | 候选实例中组装恢复器与原队列、终态 clock |
| `src/uaw/composition.py` | 显式注入 conversation_clocks，管理恢复入口生命周期 |
| `src/uaw/api/conversation.py` | 原持久受理后只发信号；通知失败不改成提交失败 |
| `src/uaw/api/documentation.py` | 明确受理与可选后台恢复的实际区别 |
| `src/uaw/run/completion.py`、`termination.py` | 正式成果/取消/失败提交和计时收尾同事务 |
| `src/uaw/agent/completion/assembly.py` | 传递既定内部 clock port |
| `tests/integration/agent/test_conversation_recovery_service.py` | 原 HTTP/SQL/队列/库存与显式受控 clock 的验证 |

只有显式注入 conversation_clocks 的新候选实例会安装恢复扫描。**默认没有生产 D clock，因此没有打开实际自动恢复；当前 H01-v5 服务没有替换。** 本段不修改公共 schema、固定 A/D port、依赖锁或 feature flags。

## 6. 验证与未过门槛

最终 **39 个不同真实 SQL 节点全部通过，0 失败/错误/跳过**：16 个恢复服务、12 个安全续跑、9 个原对话、2 个 HTTP/CLI/Cookie 认证兼容。耗时 496.66 秒；原首次 8 项和复跑 12 项不重复相加。12 个变动源码/测试文件 Ruff/格式通过，229 个源码文件严格类型检查通过。没有执行本轮全仓门槛。

精确命令、最终节点、原失败和源码摘要见 [机器回执](evidence/ms-i2m-a5.json)。首次 SQL 中测试把用户真实取消产生的 `user_control` 也算成恢复提示，已按实际稳定 Item ID 区分；原回执保留。另一次验证命令引用错误的历史节点名，收集失败且未执行，后续用核对后的真实节点重跑。一次类型复跑遗漏仓库既定的 `apps/local_runner/uaw_runner` 源码参数，产生 70 个导入及衍生错误；按 `ops/check.ps1` 的原命令补齐参数后，229 个源码文件检查通过。

所有新 SQL 用随机测试用户和 A 开发库；模型是 owning Gateway 的受控 HTTP 返回。没有实际 DeepSeek 新调用/费用，也不证明 D 的真实耗时、长期等待或本人 H02 体验。原失败、pending 费用、本人记录、旧标签及 last_full 保留。

下一步：接收 D 的实际组件/SQL阶段；建立超出原墙钟的可信剩余主动执行段，并逐个接入实际预算/权限/租约/模型/Tool 和成果来源，原已派发调用/审批/root/native 期限保持不变。再启动独立新服务供 B 真实联调、导出 C 的真实质量样本，完成固定用户模型与 H02 本人体验。不能用本段受控时钟结果代替这些门槛。
