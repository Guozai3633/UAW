# MS-I2m M1：原Run控制读取、受理与真实空闲库存

2026-10-16，A / integration，从固定`ms-i2m-start`与自己发布HEAD继续。准确阶段SHA以DISPATCH阶段回执为准。

## 1. 实现和消费

- `ConversationControls(records)`统一入口：view/question/answer/correct/lookup，五个既定0.2 HTTP已装配到候选源码。沿用真实浏览器精确Origin、CSRF、退出失效与CLI bearer，OpenAPI区分旧RequestMeta和新ConversationRequestMeta。
- `RunIdleEffects().check(tx,actor,run_id)`为D ClockIdlePort的实际来源：检查所属会话/Run、根账本、全部该Run model.invocations、实际派发tool.contexts/dispatch.intents/effects以及逐项budget.accounting/reservations。未知/未完效果和可执行预留不能暂停；已知调用费用pending照实保留，不冒充最终账单。
- `conversation_entry.settled_effects`转用同一个实际Reader，原消息发布前的其他核验与授权调用全部保留。

```python
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.conversation_control import ConversationControls

controls = ConversationControls(records)
view = await controls.view(authenticated_user, original_run_id)
# D在自己的构造入口注入RunIdleEffects()，A负责最后装配。
# change仍加入同一个原Run事务，Reader不新建权限或时限。
```

固定URL与字段见[MS-I2m接口](../coordination/requests/A/MS-I2m-AD-contract.md)。HTTP成功返回真实RunContinuationReceipt，patch.state当前仅accepted；**本阶段没有队列唤醒、applied提交、长等待续跑或新浏览器部署**。B可按此源码消费真实handler形状，实际localhost服务在A M2另发，H01-v5旧端口不热改。

## 2. 同域写入和恢复策略

原主体/会话/Run/protocol/input/question/CAS复核后，在同一`conversation:<id>`事务内追加逐字InputRecord及user_message、RunInputPatch、输入集合新版本、协议输入版本、问题answered或stale、Run/Task当前frame指针失效与持久事件。原Input/Model/TaskFrame/成果内容和旧引用保留，不创建第二Run或Task，不覆盖原文。

请求键从owner/run/request_id派生固定有界哈希，原request_id保留。相同键/相同内容及预期版本复用原受理，返回**当前**patch与Run（含后来取消）；不同内容409。旧问题/输入412或Run CAS409；原控制等待中取消会使accepted补充及open问题失效，不能再续起。终态与旧协议只读兼容，旧Run新控制明确503。

最多16条补充、原输入集合UTF8总量64KiB；当前附件摄取未装配时明确503，不丢弃附件。新HTTP限制body总量，路径ID禁止重复塞payload，0.2与旧0.1解析独立。accepted不声明新模型已经消费，运行中纠正的完整安全边界由M2另验。

## 3. 验证与尚未接受范围

精确测试/失败/修复/静态回执在本轮机器记录与原JUnit中记录；不把旧P1-13或历史675/1691算本轮全量。SQL使用A55432随机fixture，未操作本人H01数据或B/C/D数据库。

首轮发现RecordTransaction.write会更新已加载ORM行修订，导致后续binding错误多增一次输入版本；已改为冻结base_input_revision再写。首轮5失败/3通过保留。第二轮7通过/1失败来自测试fixture已有另外一个Model Run，已改为对比前后真实ID集合来验证零新Run，未修改实现绕过检查；第二轮原回执保留。

独立发布门槛：实际Run问答/纠正执行、D时钟与剩余主动段、真实固定模型、B实际页面、C事实评测、单Agent文本成果及本人体验仍待M2–M4。本机原签名文件首次链仍独立未通过。新运行时子Agent/DAG/本机写入安装exec保持关闭；本轮没有真实LLM新请求或新增费用。

后续汇合20个不同SQL节点首跑19通过/1用例准备失败：测试用65536个ASCII字符触发了单条Text 16384字符合同，尚未进入64KiB合计检查。改用合同内16384个四字节字符，真实覆盖UTF8合计越界；不放宽原Text或64KiB限制。原失败XML保留。

最终新增11个SQL节点复跑全部通过；与之前最终通过的9个P1-13兼容节点合计20个不同节点，原19/1失败批次不改写。54个对象/动作契约用例通过。契约checker在SQL尚未落XML时曾返回5个证据路径缺失，原回执另存ms-i2m-m1-first-contract-check.json；等待实际JUnit后再做最终checker，不创建占位证据。
