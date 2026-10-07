# CheckpointCaptureRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

只从各域已提交仓储取得版本，pending游标可缺省。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `committed_event_seq` | [Revision](./Revision.md) | 是 | 事件提交点 | 类型约束见对应对象 |
| `domain_refs` | [DomainRefMap](./DomainRefMap.md) | 是 | 跨域已提交版本 | 类型约束见对应对象 |
| `pending_call_cursor` | [Cursor](./Cursor.md) | 否 | 未决工具位置 | 类型约束见对应对象 |
| `schema_version` | [Version](./Version.md) | 是 | 格式 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "committed_event_seq": 0,
  "domain_refs": {},
  "schema_version": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CheckpointCaptureRequest`。
