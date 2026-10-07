# IntentOutputProposal

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

成果类型是描述，不是能力授权；描述必须逐字引用用户输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `kind` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `80` |
| `quote` | [IntentQuote](./IntentQuote.md) | 是 | 用户成果要求原文 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "kind": "example_001",
  "quote": {
    "source_index": 0,
    "start": 0,
    "end": 0,
    "text": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.IntentOutputProposal`。
