"""Durable display checkpoints; original Model/Run completion remain authoritative."""


def register(obj, field):
    obj("ConversationStreamRecord", "run", "原模型调用的未完成正文检查点，不授予执行或完成。", {
        "id": field("ID", "原invocation ID"),
        "revision": field("Revision", "流记录CAS"),
        "run_id": field("ID", "原Run"),
        "conversation_id": field("ID", "原会话"),
        "operation_id": field("ID", "原Agent operation"),
        "item_id": field("ID", "原稳定消息"),
        "input_revision": field("Revision", "原输入版本"),
        "attempt_id": field("ID", "实际提供方attempt"),
        "snapshot_ref": field("Ref", "原上下文"),
        "model_config": field("ResolvedModelConfig", "原模型配置"),
        "state": field({"enum": ["receiving", "received", "interrupted", "published"]}, "生命周期"),
        "text": field("Text", "只含允许展示的普通回复前缀"),
        "created_at": field("Timestamp", "创建时刻"),
        "updated_at": field("Timestamp", "最新检查点时刻"),
        "first_provider_at": field("Timestamp", "首content，不含推理", True),
        "first_text_at": field("Timestamp", "首可展示正文", True),
        "received_at": field("Timestamp", "原响应收齐时刻", True),
        "output_ref": field("Ref", "原模型输出", True),
        "failure_code": field("ID", "原失败，不作为完成", True),
        "provider_chunks": field("Count", "收到的content分片数"),
        "persisted_chunks": field("Count", "已持久正文次数"),
    })
