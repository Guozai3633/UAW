# InternalAgentCollaborationHandoffRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

可选控制权交接的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `from_agent_ref` | [Ref](./Ref.md) | 是 | 移交前当前控制实例，必须持有有效租约。 | 类型约束见对应对象 |
| `to_agent_ref` | [Ref](./Ref.md) | 是 | 同任务树且有匹配角色/权限的目标实例。 | 类型约束见对应对象 |
| `expected_control_revision` | [Revision](./Revision.md) | 是 | 控制租约域CAS版本，防止双控制者。 | 类型约束见对应对象 |
| `unfinished_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 移交给新控制者的未完工作与待定状态引用。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- Agent拥有唯一ControlLease，Run保存恢复引用。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "from_agent_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "to_agent_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_control_revision": 0,
  "unfinished_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCollaborationHandoffRequest`。
