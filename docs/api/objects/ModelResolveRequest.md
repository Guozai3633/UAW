# ModelResolveRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

把用户指定名称解析为可用目录ID。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `requested_name` | [NonEmptyText](./NonEmptyText.md) | 是 | 用户指定 | 类型约束见对应对象 |
| `source_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 来源 | 类型约束见对应对象 |
| `required_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 要求 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "requested_name": "example_001",
  "source_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "required_capabilities": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelResolveRequest`。
