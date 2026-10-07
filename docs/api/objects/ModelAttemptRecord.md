# ModelAttemptRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

每次真实发送的固定配置、原始响应引用与观察用量；秘密不进入记录。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 尝试 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `invocation_id` | [ID](./ID.md) | 是 | 逻辑调用 | 类型约束见对应对象 |
| `actual_config` | [ResolvedModelConfig](./ResolvedModelConfig.md) | 是 | 固定实际配置 | 类型约束见对应对象 |
| `state` | [NonEmptyText](./NonEmptyText.md) | 是 | dispatched、received或failed | 类型约束见对应对象 |
| `usage` | [Usage](./Usage.md) | 否 | 实际观察 | 类型约束见对应对象 |
| `response_ref` | [Ref](./Ref.md) | 否 | 完整成功HTTP响应 | 类型约束见对应对象 |
| `output_ref` | [Ref](./Ref.md) | 否 | 完整模型文本 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 脱敏错误 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 发送意图时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "run_id": "example_001",
  "invocation_id": "example_001",
  "actual_config": {
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
  "state": "prepared",
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelAttemptRecord`。
