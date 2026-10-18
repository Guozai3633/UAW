# ConversationStreamRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

原模型调用的未完成正文检查点，不授予执行或完成。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 原invocation ID | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 流记录CAS | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | 原Run | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 是 | 原会话 | 类型约束见对应对象 |
| `operation_id` | [ID](./ID.md) | 是 | 原Agent operation | 类型约束见对应对象 |
| `item_id` | [ID](./ID.md) | 是 | 原稳定消息 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 原输入版本 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 实际提供方attempt | 类型约束见对应对象 |
| `snapshot_ref` | [Ref](./Ref.md) | 是 | 原上下文 | 类型约束见对应对象 |
| `model_config` | [ResolvedModelConfig](./ResolvedModelConfig.md) | 是 | 原模型配置 | 类型约束见对应对象 |
| `state` | enum: `receiving` / `received` / `interrupted` / `published` | 是 | 生命周期 | — |
| `text` | [Text](./Text.md) | 是 | 只含允许展示的普通回复前缀 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 创建时刻 | 类型约束见对应对象 |
| `updated_at` | [Timestamp](./Timestamp.md) | 是 | 最新检查点时刻 | 类型约束见对应对象 |
| `first_provider_at` | [Timestamp](./Timestamp.md) | 否 | 首content，不含推理 | 类型约束见对应对象 |
| `first_text_at` | [Timestamp](./Timestamp.md) | 否 | 首可展示正文 | 类型约束见对应对象 |
| `first_committed_at` | [Timestamp](./Timestamp.md) | 否 | 首次正文事务COMMIT返回后的观察时刻，后续检查点保存；进程突失时可缺失 | 类型约束见对应对象 |
| `received_at` | [Timestamp](./Timestamp.md) | 否 | 原响应收齐时刻 | 类型约束见对应对象 |
| `provider_started_at` | [Timestamp](./Timestamp.md) | 否 | 适配器开始实际HTTP请求 | 类型约束见对应对象 |
| `provider_headers_at` | [Timestamp](./Timestamp.md) | 否 | 收到提供方HTTP头 | 类型约束见对应对象 |
| `provider_first_content_at` | [Timestamp](./Timestamp.md) | 否 | 收到首个实际content delta，持久化之前 | 类型约束见对应对象 |
| `provider_last_content_at` | [Timestamp](./Timestamp.md) | 否 | 收到最后实际content delta，持久化之前 | 类型约束见对应对象 |
| `provider_ended_at` | [Timestamp](./Timestamp.md) | 否 | 适配器退出时刻，可能失败或取消 | 类型约束见对应对象 |
| `output_ref` | [Ref](./Ref.md) | 否 | 原模型输出 | 类型约束见对应对象 |
| `failure_code` | [ID](./ID.md) | 否 | 原失败，不作为完成 | 类型约束见对应对象 |
| `provider_chunks` | [Count](./Count.md) | 是 | 收到的content分片数 | 类型约束见对应对象 |
| `persisted_chunks` | [Count](./Count.md) | 是 | 已持久正文次数 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "run_id": "example_001",
  "conversation_id": "example_001",
  "operation_id": "example_001",
  "item_id": "example_001",
  "input_revision": 0,
  "attempt_id": "example_001",
  "snapshot_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "model_config": {
    "model_id": "example_001",
    "catalog_revision": 0,
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "max_output_tokens": 0
  },
  "state": "receiving",
  "text": "example_001",
  "created_at": "2026-10-07T02:00:00Z",
  "updated_at": "2026-10-07T02:00:00Z",
  "provider_chunks": 0,
  "persisted_chunks": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ConversationStreamRecord`。
