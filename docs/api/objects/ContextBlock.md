# ContextBlock

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

分区、溯源、可裁剪的模型输入块。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 输入块 | 类型约束见对应对象 |
| `kind` | [BlockKind](./BlockKind.md) | 是 | 指令/材料/历史/结果 | 类型约束见对应对象 |
| `source_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际来源 | 最少项 `0`；最多项 `256` |
| `content_ref` | [Ref](./Ref.md) | 是 | 内容 | 类型约束见对应对象 |
| `estimated_tokens` | [Count](./Count.md) | 是 | 估算Token | 类型约束见对应对象 |
| `required` | [Bool](./Bool.md) | 是 | 是否禁止丢弃 | 类型约束见对应对象 |
| `trust` | [TrustLevel](./TrustLevel.md) | 是 | 指令可信度 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "kind": "instruction",
  "source_refs": [],
  "content_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "estimated_tokens": 0,
  "required": true,
  "trust": "platform"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ContextBlock`。
