# H02-I03：主界面、任务理解与成果状态统一

2026-10-18。本人两张截图，会话`conversation-6702653d5e0a45159a1eee55d171ab2f`，原Run `run-169ef7763d694cc297c00b51dea9e6b4`。本单是具体修复范围；未收到A正式消息前不视为新包已派发。

## 实际证据

原Run running/v5，原job为delivery/waiting，报告及核验已持久化，无新增模型正在执行，实际等待本人审阅。为了保留已签定的proposal.run_ref，后端没有把Run推进新修订；前端仅按Run.status显示“努力奔跑中”。模型同次返回了真实understanding，但该对象只保存在FirstDecisionRecord，未接到页面的TaskFrame/理解项。不能把这次理解缺失说成模型尚未完成，更不能补一次模型调用制造理解。

## 固定责任

- A：新增只读`GET /v1/runs/{run_id}/presentation`，0.2协议，生成`RunPresentationView`。在同一owned会话读事务中组合原Run/input_revision、实际activity、可选理解及当前成果引用；原Run/CAS/Frame/Proposal/接受不改写。字段及准确可消费源码由A后续固定阶段给出。
- B：仅改原允许`apps/web/`、B请求/交接/回执目录。消费A生成DTO，不能用消息文字、时间或成果存在性猜完成；不改A/backend/公共schema源/锁/flags。不合浮动integration，不操作本人授权或接受。

## 目标行为

1. 原同Run、当前input_revision、proposal.run_ref与Run.revision一致且实际处于等待接受时，主状态显示“成果已就绪，等待你审阅”，显式提供“查看成果”。仍允许继续修改、停止或本人接受；不能显示完成，也不能自动解除原请求限制。
2. 用户已接受、后台尚在收尾时显示收尾；只有权威Run.completed才显示完成。旧成果/stale、不同Run/账号/新输入不得覆盖当前状态或启用接受。
3. 理解来自A实际模型记录的`understanding`投影，不把复制原文的TaskFrame当独立语义理解。有值显示摘要/假设；模型已结束而未给理解时隐藏等待或显示“按你的原文执行，本次未单独提供理解摘要”；真正首调用尚未返回才可显示等待。
4. 工作区、ConversationPanel与Review不独立保留相互矛盾的显示状态。接到更新用同一账号/conversation/run/input/Run修订核对；迟到的旧响应不回退；读取中显示为后台更新，保留最后一次已核对值，不用全屏loading暗示任务仍未产生结果。
5. B在宽屏/1050px成果抽屉、刷新、接受响应丢失、补充生效、取消/终态、身份切换及缺A来源场景做定向验证。缺来源明确不可用；不猜成功或自动重发。

## 原始边界

不替本人点击接受、停止、目录授权或提交问题，不改原失败/成果/费用。只读观察原Page可用；新诊断使用明确测试主体。组件通过、实际页面、事实质量和本人满意分开记录。

交阶段/最终源码与独立handoff、实际dist/hash、去重验证回执及A接线要求。A收到阶段即审阅，不等待其它worker；本单不扩大C/D范围。
