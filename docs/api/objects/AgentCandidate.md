# AgentCandidate

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

可见角色摘要，不加载全部方法。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `definition_ref` | [Ref](./Ref.md) | 是 | 固定版本 | 类型约束见对应对象 |
| `name` | [NonEmptyText](./NonEmptyText.md) | 是 | 名称 | 类型约束见对应对象 |
| `description` | [NonEmptyText](./NonEmptyText.md) | 是 | 职责 | 类型约束见对应对象 |
| `use_when` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 调用条件 | 最少项 `0`；最多项 `32` |
| `avoid_when` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 排除 | 最少项 `0`；最多项 `32` |
| `available` | [Bool](./Bool.md) | 是 | 当前可用摘要，调用仍复核 | 类型约束见对应对象 |
| `output_contract_ref` | [Ref](./Ref.md) | 是 | 验收契约 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "definition_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "name": "example_001",
  "description": "example_001",
  "use_when": [],
  "avoid_when": [],
  "available": true,
  "output_contract_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentCandidate`。
