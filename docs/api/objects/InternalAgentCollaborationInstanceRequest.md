# InternalAgentCollaborationInstanceRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

隔离运行实例的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `definition_ref` | [Ref](./Ref.md) | 是 | 可用且绑定当前会话的固定角色定义版本。 | 类型约束见对应对象 |
| `delegation_ref` | [Ref](./Ref.md) | 是 | 目标、资料、验收与预算已经固定的委派契约。 | 类型约束见对应对象 |
| `parent_agent_ref` | [Ref](./Ref.md) | 是 | 父实例必须同一任务树且仍拥有有效权限/预算。 | 类型约束见对应对象 |
| `creation_key` | [Text](./Text.md) | 是 | 重复创建同一输入返回已有实例；不同输入相同键冲突。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 实例状态与定义分开，复用定义不复用scratch。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "definition_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "delegation_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "parent_agent_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "creation_key": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCollaborationInstanceRequest`。
