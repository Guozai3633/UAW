# MS-I2m A2：原任务补充的来源与上下文准备

2026-10-16，A / integration，准确源码在DISPATCH阶段回执。沿原MS-I2m连续开发，未新派worker包。

## 已实现

`conversation_entry.source_frame`按真实输入版本生成下一个TaskFrame修订，旧RecordVersion及原Input不覆盖。每个输入版本有独立幂等键；相同输入已具备完整frame/binding与Run/Task指针时可复用原快照，兼容旧键留下的已完成准备；新增修订的事件base/result精确使用写入前保存的版本。

新增`ConversationQuestions`读取原RunInputPatch、原问题Item/ClarificationQuestion/FirstDecision记录及准确答复InputRef；全量问题/原因/选项进入`clarifications`数据块，避免用户回答“第二个”时模型只有回答、没有原问题。它属于历史任务数据，不升为平台指令。所有来源归属、版本、hash和答复集合在使用前复核，问题改变会使快照拒绝。

普通无补充输入直接返回空问题集，不额外查询问题表，不添加空clarifications字段；保持已有普通回复的ModelPrompt数据形状。仍无需独立理解或自评调用。

## 验证与实际范围

[机器回执](evidence/ms-i2m-a2.json)。4个真实A SQL节点通过，包括3个新来源/输入准备节点和原单调用重启兼容；225源码类型/4文件静态格式通过。原命令用错兼容节点名导致收集失败，未运行测试，其XML保留；修正节点名后四项全部通过。

测试直接构建同Run新输入和ModelPrompt，没有派发第二次真实模型、没有新生产Run执行，也没有将accepted标applied。测试中按原合法状态机把随机fixture切到preparing用于验证来源准备，不冒充生产队列唤醒或长等待。

M1的74个不同节点作为已交付组件回执独立保留，不与本阶段4项相加冒充新源码全仓全量。新普通兼容节点实际再次运行。

## 下一段真实依赖

D的ExecutionClocks/current/change实际组件及SQL回执到达后，A消费它和M1 RunIdleEffects，不代写D实现。A仍需实现原队列fence安全唤醒、旧动作对账后消费新输入、实际applied回执、剩余主动段的可信准入，并逐入口检查原Model/Tool/审批/root期限没有改变。

这属于M2的输入准备子段；M2完整续跑、B真实新页面、C事实门槛、固定DeepSeek及文本成果/H02本人体验仍pending。当前不部署替换H01-v5，不改变原用户Run/历史/费用、flags或本机整链状态。
