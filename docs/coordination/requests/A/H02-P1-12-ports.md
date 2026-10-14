# H02 P1-12：固定公共契约与消费说明

2026-10-14，Session A / integration。契约目录 **0.2**，模型动作标记 **conversation-v1**。准确阶段提交以 DISPATCH 页首为准。此契约阶段不是新页面/原任务续跑上线，也不自动派发 B/C/D。

## 1. 状态及兼容范围

已实现：统一 schema 新对象、四分支首次决策、Python 严格消费者、公共 port、纯时钟读取与原用户/Run/问题/CAS 检查函数。未实现：新 HTTP handlers、数据库原子追加/时钟持久化/Outbox、首次真实模型路由、消息完成提交及 B 页面接续。

**旧 0.1 的 1362 个命名结构保持不变**。原 RequestMeta.schema_version=0.1、AgentDecision 的 respond/call_tools/wait/propose_completion/blocked、原 InputRecord/RunRecord/Budget/RootBudgetLedger 保留。新 Run 必须在受理时登记 ConversationProtocolBinding，缺记录只能按旧原 deadline 工作；不得把用户现有取消任务批量转换成新模式。

## 2. 大模块与精确对象

| 模块 | 对象/port | 实际输入、输出和边界 |
| --- | --- | --- |
| Agent / Intent | FirstDecisionRequest → FirstDecisionRecord；FirstDecisionPort.decide | 输入原Run、原InputRef、补充、输入版本、最小Context、剩余调用预算；没有强制TaskFrame。输出服务固定的模型/attempt/usage与唯一动作；模型不能自报可信元数据 |
| Agent 首次输出 | FirstDecision | protocol=conversation-v1；reply(text)、tool(calls恰好1)、ask(question文本/原因/候选)、deliver(text)互斥。理解摘要可省略，不因省略额外调用 |
| Run 消息 | ReplyProposal → ReplyCommitReceipt；ReplyCommitPort.commit | 原决策记录、Run/输入版本、消息文本与实际引用；不要求Artifact。提交前读完整Model/Tool账本及取消/当前来源，不能只信空unresolved_effect_refs |
| Run 问题 | ClarificationProposal → ClarificationView；QuestionCommitPort.commit | 原ask来源、输入版本、具体问题；问题Item、waiting、暂停时钟、事件同域提交，实际有在途调用时不能免费暂停 |
| Run 控制 | ConversationControlPort.question/answer/correct/lookup | 当前真实用户、原Run/问题、两个CAS版本、幂等键；先受理再到安全边界生效，不让LLM审批自己 |
| Run 时间 | RunExecutionClock；ExecutionClockPort.current | 当前持久段、累计主动/等待时间、原上限、在途调用与等待Item；remaining_active_ms是纯读数，不是授权或续跑 |

精确字段见 [对象总字典](../../../api/OBJECTS.md)，维护源 [conversation_catalog.py](../../../../contracts/conversation_catalog.py) 由 interface_catalog.finalize 注册；Python 消费者在 [shared/conversation.py](../../../../src/uaw/shared/conversation.py)，业务纯检查在 [run/conversation_protocol.py](../../../../src/uaw/run/conversation_protocol.py)。

## 3. 新 HTTP 端点（尚未安装）

| 方法与路径 | 请求/结果 |
| --- | --- |
| GET /v1/runs/{run_id}/clarifications/{question_item_id} | RunClarificationGetRequest → ClarificationView |
| POST /v1/runs/{run_id}/clarifications/{question_item_id}/answers | RunClarificationAnswerRequest → RunContinuationReceipt |
| POST /v1/runs/{run_id}/corrections | RunCorrectionRequest → RunContinuationReceipt |
| GET /v1/runs/{run_id}/continuations/{request_id} | RunContinuationGetRequest → RunContinuationReceipt |

写请求仍是 `{meta,payload}`，路径参数不得重复塞进payload。**新meta使用0.2且expected_revision≥1**；payload不再重复Run版本，但包含 expected_input_revision，澄清另含 expected_question_revision。GET可用X-UAW-Schema-Version: 0.2。

```json
{
  "meta": {"request_id": "answer-1", "schema_version": "0.2", "expected_revision": 6},
  "payload": {
    "expected_question_revision": 1,
    "expected_input_revision": 1,
    "text": "我指的是协调协议。",
    "attachment_refs": []
  }
}
```

这是形状示例，run/question必须来自当前页面读取，不能实际发送示例ID。实际Cookie登录沿用已有受保护同源会话，写请求核对精确Origin与X-UAW-CSRF；CLI保持原Bearer认证。新端点未安装时当前服务404，不声称已经支持续跑；装配后缺真实来源应按合同明确503，不能用mock填可用状态。

相同用户/Run/操作/request_id+相同参数返回原受理及最新生效状态；同键不同内容409。重试先查询continuations原ID，不生成第二Run。取消/终态409，输入/问题失效412，归属拒绝403；实际认证失效401。旧问题answered/stale/cancelled不可再次回答。

## 4. A/B 的下一轮接线顺序

1. A在新Run受理时固定protocol binding、原用户/输入集合和clock；原Run保持legacy，Budget原绝对deadline不能就地改成长等待免费执行。
2. A实现P1-13 FirstDecision调用和真实模型owning reader；同次理解消费，reply消息与deliver合同分流，模型政策不暗换。
3. A实现P1-14 Run事务：读取当前owned conversation/Run/protocol/question/取消与租约；调用纯边界检查只是其中一步。原InputRecord追加、InputPatch关联、输入集合、问题关闭、Run/Clock和Outbox同域提交；附件当前来源单独复核。
4. 生效前再查模型、当前权限、总费用、授权/租约期限、原未决效果。新调用按剩余主动段构造新的有效调用deadline；旧invocation deadline、15/90秒本机期限、审批/root有效期都不改。
5. B收到正式允许目录和准确源后接上述端点；区分accepted与applied反馈，刷新先读原问题/原提交，保留草稿，不自动停止/发送/native确认/成果接受。

P1-12只提供协议和纯函数，**没有事务/权限Reader/服务实例替身**。未连接模块按真实可用性返回失败，实际资料读数不能只靠参数自报。

### 后续记录与事务位置（尚未写入生产数据）

| 逻辑命名空间 | 记录/schema | 键与CAS |
| --- | --- | --- |
| run.protocol_bindings | ConversationProtocolBinding | 原run_id；revision CAS；owner由当前原会话读入 |
| run.execution_clocks | RunExecutionClock | 原run_id；revision CAS；clock_ref用checkpoint容器、原run_id与clock修订，由专用Reader解析 |
| run.clarification_questions | ClarificationQuestion | 稳定item_id；revision CAS；不能凭文本搜索猜最新问题 |
| run.input_patches | RunInputPatch | 使用原主体/Run/操作/request_id规范哈希派生有界ID；原request_id保留用于查询/幂等 |

这些目标记录可落现有RecordStore通用表，不需要先改DDL；业务归属/CAS/Outbox仍由Run事务实现，不能把共享表当万能状态。问题Item与独立问题记录同原事务，读取对照归属/版本；clock_ref不是通用恢复命令。

首次控制受理增加InputPatch与输入集合版本，令旧模型提案失效；accepted表示新要求已持久化，applied表示Agent到达安全边界并消费。不可取消的旧调用继续原参数/期限完成或对账，不把旧结果当新目标成功；后续补充以当前已受理输入版本为CAS。

事件沿用已有item.updated/run.updated及稳定Item/revision结构；控制受理/生效新增类型需P1-14注册实际EventPayload分支后发布，不能往现有严格枚举塞临时JSON。若事务失败或租约丢失，重读原request_id回执和clock；用户等待、未知费用与原调用分别恢复。

## 5. 本地消费演示与验收

```powershell
.venv/Scripts/python.exe ops/demo_conversation_contracts.py
.venv/Scripts/python.exe -m pytest -q tests/unit/shared/test_conversation_contracts.py tests/unit/shared/test_contracts.py
.venv/Scripts/python.exe contracts/check_interfaces.py --implementation-source-ref 90ef2f12bc92eea2877cb8c9d8820e9f833552bb
```

演示只解析fixture、读取暂停时钟，不运行HTTP/LLM或写状态。严格数组消费使用model_validate_json，wire仍是JSON数组；Python model_validate不负责把任意类型强制转换。

契约checker显式固定历史源码核对原回执，并列出当前源码差异。它不把旧675历史并集当本轮全量；本轮实际用例/失败/静态/类型回执见 [P1-12报告](../../../implementation/P1-12.md)。新接口均 implemented=false，只有真正服务/模型/页面验收后才更新实现登记。
