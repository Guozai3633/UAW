# InternalAgentDefinitionsDiscoveryRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

会话Agent发现的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `conversation_id` | [ID](./ID.md) | 是 | 当前获准会话，服务校验与可信上下文一致。 | 类型约束见对应对象 |
| `task_goal` | [Text](./Text.md) | 是 | 当前目标摘要，仅用于候选排序，不覆盖原文。 | 类型约束见对应对象 |
| `role_constraints` | 数组&lt;[Text](./Text.md)&gt; | 是 | 任务所需职责与不能进行的动作。 | 最多项 `256` |
| `max_candidates` | integer | 是 | 一次最多提供候选数，减少模型输入而不授予权限。 | ≥ `1`；≤ `64` |
| `definitions_revision` | [Revision](./Revision.md) | 是 | 候选角色目录修订，用于缓存及失效。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 候选仅诊断/缓存派生；发现不创建实例、不批权限。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "conversation_id": "example_001",
  "task_goal": "example_001",
  "role_constraints": [],
  "max_candidates": 1,
  "definitions_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentDefinitionsDiscoveryRequest`。
