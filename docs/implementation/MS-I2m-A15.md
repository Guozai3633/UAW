# A15 / H02-I03：原任务显示阶段与真实理解

2026-10-18。本人成果抽屉已读到报告，聊天区却显示running和“等待实际任务理解”。只读核对确认它们是同一个Run `run-169ef7763d694cc297c00b51dea9e6b4`、输入v1、Run修订5。job实际delivery/waiting，模型2调用已结束，报告已核验，正在等待本人审阅；模型同次返回understanding，但旧页面只读执行TaskFrame，没有消费真实决策中的理解。

## 模块、接口和策略

| 位置 | 处理策略 |
| --- | --- |
| `contracts/conversation_catalog.py` | 新增5个类型及一个只读0.2端点；原1404个类型逐对象不变 |
| `src/uaw/run/presentation.py` | 统一读取原Run、当前输入、同版原模型理解及当前完整成果；一个REPEATABLE READ READ ONLY事务，没有执行和写入 |
| `src/uaw/api/conversation.py`、`routes.py` | 复用实际认证及0.2读取规则；`GET /v1/runs/{run_id}/presentation`，no-store；非所属用户/旧协议/未知参数拒绝 |
| `tests/integration/agent/test_run_presentation.py` | 真实SQL检查原报告/理解、缺摘要、修订后旧成果、接受前后、取消受理、unknown、并发快照及HTTP |
| B `apps/web/` | 后续消费统一读图，将主界面、成果入口和理解显示为同一版本；A不代写其源码 |

该接口是显示投影，不替代Run.status。为保留原DeliveryProposal绑定的Run修订及本人接受合同，不因改文案推进Run、重新生成报告或覆盖Frame。理解取自同Run/当前输入的最新真实FirstDecisionRecord及成功ModelOutput；缺失区分pending/not_provided，不能伪造独立语义解析或额外调用模型。

显示阶段包括preparing、working、verifying、waiting_for_user、awaiting_acceptance、finalizing、needs_revision、stopping及实际completed/failed/cancelled，另有unavailable。awaiting_acceptance只在当前完整Bundle/Artifact/Report/Contract/Proposal相符、原Run/Frame/输入版本匹配、原合同要求本人接受、核验成功、尚无接受决定且原效果已结清可等待时返回。当前权限或执行权不由本接口授予；真正读取正文和接受仍调用原接口并独立复核。

取消请求已受理但原Run尚未终态显示stopping，不提前冒充cancelled。本人接受持久化后、原队列完成前显示finalizing；只有原Run.completed才显示completed。新输入或Run修订变化后旧成果不返回当前delivery，原成果仍能通过原历史Reader查看。

## 原会话与验证边界

新的Reader已在本人原库存只读得到awaiting_acceptance、understanding=available、同Run/v5成果；0新模型调用、0运行写入。截图原Run未停止、重发、完成或代接受。

首次SQL为5通过/3失败：遗漏“取消受理尚未终态”的显示分支；两个测试错误预期已cancelled；一个HTTP测试错误预期400而原0.2拒绝约定为422。新增stopping并保留旧回执，未弱化取消或认证。最终验证以[SQL回执](evidence/h02-i03-presentation-final.xml)和后续机器记录为准。

契约校验默认对比历史675项快照会报旧源码不同；原结果保留，使用原准确证据提交核对历史，不能把旧全量改成当前全量。当前新源码类型/受影响SQL分别验证，不更新last_full，不代替事实质量或本人体验。

## 页面接线与阶段

[B具体修复单](../coordination/requests/A/H02-I03-B-run-presentation-sync.md)已获本人授权直接派发；A固定准确接口源码后发送。此阶段尚未部署到H02-v5，旧页面仍可能显示原文案；不能把Reader通过当真实页面修复。B需在自己原工作区普通合并准确阶段源码，保留原交付，不合浮动integration；仅修改B允许路径。C/D无新包。

## A15固定组件回执

最终10个不同真实SQL通过＝8新Reader/HTTP节点＋2原问题/成果接受回归；249源码类型/4Python静态格式通过。契约1409正例/337反例通过，原1404schema与原所有OpenAPI路径逐对象不变，只有5新对象和1新端点。旧675为指定历史源码的证据核对，不是本轮全仓；原默认源码差异及过早查询未产生的最终XML记录均保留。[机器记录](evidence/h02-i03-a15.json)。

B应消费[字段与异步版本规则](../coordination/requests/A/MS-I2m-A15-presentation-wiring.md)。A源标签发布不意味着H02页面已更新，实际部署与B回执另行记录。
