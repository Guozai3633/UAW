# IntentReceipt

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

理解提交与事件同事务保存的幂等回执。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `request_hash` | [Hash](./Hash.md) | 是 | 请求与可信关联摘要 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 源版本 | 类型约束见对应对象 |
| `frame_ref` | [Ref](./Ref.md) | 是 | 提交版本 | 类型约束见对应对象 |
| `result` | [Object](./Object.md) | 是 | 已验证的Runtime结果 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "request_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "run_id": "example_001",
  "input_revision": 0,
  "frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "result": {}
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.IntentReceipt`。
