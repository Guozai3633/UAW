# BoardCommitRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

候选共享结果CAS。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `entry_key` | [ID](./ID.md) | 是 | 条目 | 类型约束见对应对象 |
| `result_ref` | [Ref](./Ref.md) | 是 | 结果 | 类型约束见对应对象 |
| `expected_board_revision` | [Revision](./Revision.md) | 是 | 共享板版本 | 类型约束见对应对象 |
| `provenance` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 来源 | 最少项 `0`；最多项 `256` |
| `status` | [BoardStatus](./BoardStatus.md) | 是 | 候选/确认 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "entry_key": "example_001",
  "result_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_board_revision": 0,
  "provenance": [],
  "status": "candidate"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.BoardCommitRequest`。
