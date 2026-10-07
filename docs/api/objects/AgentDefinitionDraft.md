# AgentDefinitionDraft

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

用户要求持久保存的角色草案。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `client_definition_key` | [ID](./ID.md) | 是 | 批量每项稳定幂等键 | 类型约束见对应对象 |
| `name` | string | 是 | 会话内唯一名称 | 最少字符 `1`；最多字符 `80` |
| `description` | [NonEmptyText](./NonEmptyText.md) | 是 | 短职责 | 类型约束见对应对象 |
| `instructions` | [NonEmptyText](./NonEmptyText.md) | 是 | 短工作指令 | 类型约束见对应对象 |
| `use_when` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 语义调用条件 | 最少项 `1`；最多项 `32` |
| `avoid_when` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 排除条件 | 最少项 `0`；最多项 `32` |
| `skill_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 获准技能依赖 | 最少项 `0`；最多项 `32` |
| `tool_categories` | 数组&lt;[ID](./ID.md)&gt; | 是 | 能力类别请求 | 最少项 `0`；最多项 `64` |
| `input_contract` | [Contract](./Contract.md) | 是 | 必要输入及缺口语义 | 类型约束见对应对象 |
| `output_contract` | [Contract](./Contract.md) | 是 | 子结果验收 | 类型约束见对应对象 |
| `model_request` | [ModelRequest](./ModelRequest.md) | 是 | 模型意图，默认显式填写inherit | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 不含owner/conversation/approved；服务注入，角色不能授予新权限；临时分工不得自动持久保存。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
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
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentDefinitionDraft`。
