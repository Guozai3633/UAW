# BoardEntry

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

版本化共享结果，不存所有Agent私有思维。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `key` | [ID](./ID.md) | 是 | 条目键 | 类型约束见对应对象 |
| `result_ref` | [Ref](./Ref.md) | 是 | 候选/确认结果 | 类型约束见对应对象 |
| `status` | [BoardStatus](./BoardStatus.md) | 是 | 确认程度 | 类型约束见对应对象 |
| `provenance` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 证据来源 | 最少项 `0`；最多项 `256` |
| `input_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 结果依赖版本 | 最少项 `0`；最多项 `256` |
| `revision` | [Revision](./Revision.md) | 是 | 条目修订 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "key": "example_001",
  "result_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "status": "candidate",
  "provenance": [],
  "input_refs": [],
  "revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.BoardEntry`。
