# InternalIntentOriginalRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

原文读取的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `original_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 获准且不可变的原始用户输入；不得指向模型摘要。 | 类型约束见对应对象 |
| `user_patch_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 运行中追加的用户要求版本，原文不覆盖。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 只读原文，不维护第二份可修改账本；纠正必须先成为新的用户输入记录。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "original_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "user_patch_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalIntentOriginalRequest`。
