# A15固定读取接口：同Run阶段、真实理解与当前成果

2026-10-18。B消费本页和[本人具体修复单](H02-I03-B-run-presentation-sync.md)。本页不代表页面已改或本人体验已验收；准确可消费提交以DISPATCH页首发布SHA为准。

## 1. HTTP与对象

`GET /v1/runs/{run_id}/presentation`，`X-UAW-Schema-Version: 0.2`，沿用原cookie用户会话或CLI bearer。只接受路径run_id，无查询字段/请求体。返回原`kind/ payload/ output_refs`封装，成功payload为生成对象`RunPresentationView`；`Cache-Control: no-store`。缺旧协议来源503、非本人404/403、版本/来源不一致412；错误0.2版本或查询遵守原reject默认422。服务不接受请求自报主体或授权。

```text
payload.protocol = conversation-v1
payload.run = 原RunRecord（状态/修订不改）
payload.input_revision = 当前有效输入版本
payload.phase = 显示阶段
payload.understanding = {state, input_revision, value?, decision_record_ref?, model_output_ref?}
payload.delivery? = {bundle_ref, artifact_ref, report_ref, proposal_ref,
                    run_revision, input_revision, outcome, requires_acceptance}
payload.captured_at = 本次一致性快照读取时间
```

| 字段 | B的消费与约束 |
| --- | --- |
| `phase=awaiting_acceptance` | “成果已就绪，等待你审阅”；打开成果。不能改Run.status、启用新请求或代接受 |
| `phase=finalizing` | “正在收尾”；已经有本人决定/无需接受而后台未终态，不能宣称completed |
| `phase=stopping` | 取消已受理，原Run尚未终态；显示正在停止，不当作cancelled |
| `phase=needs_revision` | 当前成果未满足合同或本人拒绝；引导查看原核验，不冒充成功 |
| `phase=completed/failed/cancelled` | 必须与返回原Run实际终态相同 |
| `phase=working/preparing/verifying/waiting_for_user` | 显示原阶段；澄清继续由原ConversationView定位具体问题；不能把人工审批/成果接受当问题 |
| `phase=unavailable`或接口错误 | 当前来源不可核对；明确不可用，不猜测成功、重发或复活任务 |
| `understanding.state=available` | 显示`value.summary/assumptions`及input_revision；来自原真实ModelOutput，不再等待TaskFrame.summary |
| `not_provided` | 模型已决策但未附摘要；“按你的原文执行，本次未单独提供理解摘要”，或隐藏卡片，不追加模型调用 |
| `pending` | 当前输入尚无已完成真实决策，只有此时才显示等待；旧理解不能冒充当前 |
| `delivery` | 只含原当前Run/输入版本匹配的引用；全文/核验/接受仍走原DeliveryReader/accept API，保持所有授权、摘要与CAS检查 |

## 2. 版本和异步读取

这是同一REPEATABLE READ READ ONLY快照；不写Frame、Run、事件、预算或Proposal。`captured_at`不是命令ID或授权。由于原Run修订为本人接受提案固定，**phase和understanding可在Run.revision不变时更新**；不能只在revision增加时刷新这两个字段。B要用实际请求generation/abort及同账号+conversation+run绑定处理迟到响应；接受/纠正同时发生时另按input_revision核对。

1. 工作区和成果面板使用同一最新有效读图，或在收到有版本差异时统一重读。不要把抽屉的新成果与主区旧loading并列当最新状态。
2. 读图中Run.id/conversation_id必须与当前页面匹配；input_revision需与当前补充读图一致。新补充后旧delivery不返回当前字段，但原历史成果仍可读。
3. 真实接受决定后phase可能先finalizing、再completed；接受按钮使用原Delivery接口当前版本重查，不能凭phase授予接受权。
4. 自动读取只做GET，不触发后台/续期/原任务重发。读取中保留上一份已核对展示，并标更新，不反复清空卡片。超限/缺源准确提示。

## 3. 实测和固定来源

原截图Run/v5/Input1通过新Reader只读得出awaiting_acceptance，真实理解available，成果当前可读；新增模型0、原运行写入0。原Frame/Proposal/Run没有因显示摘要改版。接口实际认证HTTP和并发取消快照用随机测试主体验证；不是本人接受或事实质量证明。

本轮5个新schema，原1404类型逐对象不变。生成源是`contracts/conversation_catalog.py`，B仅在自己apps/web中正常运行generate消费，不编辑canonical或复制自造DTO；原B契约生成器保持。A不操作B分支或未提交文件。B交阶段后A会准备准确新服务/原Page，以当时的实际来源为准；当前H02-v5尚未有此端点。
