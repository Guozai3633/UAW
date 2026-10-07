# IntentQuote

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

逐字引文，坐标是Python/Unicode码点半开区间[start,end)，不是UTF8字节。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `source_index` | [Count](./Count.md) | 是 | 0原文，其余按补充顺序 | 类型约束见对应对象 |
| `start` | [Count](./Count.md) | 是 | 起始码点 | 类型约束见对应对象 |
| `end` | [Count](./Count.md) | 是 | 结束码点 | 类型约束见对应对象 |
| `text` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `16384` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "source_index": 0,
  "start": 0,
  "end": 0,
  "text": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.IntentQuote`。
