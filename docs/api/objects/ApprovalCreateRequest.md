# ApprovalCreateRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

创建固定动作审批。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `action_id` | [ID](./ID.md) | 是 | 动作 | 类型约束见对应对象 |
| `arguments_hash` | [Hash](./Hash.md) | 是 | 参数 | 类型约束见对应对象 |
| `resource_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 资源 | 最少项 `0`；最多项 `256` |
| `effect` | [EffectKind](./EffectKind.md) | 是 | 效果 | 类型约束见对应对象 |
| `summary` | [NonEmptyText](./NonEmptyText.md) | 是 | 可读行为 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 截止 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action_id": "example_001",
  "arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "resource_refs": [],
  "effect": "read",
  "summary": "example_001",
  "expires_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ApprovalCreateRequest`。
