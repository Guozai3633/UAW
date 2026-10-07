# Transition

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

内部状态转移提案。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `from_state` | [RunStatus](./RunStatus.md) | 是 | 预期原状态 | 类型约束见对应对象 |
| `to_state` | [RunStatus](./RunStatus.md) | 是 | 目标状态 | 类型约束见对应对象 |
| `reason` | [NonEmptyText](./NonEmptyText.md) | 是 | 转移依据 | 类型约束见对应对象 |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 真实证据 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "from_state": "queued",
  "to_state": "queued",
  "reason": "example_001",
  "evidence_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Transition`。
