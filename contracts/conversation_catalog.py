"""Additive conversation-v1 contracts; registration does not install handlers.

The existing RequestMeta/RunRecord/AgentDecision remain at wire version 0.1.
Only these new operations use ConversationRequestMeta version 0.2.
"""

PROTOCOL = "conversation-v1"
WIRE_VERSION = "0.2"


def register(types, owners, rules, operations, obj, field, ref, arr, operation):
    original_names = set(types)
    def literal(value):
        return {"type": "string", "const": value}

    def revision(description):
        return field("Revision", description, minimum=1)

    def reference(name, kind):
        types[name] = {"allOf": [ref("Ref"), {"properties": {"kind": {"const": kind}}}]}
        owners[name], rules[name] = "run", ["结构限定来源类型；真实主体、当前权限、版本仍由来源域核验。"]

    for name, kind in [("ConversationRunRef", "run"), ("ConversationItemRef", "item"),
                       ("ConversationClockRef", "checkpoint")]:
        reference(name, kind)
    obj("ConversationRequestMeta", "run", "新对话控制专用元信息；不能提交给旧0.1入口。", {
        "request_id": field("ID", "同一逻辑补充提交保持不变"),
        "schema_version": field(literal(WIRE_VERSION), "新控制HTTP版本"),
        "expected_revision": revision("原Run预期修订，必需且从1开始"),
    })
    obj("ConversationUnderstanding", "intent", "首次调用中的可选理解提示，不是额外调用或权限。", {
        "summary": field("NonEmptyText", "理解摘要", maxLength=2000, pattern=r"\S"),
        "assumptions": field(arr("NonEmptyText", 8), "明确的少量假设"),
    })
    obj("ClarificationPrompt", "run", "模型的必要补充问题；不是审批请求。", {
        "text": field("NonEmptyText", "自包含问题", pattern=r"\S"),
        "reason": field("NonEmptyText", "缺什么和为什么需要", pattern=r"\S"),
        "options": field(arr("NonEmptyText", 5), "可选候选，空数组表示自由答复", uniqueItems=True),
    })
    obj("ClarificationProposal", "run", "服务从实际ask动作创建的问题提交候选，不是用户授权。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run_ref": field("ConversationRunRef", "原Run预期版本"),
        "input_revision": revision("原有效输入版本"),
        "decision_record_ref": field("Ref", "服务登记的原ask模型回执"),
        "prompt": field("ClarificationPrompt", "须与实际ask输出一致"),
    }, ["Run复查原ask/当前版本/取消/在途调用；问题Item、等待、时钟和事件同域提交；存在在途调用不能暂停主动计时。"])
    common = {
        "protocol": field(literal(PROTOCOL), "首次决策版本"),
        "understanding": field("ConversationUnderstanding", "可选同次理解摘要", True),
    }
    branch_specs = [
        ("FirstReplyDecision", "reply", {"text": field("NonEmptyText", "直接答复，无Artifact硬要求", pattern=r"\S")}),
        ("FirstToolDecision", "tool", {"calls": field(arr("ToolCall", 1, 1), "首版一个工具提案，调用仍经Tool治理")}),
        ("FirstAskDecision", "ask", {"question": field("ClarificationPrompt", "必要问题")}),
        ("FirstDeliverDecision", "deliver", {"text": field("NonEmptyText", "正式文本成果候选，不证明交付成功", pattern=r"\S")}),
    ]
    for name, action, fields in branch_specs:
        obj(name, "agent", "同次首次决策的" + action + "分支，无执行或授权字段。",
            {**common, "action": field(literal(action), "唯一动作"), **fields})
    types["FirstDecision"] = {"description": "首次模型输出；精确互斥分支，不接收真实模型/主体/授权元数据。",
                              "oneOf": [ref(name) for name, _, _ in branch_specs]}
    owners["FirstDecision"], rules["FirstDecision"] = "agent", ["模型提案不直接结束Run；权限和来源由Runtime核验。"]
    obj("FirstDecisionRequest", "agent", "首次调用不要求独立TaskFrame；Context仅最小必要来源。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run_ref": field("ConversationRunRef", "原Run版本"),
        "original_input_ref": field("UserInputRef", "原文来源"),
        "patch_refs": field(arr("UserInputRef", 32), "已受理的有效补充", uniqueItems=True),
        "input_revision": revision("输入集合版本"),
        "context_ref": field("Ref", "有界ContextSnapshot"),
        "remaining_budget": field("Budget", "本次有效调用预算，不复制原完整时限"),
    })
    obj("FirstDecisionRecord", "agent", "服务写入的实际模型来源；不能由模型自报。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run_ref": field("ConversationRunRef", "原Run版本"),
        "input_revision": revision("决策使用的输入集合版本"),
        "decision": field("FirstDecision", "原模型动作"),
        "model_output_ref": field("Ref", "Model owning reader固定回执"),
        "model_policy_ref": field("Ref", "原用户固定模型政策"),
        "attempt_id": field("ID", "实际ModelOutput尝试，必须与来源一致"),
        "usage_ref": field("Ref", "实际用量，pending保留"),
    })
    obj("ConversationProtocolBinding", "run", "新Run专用版本绑定；不转换旧Run或改写旧Budget语义。", {
        "protocol": field(literal(PROTOCOL), "实际准入的版本"),
        "run_id": field("ID", "新Run"), "owner_id": field("ID", "服务从原会话核实的用户"), "revision": revision("绑定CAS修订"),
        "input_revision": revision("当前有效输入集合版本"),
        "completion_mode": field({"type": "string", "enum": ["message", "delivery"]}, "消息或正式交付"),
        "clock_ref": field("ConversationClockRef", "新Run专属计时检查点"),
    }, ["只有服务准入记录可启用新模式；缺记录使用legacy固定原deadline；不能从模型参数推断绑定。"])
    obj("ReplyProposal", "run", "消息完成候选，无Artifact/VerificationReport或用户接受字段。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run_ref": field("ConversationRunRef", "提议结束的原Run版本"),
        "input_revision": revision("有效原文/补充版本"),
        "decision_record_ref": field("Ref", "已登记FirstDecisionRecord"),
        "text": field("NonEmptyText", "实际原模型reply文本", pattern=r"\S"),
        "source_refs": field(arr("Ref", 32), "已实际读取的用户材料/工具引用"),
        "unresolved_effect_refs": field(arr("Ref", 0), "消息终态依赖未决效果必须为空"),
    }, ["实际commit读取完整Tool/模型账本与当前输入版本，不能只相信提案的空效果列表；来源正文/attempt/模型政策与reply分支必须一致。"])
    obj("ReplyCommitReceipt", "run", "消息与Run/Event原子提交的服务回执。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run": field("RunRecord", "实际completed Run"),
        "item": field("InteractionItem", "实际agent_message"),
        "input_revision": revision("提交时输入版本"),
        "event_seq": revision("最后持久事件位置"),
    })
    types["ReplyCommitReceipt"]["properties"]["run"] = {"description": "实际completed Run", "allOf": [ref("RunRecord"), {"properties": {"status": {"const": "completed"}, "outcome": {"const": "succeeded"}}, "required": ["outcome"]}]}
    types["ReplyCommitReceipt"]["properties"]["item"] = {"description": "实际消息Item", "allOf": [ref("InteractionItem"), {"properties": {"type": {"const": "agent_message"}, "status": {"const": "completed"}}, "required": ["run_id"]}]}
    obj("ClarificationQuestion", "run", "原问题的持久权威关联，用稳定Item表达，无新RefKind。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run_id": field("ID", "原Run"), "conversation_id": field("ID", "所属会话"),
        "item_id": field("ID", "agent_message问题Item"), "revision": revision("问题CAS版本"),
        "input_revision": revision("提问时有效原文版本"),
        "prompt": field("ClarificationPrompt", "用户看到的问题"),
        "decision_record_ref": field("Ref", "原ask动作的实际模型记录"),
        "state": field({"type": "string", "enum": ["open", "answered", "stale", "cancelled"]}, "问题状态"),
        "created_at": field("Timestamp", "问题提交时间"),
        "answer_input_ref": field("UserInputRef", "实际受理答复，answered时必需", True),
    })
    types["ClarificationQuestion"]["allOf"] = [{"if": {"properties": {"state": {"const": "answered"}}, "required": ["state"]},
        "then": {"required": ["answer_input_ref"]}, "else": {"not": {"required": ["answer_input_ref"]}}}]
    obj("ClarificationView", "run", "UI同源读取原问题与Run，刷新不创建新launch或会话。", {
        "question": field("ClarificationQuestion", "当前实际问题"),
        "run_revision": revision("当前Run版本，用于提交CAS"),
        "run_status": field("RunStatus", "当前Run真实状态"),
        "input_revision": revision("当前有效输入版本"),
    })
    types["ClarificationView"]["allOf"] = [{"if": {"properties": {"question": {"properties": {"state": {"const": "open"}}, "required": ["state"]}}, "required": ["question"]},
        "then": {"properties": {"run_status": {"const": "waiting_for_user"}}}}]
    obj("RunClarificationAnswerRequest", "run", "原Run回答；身份和expected_run_revision来自meta。", {
        "run_id": field("ID", "路径中的原Run"),
        "question_item_id": field("ID", "路径中原问题稳定Item"),
        "expected_question_revision": revision("问题预期CAS版本"),
        "expected_input_revision": revision("原有效输入版本"),
        "text": field("Text", "用户真实回答"),
        "attachment_refs": field(arr("Ref", 16), "本人获准材料，真实权限另查", uniqueItems=True),
    })
    obj("RunCorrectionRequest", "run", "当前Run纠正，不让客户端指定任意执行节点或权限。", {
        "run_id": field("ID", "路径中的原Run"),
        "expected_input_revision": revision("原有效输入版本"),
        "text": field("Text", "明确用户纠正"),
        "attachment_refs": field(arr("Ref", 16), "本人获准材料", uniqueItems=True),
    })
    for name in ("RunClarificationAnswerRequest", "RunCorrectionRequest"):
        types[name]["anyOf"] = [{"properties": {"text": {"minLength": 1, "pattern": r"\S"}}, "required": ["text"]},
                              {"properties": {"attachment_refs": {"minItems": 1}}, "required": ["attachment_refs"]}]
        rules[name] = ["请求+附件总字节有界；客户端引用不赋予权限；真实同用户会话、Run/问题/输入CAS、幂等和终态/取消复核。"]
    obj("RunInputPatch", "run", "追加输入关联，InputRecord结构不变；受理与生效区分。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run_id": field("ID", "原Run"), "conversation_id": field("ID", "会话"),
        "request_id": field("ID", "原用户逻辑请求"),
        "input_ref": field("UserInputRef", "原子追加的实际InputRecord"),
        "kind": field({"type": "string", "enum": ["clarification_answer", "correction"]}, "来源类型"),
        "base_input_revision": revision("原有效输入版本"), "input_revision": revision("受理后有效输入版本"),
        "question_item_id": field("ID", "澄清时必需；纠正时不允许", True),
        "question_revision": field("Revision", "原提问版本，与Item关联", True, minimum=1),
        "state": field({"type": "string", "enum": ["accepted", "applied", "superseded", "cancelled"]}, "受理/真实生效"),
        "created_at": field("Timestamp", "受理时间"), "applied_at": field("Timestamp", "实际安全边界生效时刻", True),
    })
    types["RunInputPatch"]["allOf"] = [
        {"if": {"properties": {"kind": {"const": "clarification_answer"}}, "required": ["kind"]},
         "then": {"required": ["question_item_id", "question_revision"]},
         "else": {"not": {"anyOf": [{"required": ["question_item_id"]}, {"required": ["question_revision"]}]}}},
        {"if": {"properties": {"state": {"const": "applied"}}, "required": ["state"]},
         "then": {"required": ["applied_at"]}, "else": {"not": {"required": ["applied_at"]}}},
    ]
    obj("RunContinuationReceipt", "run", "补充受理和实际生效回执，不等于最终成果完成。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run": field("RunRecord", "当前原Run；允许受理后又取消的查询结果"),
        "patch": field("RunInputPatch", "原请求受理及生效状态"),
        "event_seq": revision("最后可续持久事件序号"),
    })
    obj("RunInputApplication", "run", "原模型实际消费补充的不可变证据；不是执行授权。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run_id": field("ID", "原Run"), "input_revision": revision("实际模型输入版本"),
        "attempt_id": field("ID", "原模型attempt"),
        "context_snapshot_ref": field("Ref", "实际调用固定上下文"),
        "model_output_ref": field("Ref", "实际完成模型输出"),
        "decision_record_ref": field("Ref", "所属有效Agent决策"),
        "source_input_refs": field(arr("UserInputRef", 17, 2), "原文及全部实际消费补充", uniqueItems=True),
        "patch_input_refs": field(arr("UserInputRef", 16, 1), "本事务从accepted变applied的原Input", uniqueItems=True),
        "applied_at": field("Timestamp", "可信服务提交时间"),
    }, ["只有原ModelInvocation/Output/LoopOperation与快照、当前输入/来源和已登记decision全部一致才标生效。",
        "patch、不可变应用证据、Run版本及Outbox同事务；重读/重启不重复应用，不更新ModelOutput或旧输入。",
        "不创建预算、权限、续期、唤醒或自动接受；仅证明原模型已消费。"])

    obj(
        "InternalRunActiveSegment",
        "run",
        "可信服务在原事务签发的新执行段；非HTTP或模型输入。",
        {
            "protocol": field(literal(PROTOCOL), "协议"),
            "run_id": field("ID", "原Run"),
            "revision": revision("执行段CAS修订"),
            "input_revision": revision("签发时的有效补充版本"),
            "context": field("TrustedExecutionContext", "仅新调用使用的新上下文；旧上下文保留"),
            "source_job_ref": field("Ref", "原blocked作业历史版本和完整摘要"),
            "clock_ref": field("ConversationClockRef", "实际active时钟历史版本和摘要"),
            "budget_hash": field("Hash", "原Run预算全量摘要，不增加资源或限额"),
            "ledger_deadline": field("Timestamp", "原账本截止时间，不能改写"),
            "issued_at": field("Timestamp", "原active时钟捕获时刻"),
        },
        [
            "只在同Run安全续跑事务中由实际D时钟剩余额度派生，源作业与时钟历史必须可复核。",
            "不修改旧Run预算/账本deadline、invocation、预留、审批或native授权；新段不是权限或额度扩张。",
            "缺生产clock/源版本、归属变化、取消、时钟停止或原额度耗尽均拒绝；旧协议原期限不变。",
        ],
    )

    obj("RunExecutionClock", "run", "新Run有版本主动执行时钟；旧调用/授权独立到期。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run_id": field("ID", "原Run"), "revision": revision("持久CAS修订"),
        "mode": field({"type": "string", "enum": ["active", "waiting_for_user", "stopped"]}, "执行段状态"),
        "active_limit_ms": field("Duration", "最大主动执行时间", minimum=1),
        "active_elapsed_ms": field({"type": "integer", "minimum": 0, "maximum": 9007199254740991}, "已经结束的主动段实际耗时，允许真实超额但不能再执行"),
        "wait_elapsed_ms": field({"type": "integer", "minimum": 0, "maximum": 9007199254740991}, "已经结束的等待耗时，与主动时间上限分别计量"),
        "captured_at": field("Timestamp", "可信服务采集时间"),
        "active_since": field("Timestamp", "active时必需，最近主动段起点", True),
        "waiting_since": field("Timestamp", "等待时必需，当前等待起点", True),
        "waiting_item_ref": field("ConversationItemRef", "等待问题或人工审批的稳定Item", True),
        "in_flight_refs": field(arr("Ref", 64), "原已派发且未结束调用；不能当免费暂停"),
    })
    types["RunExecutionClock"]["allOf"] = [
        {"if": {"properties": {"mode": {"const": "active"}}, "required": ["mode"]},
         "then": {"required": ["active_since"], "not": {"anyOf": [{"required": ["waiting_since"]}, {"required": ["waiting_item_ref"]}]}}},
        {"if": {"properties": {"mode": {"const": "waiting_for_user"}}, "required": ["mode"]},
         "then": {"required": ["waiting_since", "waiting_item_ref"], "not": {"required": ["active_since"]}, "properties": {"in_flight_refs": {"maxItems": 0}}}},
        {"if": {"properties": {"mode": {"const": "stopped"}}, "required": ["mode"]},
         "then": {"not": {"anyOf": [{"required": ["active_since"]}, {"required": ["waiting_since"]}, {"required": ["waiting_item_ref"]}]}}},
    ]
    rules["RunExecutionClock"] = ["时间只由可信Run服务采集；active_since/waiting_since不能晚于captured_at；真实耗时超额照实保存，剩余归0且不能续领时间。",
        "主动段并集计时；未知在途调用不得转waiting免费暂停；进程重启/租约丢失按持久段对账，不重领完整预算。",
        "预算deadline原0.1语义不改；新Run按协议绑定使用此时钟派生尚未发送调用的期限，已经发送的ctx/deadline不修改。"]

    def http(id, method, path, request, response, write=False):
        operation(id, "http", "run", "ui ingress run.history run.state run.budget", request, response,
                  "internal_write" if write else "read", [
                      "MS-I2m M1仅安装所属原Run控制的读取与受理handler，尚不唤醒执行；旧Run无conversation-v1绑定明确拒绝，不转换旧期限。",
                      "实际认证、精确Origin、CSRF与原会话归属仍必需；请求体没有可信主体、批准或授权字段。",
                      "受理后返回真实原Run/补充状态；当前权限/模型/预算复核和未知效果对账后才执行。",
                  ], method=method, path=path,
                  errors=["旧协议或来源缺失明确不可用；版本冲突重读；终态/取消不能复活；unknown先对账不重发。"])
        operations[-1].update(wire_version=WIRE_VERSION, request_meta="ConversationRequestMeta",
                              requires_cas=write, protocol=PROTOCOL, browser_session=True)

    obj("RunConversationView", "run", "当前Run对话控制读图；问题ID来自持久来源，不猜消息文本。", {
        "protocol": field(literal(PROTOCOL), "对话协议"),
        "run": field("RunRecord", "当前原Run及CAS修订"),
        "input_revision": revision("当前有效输入版本"),
        "question": field("ClarificationView", "当前仍开放的具体问题；没有时省略，不传null", True),
        "continuation_request_ids": field(arr("ID", 64), "按输入版本排序的既有补充request_id；查询原回执用", uniqueItems=True),
    }, ["同一事务内读取当前owned会话/Run/协议/输入集/问题/补充；问题必须与当前Run/input版本一致。",
        "只读，不触发执行/续期/重发；旧Run无协议返回明确503，取消/终态保持可读。",
        "question只在open且原Run等待时返回；人工工具审批与成果接受不伪装成澄清。"])
    http("runs.conversation.get", "GET", "/v1/runs/{run_id}/conversation", "RunsGetRequest", "RunConversationView")

    obj("RunPresentationUnderstanding", "run", "同次真实模型决策的理解提示，独立于不可变执行帧。", {
        "state": field({"type":"string", "enum":["pending", "available", "not_provided"]}, "尚未得到决策、有原理解或本次未提供"),
        "input_revision": revision("本次读取的当前输入版本"),
        "value": field("ConversationUnderstanding", "真实模型摘要和假设；没有时省略", True),
        "decision_record_ref": field("Ref", "原FirstDecisionRecord及摘要", True),
        "model_output_ref": field("Ref", "原ModelOutput版本", True),
    }, ["available必须绑定同Run/当前input_revision的原决策及成功ModelOutput；不改TaskFrame或补造理解。"])
    types["RunPresentationUnderstanding"]["allOf"] = [
        {"if":{"properties":{"state":{"const":"available"}},"required":["state"]},
         "then":{"required":["value","decision_record_ref","model_output_ref"]},
         "else":{"not":{"anyOf":[{"required":[name]} for name in ["value","decision_record_ref","model_output_ref"]]}}},
    ]
    obj("RunPresentationDelivery", "run", "当前输入和Run修订的完整已登记成果引用；不是接受授权。", {
        "bundle_ref": field("Ref", "原完整成果包"),
        "artifact_ref": field("Ref", "原成果版本"),
        "report_ref": field("Ref", "原逐项核验"),
        "proposal_ref": field("Ref", "原交付提案"),
        "run_revision": revision("交付提案绑定的当前Run修订"),
        "input_revision": revision("原执行帧绑定的当前输入版本"),
        "outcome": field("Outcome", "真实核验结果，不代表独立事实质量"),
        "requires_acceptance": field("Bool", "原合同是否要求本人接受"),
    })
    obj("RunPresentationView", "run", "同一只读数据库快照中的显示阶段、真实理解及当前成果；不授权执行或完成。", {
        "protocol": field(literal(PROTOCOL), "协议"),
        "run": field("RunRecord", "权威原Run，保持原CAS修订和状态"),
        "input_revision": revision("当前有效输入版本"),
        "phase": field({"type":"string", "enum":["preparing","working","verifying","waiting_for_user","awaiting_acceptance","finalizing","needs_revision","stopping","completed","failed","cancelled","unavailable"]}, "显示阶段，不替代Run.status；取消受理尚未终态为stopping"),
        "understanding": field("RunPresentationUnderstanding", "真实理解状态与来源"),
        "delivery": field("RunPresentationDelivery", "仅返回同一当前Run修订和输入的成果", True),
        "stopped_reply_ref": field("Ref", "原普通回复与调用已停止的证据；仅释放本地发送查询，不结算Run/费用或授权续跑", True),
        "captured_at": field("Timestamp", "一致性快照读取时间"),
    }, ["读取原Run、输入、实际决策/ModelOutput、原job及当前成果；同一次REPEATABLE READ READ ONLY事务，不写事件或执行。",
        "awaiting_acceptance要求当前完整成果、实际交付等待、原合同要求接受、核验成功且未接受；旧成果或unknown不得推断完成。",
        "已有Frame、Proposal和Run不因显示理解/阶段被改写；缺源503/明确不可用；0.1与旧conversation端点不变。"])
    http("runs.presentation.get", "GET", "/v1/runs/{run_id}/presentation", "RunsGetRequest", "RunPresentationView")

    obj("RunClarificationGetRequest", "run", "读取原Run特定问题，不猜最新问题。", {
        "run_id": field("ID", "路径原Run"), "question_item_id": field("ID", "路径原问题"),
    })
    obj("RunContinuationGetRequest", "run", "原提交响应丢失或刷新后的受理/生效查询。", {
        "run_id": field("ID", "路径原Run"), "request_id": field("ID", "路径原逻辑提交ID"),
    })
    http("runs.clarification.get", "GET", "/v1/runs/{run_id}/clarifications/{question_item_id}", "RunClarificationGetRequest", "ClarificationView")
    http("runs.clarification.answer", "POST", "/v1/runs/{run_id}/clarifications/{question_item_id}/answers", "RunClarificationAnswerRequest", "RunContinuationReceipt", True)
    http("runs.correction.create", "POST", "/v1/runs/{run_id}/corrections", "RunCorrectionRequest", "RunContinuationReceipt", True)
    http("runs.continuation.get", "GET", "/v1/runs/{run_id}/continuations/{request_id}", "RunContinuationGetRequest", "RunContinuationReceipt")
    for id, owner, nodes, request, response in [
        ("AgentRuntime.first_decision", "agent", "agent.loop intent.semantic", "FirstDecisionRequest", "FirstDecisionRecord"),
        ("RunRuntime.commit_reply", "run", "run.state run.history agent.loop", "ReplyProposal", "ReplyCommitReceipt"),
        ("RunRuntime.commit_question", "run", "run.state run.history run.budget intent.ambiguity", "ClarificationProposal", "ClarificationView"),
    ]:
        operation(id, "runtime", owner, nodes, request, response, "internal_write", [
            "仅可信服务port；未装配时明确不可用。模型来源与当前Run/输入/权限/预算/取消由服务复核。",
            "首次动作不能直接结束Run；消息完成不要求Artifact，但原Tool效果账本不能仅信任空候选列表。",
        ], auth="service")
        operations[-1].update(protocol=PROTOCOL, wire_version=WIRE_VERSION)
    for name in set(types) - original_names:
        types[name]["x-uaw-protocol"] = PROTOCOL
