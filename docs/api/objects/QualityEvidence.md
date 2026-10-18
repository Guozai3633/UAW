# QualityEvidence

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。



[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `kind` | enum: `provided_material` / `primary_source` | 是 | 见类型说明 | — |
| `locator` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `16384` |
| `captured_at` | string | 是 | 见类型说明 | 最少字符 `20`；最多字符 `40` |
| `text` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `65536` |
| `sha256` | string | 是 | 见类型说明 | 正则 `^[0-9a-f]{64}$` |
| `url` | 至少一个分支 | 否 | 见类型说明 | 默认注解 `None` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 原来源/回答版本绑定；认证用户独立判断，未知不当作通过。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "kind": "provided_material",
  "locator": "example_001",
  "captured_at": "example_001xxxxxxxxx",
  "text": "example_001",
  "sha256": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.QualityEvidence`。
