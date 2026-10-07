# McpTransportConfig

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

协议适配配置，不包含秘密或任意任务代码。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 配置 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 固定版本 | 类型约束见对应对象 |
| `transport` | [McpTransport](./McpTransport.md) | 是 | HTTP或stdio | 类型约束见对应对象 |
| `endpoint` | [URL](./URL.md) | 否 | HTTP地址 | 类型约束见对应对象 |
| `launcher_template_ref` | [Ref](./Ref.md) | 否 | 管理员批准的stdio启动模板 | 类型约束见对应对象 |
| `credential_ref` | [Ref](./Ref.md) | 否 | 秘密库句柄 | 类型约束见对应对象 |
| `protocol_version` | [Version](./Version.md) | 是 | 协议配置 | 类型约束见对应对象 |
| `timeout_ms` | [Duration](./Duration.md) | 是 | 超时 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "properties": {
        "transport": {
          "const": "http"
        }
      },
      "required": [
        "endpoint"
      ],
      "not": {
        "required": [
          "launcher_template_ref"
        ]
      }
    },
    {
      "properties": {
        "transport": {
          "const": "stdio"
        }
      },
      "required": [
        "launcher_template_ref"
      ],
      "not": {
        "required": [
          "endpoint"
        ]
      }
    }
  ]
}
```

## 运行时约束

- HTTP需endpoint；stdio需launcher_template_ref且不执行模型构造的任意命令；敏感headers由适配器注入。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "transport": "http",
  "protocol_version": "example_001",
  "timeout_ms": 0,
  "endpoint": "https://example.org/resource"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.McpTransportConfig`。
