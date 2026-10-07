# UnderstandingRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

首次理解，可复用主Agent同次输出。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `original_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 原文 | 类型约束见对应对象 |
| `user_patch_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 补充 | 最少项 `0`；最多项 `256` |
| `material_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 资料 | 最少项 `0`；最多项 `256` |
| `expected_revision` | [Revision](./Revision.md) | 是 | 理解CAS | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "original_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "user_patch_refs": [],
  "material_refs": [],
  "expected_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.UnderstandingRequest`。
