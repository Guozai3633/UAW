# InternalContextMemoryPolicyRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

范围与写入政策的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `memory_policy_ref` | [Ref](./Ref.md) | 是 | 当前记忆读取/贡献/范围/保留政策。 | 类型约束见对应对象 |
| `candidate_ref` | [Ref](./Ref.md) | 是 | 尚未确认的记忆/结果候选版本。 | 类型约束见对应对象 |
| `target_scope` | [Scope](./Scope.md) | 是 | 候选记忆/资源生效范围，只能在当前权限内缩小。 | 类型约束见对应对象 |
| `retention` | [Duration](./Duration.md) | 否 | 记忆保留毫秒数，最终由有效政策限定。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 政策版本记录，不把候选文字当授权。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "memory_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "candidate_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "target_scope": {
    "principal_id": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalContextMemoryPolicyRequest`。
