# ConversationPatch

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

至少一个字段，删除项目用显式detach。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `title` | [NonEmptyText](./NonEmptyText.md) | 否 | 新标题 | 类型约束见对应对象 |
| `model_choice` | [ConversationModelChoice](./ConversationModelChoice.md) | 否 | 新模型 | 类型约束见对应对象 |
| `memory_policy` | [MemoryPolicy](./MemoryPolicy.md) | 否 | 记忆设置 | 类型约束见对应对象 |
| `project_ref` | [Ref](./Ref.md) | 否 | 新项目 | 类型约束见对应对象 |
| `detach_project` | [Bool](./Bool.md) | 否 | 解除绑定 | 类型约束见对应对象 |
| `approval_mode` | [ApprovalMode](./ApprovalMode.md) | 否 | 审批模式修订，在下一安全边界生效。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## not结构规则

```json
{
  "not": {
    "required": [
      "project_ref",
      "detach_project"
    ]
  }
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "title": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ConversationPatch`。
