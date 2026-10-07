# AgentDefinitionVersion

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

已提交角色版本。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `definition_id` | [ID](./ID.md) | 是 | 定义ID | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 单调版本 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 不可变摘要 | 类型约束见对应对象 |
| `owner_id` | [ID](./ID.md) | 是 | 真实用户 | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 是 | 绑定会话 | 类型约束见对应对象 |
| `draft` | [AgentDefinitionDraft](./AgentDefinitionDraft.md) | 是 | 保存配置 | 类型约束见对应对象 |
| `status` | enum: `enabled` / `disabled` / `pending_resolution` | 是 | 可调用状态 | — |
| `source_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 用户来源 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 提交时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "definition_id": "example_001",
  "revision": 0,
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "owner_id": "example_001",
  "conversation_id": "example_001",
  "draft": {
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
  },
  "status": "enabled",
  "source_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentDefinitionVersion`。
