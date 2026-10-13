# H01-I01：B 页面等待文案与补充入口修复请求

2026-10-13，来源为本人H01真实截图反馈：“貌似没有出结果，然后还让确认什么状态”。
具体问题已由A原数据库/模型决定证实；这不是新大包或整个项目完成声明。

## 已确认事实与A修复

- 用户在H01提出概念比较，固定模型成功返回`action=wait`和具体补充问题。
- 原后台只保存/显示waiting状态，漏了原决定中的text；没有审批动作，没有可接受成果。
- 原FrameRepository已经保存任务理解，后台又生成一份，页面重复两个“任务理解”。
- 用户随后本人停止，原Run已经cancelled；不重发、不复活、不改写原失败或费用。
- A仅修复`src/uaw/run/background.py`：wait/blocked从原已完成operation和Model owning Reader复核text，
  原问题Item与Run waiting在同conversation事务提交；取消/版本/来源/期限拒绝；重复恢复一个Item、零新调用。
  仅保留FrameRepository原理解Item，删除后台重复生成。A源码和SQL回执完成后另发准确source标签。

## B具体允许范围

只改原B所属`apps/web/`、B测试、B handoff及B请求说明；不改公共schema/ports/contracts/锁或A/C/D源码。
继续原`dev/context`，不合浮动integration。开工源码由A准确发布后给出，不据本页草稿猜SHA。

1. `waiting_for_user`默认改为中性“任务等待处理”或同等清楚文案，不能统一叫“等待你确认”。
   实际ApprovalRequest可以沿原审批卡说明“仅批准本次/拒绝”；实际DeliveryView按原成果合同审阅/接受。
   没有这些来源时不得假造审批卡、成果、完成或确认按钮。
2. 原`agent_message`完整显示原补充问题或限制，保留Ref/版本。不得通过词典解析模型文本决定权限或业务动作。
3. 输入被原请求recovery限制时解释真实原因，保留用户草稿，不让用户猜是否卡死。
   当前A尚未支持原Run内steer/澄清恢复。可提供明确手动指引：先停止原任务、读到实际cancelled终态，再用原问题和补充重新提交。
   不称“已继续原Run”，不自动取消/重新提交/合并或替用户补充模型猜测；未知控制仍先读原状态。
4. 把waiting状态、没有Approval/Artifact的补充消息、审批等待、成果等待、空文本/缺源、草稿保留与实际cancelled后可发送纳入定向回归。
   页面刷新只GET，不因为等待或恢复自动发送新请求。

## 交付与验收

阶段源码SHA、仅本页规定路径、精确dist三文件hash、冻结依赖/类型/受控单元与浏览器回执，原失败保留。
真实页面只读联调用A提供的精确页面/原会话上下文，不操作本人旧任务或代点审批/接受/native。
A合入后再固定H01新版本；原H01-v1源码与回执不热改，不把受控browser通过当本人满意。
完整原Run澄清/steer后续需单独闭合输入版本、模型调用、取消和成本协议，不在本定向UI请求中自定。

**状态：待A准确source发布及用户授权直接发送给现有B。当前不算正式派发，不自动同步或扩包。**

## 正式开工来源与授权

用户2026-10-13明确答复“允许直接发给B”。
固定源码ms-i2l-a30-source / ad11ce70c50684ef304b4c137f7ea52eecb5f4ae。fetch后核对远端准确标签；
本source内原“待发布/待授权”段落仅为准备历史，最新origin/integration:docs/coordination/DISPATCH.md的A30正式派发为准。
不合浮动integration；先核对自己当前实际B工作区/分支并保留原提交及handoff。
A已验证6不同SQL节点（1完整受控持久Model队列＋5受控读取故障边界）；A后续证据与B工作并行。
InteractionItem/Run现有schema不变；模型补充问题使用agent_message，resource_refs保持3个原来源。
当前H01-v1仍固定旧快照，B真实只读联调须等待A提供新固定入口/原会话上下文。
