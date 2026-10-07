# InternalIntentProbeRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

必要信息探查的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `missing_facts` | 数组&lt;[Text](./Text.md)&gt; | 是 | 影响任务执行但尚未知道的具体事实。 | 最多项 `256` |
| `allowed_scope` | [Scope](./Scope.md) | 是 | 有效权限交集内的允许范围，不能由发现结果扩大。 | 类型约束见对应对象 |
| `max_calls` | integer | 是 | 只读探查调用上限，必须在预留预算内。 | ≥ `1`；≤ `64` |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 绝对UTC截止；重试和子调用不能延长父deadline。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 保存证据引用和探查结果，不修改用户目标或外部状态。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "missing_facts": [],
  "allowed_scope": {
    "principal_id": "example_001"
  },
  "max_calls": 1,
  "deadline": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalIntentProbeRequest`。
