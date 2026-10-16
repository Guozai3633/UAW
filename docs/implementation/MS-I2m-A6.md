# MS-I2m A6：剩余主动执行段与原期限隔离

2026-10-16，Session A / integration，继续原 M2。准确源码与固定标签见 DISPATCH。本段验证 A 的新调用来源和消费，真实 D 计时组件尚未交付；测试使用实际 PostgreSQL、原 Gateway 受控 HTTP 和明确受控服务时间。

## 1. 本段解决什么

此前即使时钟显示仍有主动额度，预算、权限、上下文和消息提交仍会因为原墙钟到期而拒绝。A6 新增内部 `InternalRunActiveSegment`，保存原 blocked 作业版本与摘要、实际 active clock 版本与摘要、原预算摘要、原账本 deadline、输入版本及新上下文。

```text
同 Run 的原补充已受理
  → 当前完整身份、固定模型、原角色和完整权限链重新观察
  → 原会话事务：问题已关闭、真实库存 idle、原作业/容量/fence 检查
  → 注入 D clock 的实际 active CAS
  → 新调用 deadline = 此次 captured_at + (原 active_limit_ms - 已耗 active_elapsed_ms)
  → 保存新执行段与新作业上下文，再唤醒原 Run
  → 预算/权限/上下文/新调用/消息或正式成果消费同一实际来源
```

执行段、clock、Run、队列与事件一起提交，失败一起回滚。新上下文只调整新调用的执行期限，主体、scope、固定模型和能力政策不变。旧作业版本、旧上下文、旧调用和原账本全部保留。

## 2. 来源复核与普通路径

普通调用仍在原有效时间内时，沿用原期限检查，不增加执行段查询。需要跨过原墙钟时才读取执行段及当前 binding/clock，并复核原作业、clock 的历史版本和摘要。

当前上下文必须与执行段的完整主体、作用域、模型及能力政策一致，deadline 必须恰好等于记录中的派生值；不能多给一秒。原预算摘要与原账本 deadline 必须保持，实际 active_limit 还要与首次准入 clock 的原上限一致。时钟停止、额度耗尽、版本变化、归属变化或取消均拒绝。缺记录的旧协议继续按原截止时间失败，不生成补充授权。

`inspect_for_continuation()` 只观察当前身份/Run 状态/完整政策链，并丢弃权限快照返回值；它没有执行授权作用。原 `resolve()` 继续强制检查有效执行段。原预算和模型发送入口仍各自核对取消、费用、能力与当前配置，unknown 仍需对账。

## 3. 预算、租约与交付

- 新预算预留和 dispatch 使用当前有效执行段，但原资源总额、used/held、原 ledger.deadline 均不改写。旧预留的原 attempt/deadline 继续生效，不能用新段重新发送。
- 新执行租约以当前段为上限。过期旧上下文不能撤销另一个仍有效的新根租约；已过期的旧 lease 不能续回，只能在实际 CAS 下创建更高 fence 的新 lease，旧历史版本保留。
- 原 Context、TaskFrame 输入及 Agent 的剩余 Budget 使用相同期限来源。普通消息仍按当前版本提交；文本成果仍有实际 Artifact、逐项报告和独立用户接受。
- **Tool dispatch 尚未完成跨原墙钟接线。** ToolLedger 仍检查原 RootBudgetLedger.deadline，因此会保守拒绝超期动作。A 未改 worker 的 Tool 源码，也未开放 native/安装/写入/exec；详见 [待审接线提案](../coordination/requests/A/MS-I2m-A6-tool-timing-proposal.md)。

## 4. 模块与目录

| 文件 | 本段职责 |
| --- | --- |
| `contracts/conversation_catalog.py` | 唯一新增的内部执行段结构，不改变原 1403 个 schema |
| `src/uaw/run/execution_segments.py` | 新段签发、历史来源验证、实际有效期限及根租约界限 |
| `src/uaw/run/conversation_resume.py` | 原事务中消费实际 active clock，签发并保存新段 |
| `src/uaw/run/jobs.py` | 同一 wake CAS 保存新上下文、保留旧版本与 fence |
| `src/uaw/run/background.py` | 显式注入、续跑前来源观察与运行期实际检查 |
| `src/uaw/composition.py` | 启动前可选组件装配，默认关闭新段签发 |
| `src/uaw/run/permissions.py` | 当前权限链观察与实际执行授权分开 |
| `src/uaw/run/budget.py`、`leases.py` | 新动作额度和 lease 消费原段，保留旧期限 |
| `src/uaw/run/context.py`、`inputs.py` | 原材料/补充读取的同源时间检查 |
| `src/uaw/run/conversation_entry.py` | 当前消息提交前的同事务来源检查 |
| `src/uaw/agent/sources.py` | 当前有效剩余 Budget 的期限，不复制旧完整时限 |
| `tests/integration/agent/test_execution_segments.py` | 受控时间跨原 deadline 的实际 SQL/队列/模型/成果验证 |

## 5. 验证边界

最终 **83 个不同真实 SQL 节点＋56 个契约单元，共 139 项通过**。原对话批次 51 项中 50 通过、1 项失败；另 32 项权限/租约/预算通过，失败的同一租约节点定向修复复跑通过，不重复计数。14 个新执行段节点、12 个原续跑、16 个后台恢复、9 个原对话均有对应回执。230 源码类型、13 变动源码/测试文件 Ruff/格式通过；1404 正例和 336 反例通过，原 1403 结构逐项不变。历史 675 和旧阶段不计本轮全仓。

精确用例、命令、源码摘要、最终节点、初次失败与复跑见 [机器回执](evidence/ms-i2m-a6.json)。初次未来时间夹具只前移 Agent 时间，队列仍停在真实时间，导致作业未 ready；随后统一受控队列时间，保留初次失败回执。租约续接同时验证旧过期上下文不能误撤销新有效 lease。

这些测试不计为 D 真实耗时计量、不计为实际长时间等待或固定 DeepSeek 的质量验收；成果接受使用随机测试主体的真实接受接口，不是本人 H02 接受。没有实际模型新调用或新费用，不覆盖旧失败、pending 费用或 last_full。

## 6. 当前尚未开放

`Container.conversation_segments` 默认 `None`，D 真实 clock 尚未合入；现有 H01-v5 未替换。真实 clock 装配、Tool 时间 port、独立新服务与 B 真实页面、C 实际质量样本、固定用户模型和 H02 本人体验仍分别待验。本机首次签名文件链继续保持独立未完成状态。

初次整组回归另发现旧 lease 测试使用了过期前的修订做新 acquire。原 `renew` 会先通过 `current` 把观察到的过期状态持久化，修订从 1 变 2，再拒绝续期。测试现在明确断言过期状态、原到期时间和 fence 保持，再以实际修订 2 创建新的 fence；历史版本 1 保留。定向失败、诊断和修复回执全部保留，未放宽期限或 CAS。
