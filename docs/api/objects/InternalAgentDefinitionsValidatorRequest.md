# InternalAgentDefinitionsValidatorRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

定义与授权校验的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `draft` | [AgentDefinitionDraft](./AgentDefinitionDraft.md) | 是 | 待校验草案，不是已授权可运行实例。 | 类型约束见对应对象 |
| `user_source_ref` | [UserInputRef](./UserInputRef.md) | 是 | 授权/创建/模型覆盖来源，必须是真实用户行为。 | 类型约束见对应对象 |
| `effective_scope` | [Scope](./Scope.md) | 是 | 父、角色、产品、设备权限求交后的真实范围。 | 类型约束见对应对象 |
| `existing_names` | 数组&lt;[Text](./Text.md)&gt; | 是 | 已占用角色名称，按规范化唯一规则比对。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- ValidatedDraft不是enabled定义，必须交Repository提交。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
  "user_source_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "effective_scope": {
    "principal_id": "example_001"
  },
  "existing_names": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentDefinitionsValidatorRequest`。
