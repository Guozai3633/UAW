# DefinitionsCreateRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

保存角色。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `conversation_id` | [ID](./ID.md) | 是 | 会话 | 类型约束见对应对象 |
| `definitions` | [DefinitionDrafts](./DefinitionDrafts.md) | 是 | 批量草案 | 类型约束见对应对象 |
| `batch_policy` | [BatchPolicy](./BatchPolicy.md) | 是 | atomic或independent | 类型约束见对应对象 |
| `source_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 用户明确创建依据 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 不会启动实例；显式模型缺失返回needs_resolution；会话名唯一；幂等client_definition_key。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "conversation_id": "example_001",
  "definitions": [
    {
      "client_definition_key": "example_001",
      "name": "example_001",
      "description": "example_001",
      "instructions": "example_001",
      "use_when": [
        "example_001"
      ],
      "avoid_when": [],
      "skill_refs": [],
      "tool_categories": [],
      "input_contract": {
        "goal": "example_001",
        "requirements": [],
        "outputs": [],
        "version": "example_001"
      },
      "output_contract": {
        "goal": "example_001",
        "requirements": [],
        "outputs": [],
        "version": "example_001"
      },
      "model_request": {
        "mode": "inherit"
      }
    }
  ],
  "batch_policy": "atomic",
  "source_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DefinitionsCreateRequest`。
