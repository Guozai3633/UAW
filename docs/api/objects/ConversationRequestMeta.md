# ConversationRequestMeta

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

新对话控制专用元信息；不能提交给旧0.1入口。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `request_id` | [ID](./ID.md) | 是 | 同一逻辑补充提交保持不变 | 类型约束见对应对象 |
| `schema_version` | 常量 `0.2` | 是 | 新控制HTTP版本 | — |
| `expected_revision` | [Revision](./Revision.md) | 是 | 原Run预期修订，必需且从1开始 | ≥ `1`；类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "request_id": "example_001",
  "schema_version": "0.2",
  "expected_revision": 1
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ConversationRequestMeta`。
