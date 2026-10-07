# AdminToolsRegisterRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

注册工具schema与提供方。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `spec` | [ToolSpec](./ToolSpec.md) | 是 | 工具版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 检查schema合法、唯一版本、提供方可用；向量索引异步构建且保持目录版本一致。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AdminToolsRegisterRequest`。
