# MS-I2m A5：后台恢复与终态计时接线

2026-10-16，固定源码 **24be0944f7c63d650e0fd67800090ebf3d100975** / **ms-i2m-a5-source**。共同开工基线、原 B/MS-U4、C/MS-E1、D/MS-K1 及连续 M1–M4 保持。本段不是新 worker 包。

## 1. A 提供的入口

`Container.conversation_clocks` 是启动前的显式依赖，默认 `None`。在 conversation-v1 实例中注入真实组件后，`Container.start()` 把同一组件传给原 BackgroundAgent，组装一个 `ConversationRecovery`，并把它的 `scan` 接到原队列空闲入口。`Container.close()` 停止原队列并清除恢复器，不为每个 HTTP 请求创建任务。

回答/纠正 HTTP 原持久受理成功后只调用 `signal(actor, run_id)`；返回的 patch 仍是实际当前状态。原队列以数据库中的 accepted patch、blocked job 和原完整用户 session 为来源，经 A4 准入唤醒原 Run。通知丢失、通知代码失败或进程重启，都从原库存找回输入；不会要求用户重发补充。

自动扫描采用默认 8 项有界批次、游标轮转和 2–30 秒负向退避；通知可提示下一轮提前扫描。恢复失败写实际 Failure 和稳定 `user_control` Item；同样原因不重复刷屏。恢复提示结束与 patch.applied 分开，实际模型消费证据仍由 A3 提交。

## 2. D 消费与真实装配前提

固定 `ClockChange`、`ConversationClockPort`、`ClockIdlePort` 的字节没有变化。D 继续原 MS-K1，不需要等 A 新发包；阶段提交及真实 SQL 回执到达后 A 审阅接线。

**下面仅是 D 真实组件合入后的装配示例；当前默认没有该组件，不是当前服务已可运行的声明。**

```python
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.execution_clock import ExecutionClocks  # D 阶段接受并合入后才存在

assert container.records is not None
container.conversation_clocks = ExecutionClocks(
    container.records,
    effects=RunIdleEffects(),
)
await container.start()  # 一次性新候选实例；不重复 prepare 或热改 H01-v5
```

发布普通消息/问题、A4 安全唤醒、取消/失败收尾和正式成果完成使用同一组件。终态控制器先完成原效果、费用、版本及用户接受检查，在原会话事务内写 terminal Run，再调用 `change(..., mode="stopped")`；A 校验实际返回、clock/binding 修订与原 Run 未变。组件失败使 Run/Task/事件一起回滚。存在 unknown 时保持原待核对状态，原调用不重发。

本段仍受**原墙钟期限**约束；长等待后的可信剩余主动执行段及其 Model/Tool/预算/政策/租约来源尚未完成。D 时钟读数本身不构成新执行权限，也不能延长原调用、审批、目录或 native 有效期。

## 3. B/C 消费

B 的五个控制 HTTP、0.2 meta 和公开对象不变。恢复受阻使用原 InteractionItem、`item.updated` 及原回执，不新增让前端猜测的消息字段；页面应重读当前原 Run/问题/continuation。尚未提供本段真实新服务入口，H01-v5 保留，不能用旧服务当本段联调成功。

C 继续原独立评测设施；本段 39 SQL 使用受控 Gateway 输出，不是实际固定 DeepSeek 的质量样本，不应标成人工事实核验。真实候选导出和质量门槛仍待后续接线。

## 4. 回执、同步与剩余门槛

最终 **39 个不同真实 SQL 节点通过**：16 恢复服务＋12 安全续跑＋9 原对话＋2 HTTP/CLI/Cookie 认证兼容，0 失败/错误/跳过；229 源码类型、12 变动文件 Ruff/格式通过。首次测试断言修正、零节点收集错误及类型命令参数遗漏均保留在 [机器回执](../../../implementation/evidence/ms-i2m-a5.json)。[实施目录和策略](../../../implementation/MS-I2m-A5.md)列出完整范围。

受控 clock 仅证明 A 的消费和事务，不证明 D 计量、超长等待、实际新浏览器或本人 H02 通过。没有实际模型新费用；旧失败、pending 费用、flags、原用户记录和 last_full 保留。

需要本阶段源码的 worker 先提交自身阶段并保持干净，自行 fetch 后核对远端 DISPATCH 与准确 tag，普通 merge 固定 `ms-i2m-a5-source`，保留原提交；不合浮动 integration、不 reset/rebase。A 不操作 worker 分支或改其业务源码。
