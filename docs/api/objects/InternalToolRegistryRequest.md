# InternalToolRegistryRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

工具注册与版本的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `tool_id` | [ID](./ID.md) | 是 | 工具稳定名，固定version后才可以执行。 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 不可变工具/方法/对象版本，不作为单调整数比较。 | 类型约束见对应对象 |
| `spec` | [ToolSpec](./ToolSpec.md) | 是 | 已按固定schema声明的完整工具契约。 | 类型约束见对应对象 |
| `provider_ref` | [Ref](./Ref.md) | 是 | 管理员配置且当前可用的固定提供方版本。 | 类型约束见对应对象 |
| `expected_registry_revision` | [Revision](./Revision.md) | 是 | 工具目录CAS修订，发布后再更新派生索引。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- ToolSpec为权威；向量表示可重建，不能储存唯一schema或凭据。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "tool_id": "example_001",
  "version": "example_001",
  "spec": {
    "id": "example_001",
    "version": "example_001",
    "description": "example_001",
    "input_schema": {},
    "output_schema": {},
    "categories": [],
    "required_capabilities": [],
    "effect": "read",
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "retry_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  },
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_registry_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolRegistryRequest`。
