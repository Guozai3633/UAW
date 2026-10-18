# H02-I04：真实成果审阅等待的持久计时范围（由 A 实施）

2026-10-18。原准备给 D 的具体范围。本人随后明确要求“本轮全部由 A 完成”，因此本单未派发，时钟及后台接线均由 A 在 integration 实施；D 原分支、提交和停止点不变。以下保留实现约束，最终验证见 H02-I04 及 A16 回执。

## 原问题与选择

真实报告已生成并核验，等待本人接受仍计入主动执行，导致原Run以background_deadline_expired失败。扩展现有waiting_for_user语义，使用真实artifact InteractionItem作为稳定waiting_item_ref，不伪造ClarificationQuestion、不新增公开clock mode或续领预算。

## A固定的内部端口

在 `src/uaw/run/clock_ports.py` 新增可选注入的 `ReviewWaitClockPort`：

```python
async def check(self, tx: RecordTransaction, actor: Principal,
                run_id: str, item_ref: Ref, *, opened: bool) -> None: ...
```

`opened=True` 必须证明：原稳定artifact Item和当前完整Bundle/Contract/Report/Proposal/Artifact绑定同用户完整会话、Run及有效输入/frame；核验succeeded、合同需本人接受、尚无接受决定；无未结模型/工具/预留、无取消/超额。A提供实际 `ReviewWaitSources`，无新权限、无commit，不把空refs当idle。

`opened=False` 仅核对原持久审阅等待来源及稳定Item/不可变原交付的历史身份/pin，允许当前Run已经纠正/取消/完成，供时钟结算/停止；不能以此证明当前仍可接受或执行。当前权限另由A消费方复查。历史等待证据损坏必须拒绝。

## 时钟实现范围（本轮 A 获授权）

- 仅 `src/uaw/run/execution_clock.py`、原run_clock单元/SQL、D请求/handoff/回执允许目录。
- 构造器可选 `reviews: ReviewWaitClockPort | None = None`，旧消费者保持；没有实际reviews时，artifact Item不能获得暂停。
- 原question路径完全保留。waiting_item_ref指向真实artifact Item时，调用reviews.check；opened时仍必须执行实际effects.check、等待后重读原clock/binding/ledger/Run并再次核对来源；返回非None拒绝。
- measure保持waiting_for_user计入wait_elapsed、不增加active_elapsed。时钟CAS/绑定同事务、原limit不变、stopped不可恢复；active/stopped转换能结算原审阅等待。取消后仅可stopped，unknown不能免费暂停。
- 不改A schema/ports/恢复/后台源码，不延长旧ctx/授权期限，不操作本人Run或真实确认/接受。

## 必要验证与交接

真实SQL覆盖审阅Item+实际A来源注入（或明确受控port单独报告）、跨原墙钟等待、重建实例后active_elapsed不增、wait_elapsed正确；无来源/错主体/错误Item或提案/已有决定/未结效果/取消/预算超额拒绝；等待中取消/终态stop和旧问题回归，CAS竞态无部分写。原失败全部保留，交阶段源码/最终独立handoff与实际去重回执，A负责完整后台/HTTP/真实模型联测。

交付后停止，不同步其他worker、不改flags/锁、不把组件通过标H02整轮通过。
