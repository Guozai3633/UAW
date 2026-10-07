# TraceSpan

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

脱敏链路观测；不保存密钥/私密思维链。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `trace_id` | [ID](./ID.md) | 是 | 链路 | 类型约束见对应对象 |
| `span_id` | [ID](./ID.md) | 是 | 片段 | 类型约束见对应对象 |
| `parent_span_id` | [ID](./ID.md) | 否 | 父片段 | 类型约束见对应对象 |
| `operation_id` | [ID](./ID.md) | 是 | 操作 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 否 | 执行尝试 | 类型约束见对应对象 |
| `domain_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 版本 | 最少项 `0`；最多项 `256` |
| `started_at` | [Timestamp](./Timestamp.md) | 是 | 开始 | 类型约束见对应对象 |
| `ended_at` | [Timestamp](./Timestamp.md) | 否 | 结束 | 类型约束见对应对象 |
| `usage_ref` | [Ref](./Ref.md) | 否 | 消耗 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 错误 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "trace_id": "example_001",
  "span_id": "example_001",
  "operation_id": "example_001",
  "domain_refs": [],
  "started_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.TraceSpan`。
