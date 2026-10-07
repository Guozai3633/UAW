# EffectRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

外部写账本记录意图、尝试和对账。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `action_id` | [ID](./ID.md) | 是 | 逻辑动作 | 类型约束见对应对象 |
| `arguments_hash` | [Hash](./Hash.md) | 是 | 规范参数摘要 | 类型约束见对应对象 |
| `provider_ref` | [Ref](./Ref.md) | 是 | 真实提供方 | 类型约束见对应对象 |
| `business_key` | [NonEmptyText](./NonEmptyText.md) | 否 | 外部业务幂等键 | 类型约束见对应对象 |
| `attempt_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 所有实际尝试 | 最少项 `0`；最多项 `256` |
| `state` | [EffectState](./EffectState.md) | 是 | 效果是否已确认 | 类型约束见对应对象 |
| `receipt_ref` | [Ref](./Ref.md) | 否 | 外部回执 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 账本版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action_id": "example_001",
  "arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "attempt_ids": [],
  "state": "confirmed",
  "revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.EffectRecord`。
