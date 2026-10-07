# ModelPolicyRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

模型政策必须来自明确用户意图或父政策。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `conversation_selection` | [ModelSelection](./ModelSelection.md) | 是 | 会话已记录意图 | 类型约束见对应对象 |
| `parent_policy_ref` | [Ref](./Ref.md) | 否 | 父政策 | 类型约束见对应对象 |
| `explicit_child_request` | [ModelRequest](./ModelRequest.md) | 否 | 子覆盖 | 类型约束见对应对象 |
| `user_source_ref` | [UserInputRef](./UserInputRef.md) | 是 | 真实用户依据 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "conversation_selection": {
    "mode": "inherit"
  },
  "user_source_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelPolicyRequest`。
