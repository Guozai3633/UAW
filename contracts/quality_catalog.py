"""Additive quality-web contracts from the same strict DTOs used by the service."""


def register(types, owners, rules, operations, obj, field, ref, arr, operation):
    from uaw.shared.quality import ROOTS

    def name(value):
        return value if value.startswith("Quality") else "Quality" + value

    def rewrite(value):
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        if not isinstance(value, dict):
            return value
        return {
            key: "#/$defs/" + name(item.rsplit("/", 1)[1])
            if key == "$ref" and item.startswith("#/$defs/") else rewrite(item)
            for key, item in value.items()
        }

    for model in ROOTS:
        schema = model.model_json_schema()
        definitions = schema.pop("$defs", {})
        definitions[model.__name__] = schema
        for original, value in definitions.items():
            key, value = name(original), rewrite(value)
            if key in types:
                assert types[key] == value, key
            else:
                types[key] = value
                owners[key] = "support"
                rules[key] = ["原来源/回答版本绑定；认证用户独立判断，未知不当作通过。"]

    for identity, properties in [
        ("quality.registered", {"review_id": field("ID", "审阅包"), "operator_id": field("ID", "可信登记来源")}),
        ("quality.saved", {"review_id": field("ID", "审阅包"), "revision": field("Revision", "审阅修订"), "auth_session_id": field("ID", "认证会话"), "basis": field({"enum": ["human_evidence_review", "controlled_test"]}, "判断来源")}),
        ("quality.submitted", {"review_id": field("ID", "审阅包"), "revision": field("Revision", "审阅修订"), "auth_session_id": field("ID", "认证会话"), "basis": field({"enum": ["human_evidence_review", "controlled_test"]}, "判断来源")}),
        ("quality.feedback.saved", {"feedback_id": field("ID", "反馈"), "run_id": field("ID", "原任务"), "auth_session_id": field("ID", "认证会话")}),
    ]:
        stem = "".join(part.capitalize() for part in identity.split("."))
        parameters, envelope = stem + "Event", "EventPayload" + stem
        obj(parameters, "support", "独立质量记录的事务审计，不是任务完成事件。", properties)
        obj(envelope, "support", "注册的质量审计分支。", {
            "action": field({"const": identity, "type": "string"}, "事件"),
            "parameters": field(parameters, "审计元数据，不含凭据"),
        })
        types["EventType"]["enum"].append(identity)
        types["EventPayload"]["oneOf"].append(ref(envelope))

    specs = [
        ("quality.reviews.list", "GET", "/v1/quality/reviews", "QualityReviewPage",
         {"cursor": field("ID", "上一页最后 ID", True)}, "read"),
        ("quality.reviews.get", "GET", "/v1/quality/reviews/{review_id}", "QualityReviewView",
         {"review_id": field("ID", "本人审阅包")}, "read"),
        ("quality.reviews.save", "POST", "/v1/quality/reviews/{review_id}/draft", "QualityReviewView", "QualitySave", "write"),
        ("quality.reviews.submit", "POST", "/v1/quality/reviews/{review_id}/submission", "QualityReviewView", "QualitySubmit", "write"),
        ("quality.reviews.export", "GET", "/v1/quality/reviews/{review_id}/export", "QualityExport",
         {"review_id": field("ID", "本人已提交包")}, "read"),
        ("quality.feedback.list", "GET", "/v1/runs/{run_id}/feedback", "QualityFeedbackPage",
         {"run_id": field("ID", "本人原任务")}, "read"),
        ("quality.feedback.save", "POST", "/v1/runs/{run_id}/feedback", "QualityFeedback", "QualityFeedbackSave", "write"),
    ]
    for identity, method, path, response, request, effect in specs:
        request_name = "".join(part.capitalize() for part in identity.split(".")) + "Request"
        if isinstance(request, str):
            import copy
            types[request_name] = copy.deepcopy(types[request])
            types[request_name]["description"] = "认证网页质量审阅写入；要求 CAS 和原目标绑定。"
            owners[request_name], rules[request_name] = "support", []
        else:
            obj(request_name, "support", "认证网页质量审阅/反馈入口。", request)
        operation(identity, "http", "support", "support.evaluation", request_name, response,
                  effect, ["本人归属；写入要求独立对象 CAS/幂等；不修改 Run。"], method, path)
