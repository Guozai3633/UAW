# ProviderDraft

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

提供方类型对应的配置须通过profile schema，不能带明文secret。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 提供方 | 类型约束见对应对象 |
| `kind` | [ProviderKind](./ProviderKind.md) | 是 | 类型 | 类型约束见对应对象 |
| `endpoint` | [URL](./URL.md) | 否 | 管理员批准地址 | 类型约束见对应对象 |
| `profile_ref` | [ProviderProfileRef](./ProviderProfileRef.md) | 是 | 适配器配置schema | 类型约束见对应对象 |
| `settings` | [Object](./Object.md) | 是 | 按profile额外校验 | 类型约束见对应对象 |
| `credential_handle` | [ID](./ID.md) | 否 | 凭据库句柄 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "kind": {
            "enum": [
              "api",
              "model"
            ]
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "required": [
          "endpoint"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "kind": {
            "enum": [
              "runtime",
              "local"
            ]
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "not": {
          "required": [
            "endpoint"
          ]
        }
      }
    }
  ]
}
```

## 运行时约束

- api/model需要网络地址；runtime/local不接受网络地址；MCP HTTP或stdio的配置按固定profile独立校验，stdio执行不能把Runtime服务当任务沙箱。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "kind": "runtime",
  "profile_ref": {
    "kind": "provider_profile",
    "id": "example_001",
    "version": "example_001"
  },
  "settings": {}
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ProviderDraft`。
