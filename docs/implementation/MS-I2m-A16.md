# A16：成果审阅等待暂停主动执行计时

2026-10-18，H02-I04。本人明确要求本轮全部由 A 完成；不向 B/C/D 派包，不移动其分支。

## 原因与行为

原报告生成、核验结束后，后台仍按原执行期限反复尝试完成。等待本人审阅因而被算进执行时间，最后出现报告仍在、Run 已超时的情况。

新任务生成完整且核验成功、合同要求本人接受的成果后，后台把稳定成果 Item 登记为等待来源，并在同一事务暂停主动时钟、停放 delivery job。等待只增加 wait_elapsed_ms；接受后校验原成果并收尾，不调用模型；纠正后才按剩余主动额度继续执行。原 Run 修订、报告和旧命令 deadline 不为等待改写。

## 模块、目录与链路

| 边界 | 文件 | 实现策略 |
| --- | --- | --- |
| 真实等待来源 | `src/uaw/run/review_wait.py` | 同一用户完整会话、Run/input/frame、稳定 artifact Item、Bundle/Contract/Report/Proposal/Artifact 逐个核对；核验必须成功、需本人接受、无未结模型/Tool/可执行预留及取消/超额。历史等待与当前可接受证明分开。 |
| 持久时钟 | `src/uaw/run/clock_ports.py`、`execution_clock.py` | 可选 ReviewWaitClockPort；无来源拒绝 artifact 暂停。旧澄清 question 保留。原 CAS、limit、效果清点及等待后复查不变，不新增公开 clock mode。 |
| 停放与唤醒 | `src/uaw/run/background.py`、`jobs.py`、`conversation_recovery.py` | conversation→queue 锁顺序；时钟和 blocked/delivery 原子提交。正常领取排除 blocked。接受由持久回执和有界恢复扫描唤醒 delivery；纠正走原输入修订/ExecutionSegment；取消走原终态控制。进程重建不依赖内存事件。 |
| 接受与完成 | `src/uaw/run/completion.py`、`agent/completion/delivery.py`、`agent/sources.py`、`agent/adapters.py` | 只有真实暂停证明才能使用只读 review_current 校验；仍检查当前身份、权限、模型/角色、来源、原版本及取消。该读取不能授权模型或工具执行。接受和最终提交在原 conversation 事务内再次复查。 |
| HTTP 与显示 | `src/uaw/api/routes.py`、`run/presentation.py` | 接受先持久化，再通知扫描。blocked/delivery 只有真实等待证据才显示 awaiting_acceptance。B 已交付页面消费原投影，无前端源码改动。 |
| 装配与诊断 | `src/uaw/run/file_runtime.py`、`ops/registered_report_probe.py` | 文件完成控制器传入原时钟；诊断明确注入实际 ReviewWaitSources。文件权限/本机有效期不因审阅暂停而延长。完整本机验收另列。 |

### 状态链

`生成与核验 → 稳定成果 Item → 同事务暂停时钟 + blocked/delivery → 等待本人`

- 接受：保存精确 Bundle/Artifact 决定 → 有界扫描 → 原 delivery 收尾 → completed / stopped；不续领执行段、不重新生成。
- 纠正：原输入补充 → 旧提案失效 → 结算等待 → 剩余额度的新执行段 → 新成果；旧正文留存。
- 取消：原取消事务 → 禁止接受/完成 → 结算等待并 stopped；不删除报告。
- 预览刚出现即被接受：在同一锁下看到已保存决定则跳过停放，正常收尾；不将“已有决定”变成执行失败。

## 约束与兼容

不新增 HTTP/schema 对象，不修改 flags、用户固定模型、提示词、依赖锁或旧在途 deadline。普通聊天仍走原快通路。未注入时钟的旧组件维持原严格期限行为，不凭字符串 waiting 跳过超时。只有当前可证明的完整审阅等待能跳过执行时间检查；授权、审批、设备目录或身份失效仍须拒绝。

原 H02 失败 Run `run-169ef7763d694cc297c00b51dea9e6b4` 保持 failed/v6，旧 v5 报告只读。本修复针对新任务，不复活旧任务，不代本人确认或接受。

## 验证与发布

定向 SQL 覆盖长等待、重建恢复、接受幂等、纠正继续、取消、权限撤销、unknown、缺等待来源和预览/接受竞态，并回归原澄清时钟及完成/显示。控制时间与受控模型回执不能代替实际墙钟或模型质量；真实模型诊断与部署结果在 `evidence/h02-i04-a16.json` 单独记录。

最终版本固定为 `d2000f958dc8f5652a38fbf18f4e6af15020166a`，H02-v7 已部署；实际普通对话、澄清、工作报告跨进程/原期限纠正和接受、取消及学术材料报告通过。18次真实诊断含脚本失败和旧误分流全部保留，未知费用 pending。准确回归、来源及部署以 `evidence/h02-i04-a16.json` 与 H02-I04 为准。不更新 last_full，不把本修复当 H02 整轮或事实质量已接受。

### 真实联测发现的简短报告分流问题

固定 A16 `50c3bdd5d0aeb14554bd29f7a7168a01dc0ea37d` 的真实报告跨原期限接受已通过；另一个约200字工作周报样例却选择 reply，直接消息完成，无法继续审阅纠正。普通回答及同 Run 澄清答复已实际通过。另有诊断脚本误读 ClarificationView 的失败，分别保留，不能混成产品模型失败。

补充源码仅在 `src/uaw/resources/prompts/conversation-v1.txt` 明确按请求结果选择动作：简短报告和原成果修订仍用 deliver；询问如何写报告仍可 reply。不增加关键词路由、额外分类调用或自动重试，不改变原模型输出记录。原题在新固定快照中已实际进入成果审阅并完成纠正；普通问答仍1调用，澄清/答复仍2调用。这是有限样例的行为验证，不宣称全任务分流准确率。
