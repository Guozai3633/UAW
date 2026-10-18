# H02-I04 / A16 内部审阅等待接口

本轮全部由 A 实施，无 worker 开工或同步要求。最终冻结源码/部署版本见 DISPATCH 与 `h02-i04-a16.json`；不根据本页推断产品整轮通过。

## 装配

```python
clocks = ExecutionClocks(
    records,
    effects=RunIdleEffects(),
    reviews=ReviewWaitSources(records),
)
driver = BackgroundAgent(
    container,
    conversation_clocks=clocks,
    conversation_segments=ExecutionSegments(records),
)
```

records 必须是原 Run 数据库，effects 必须清点原模型、工具与预算账本。只注入 clocks 而缺 reviews 时，artifact Item 暂停明确不可用。普通旧调用仍使用原严格 deadline。文件完成控制器也必须传入同一 clocks；这不是本机权限或完整文件链验收。

## 输入、输出及约束

| 内部入口 | 输入 | 输出 | 约束 |
| --- | --- | --- | --- |
| `ReviewWaitClockPort.check` | 原 RecordTransaction、Principal、run_id、稳定 item_ref、opened | `None` | 返回非 None 拒绝。opened=True 要求当前完整、核验成功、尚未决定的本人审阅；False 只证明原等待的不可变历史来源。无 commit、无权限授予。 |
| `ReviewWaitSources.read` | 同上；current、undecided | CompletionBundle 原 payload | 逐个核对 Item/Bundle/Contract/Report/Proposal/Artifact 的 schema、版本、摘要及同用户完整会话。current=True 另查当前 Run/input/frame、idle 和原 Agent。 |
| `ReviewWaitSources.paused` | 原 TrustedExecutionContext、Bundle；可选同域 tx | bool | False 表示没有实际审阅暂停；来源损坏、旧版本或 unknown 抛出错误。检查初始 clock limit、当前 clock/binding、真实等待 Item，不能仅依赖 waiting 字符串。 |
| `BackgroundAgent.park_review` | actor、原 Run、proposal_ref、持租约 job | 已提交 blocked/delivery job 或 None | 时钟与 job 同事务。无需本人接受/核验未通过时不暂停；已保存决定时跳过停放，避免预览与接受竞态。 |
| `BackgroundAgent.resume_review` | 原 Principal、run_id | bool | 仅持久 accept 回执唤醒原 delivery；重查当前身份、政策、角色和来源，不 mint 执行段、不调用模型/工具。 |
| `RegisteredAgentSources.review_current` | 原 ctx | AgentView | 供当前完整暂停的接受/完成只读复查；不检查已结束执行段的墙钟期限，但仍检查身份、政策、取消、模型/角色、输入和来源。不是可执行的权限快照。 |
| `RunJobs.wake(resume_delivery=True)` | 原 tx/job | 新 job payload | 只接受原 delivery/proposal，不能同时传 continuation_context。保留原 step_context/frame/proposal，增加原 fence，遵守队列容量。 |

公开 HTTP 请求/响应、RunExecutionClock 和 Ref 对象结构保持；`waiting_item_ref` 复用原 `item` Ref，当前指向真实 artifact InteractionItem。Run 仍可为 running，用户阶段由 `/presentation` 的 awaiting_acceptance 表达，不篡改原成果提案固定的 Run 修订。

## 持久状态与恢复

- 停放：job `stage=delivery,state=blocked`；clock `mode=waiting_for_user`，waiting_item_ref 为稳定成果 Item。
- 接受：HTTP 持久保存原 CompletionAcceptance，再通知有界扫描。扫描检查原 proposal ID 对应 accept，重建进程也可恢复。原 delivery 完成后 clock stopped；模型调用数不增加。
- 纠正：沿原输入追加协议；旧提案失效，原时钟结算等待，再由 ExecutionSegments 根据剩余主动额度生成新段。不能修改旧 ctx 或已发调用 deadline。
- 取消：原取消与完成共用 conversation 锁，旧成果不能提交，等待结算并停止。原报告和费用留存。
- 锁顺序：conversation → web.queue；完成内的等待读取加入现有事务，避免重新获取同一 advisory lock。

## 主要拒绝条件

`review_wait_source_changed`/`review_wait_clock_changed`：来源或原时钟不匹配；`review_wait_stale`：Run/input/frame/接受包已变化；`review_wait_incomplete`：没有成功且需本人审阅的完整交付；`conversation_effect_pending`：调用或可执行预留未结；原身份、权限、取消、超额错误继续按原分类返回。unknown 必须对账，不能自动重发。

## 目录与验证

实现、状态链与边界见 [A16](../../../implementation/MS-I2m-A16.md)。定向 SQL 在 `tests/integration/agent/test_review_wait.py`，回归原 owned_clock_continuation/completion/presentation/run_clock。新功能使用固定用户模型；子 Agent、DAG、本机写入、安装与 exec 未开启。
