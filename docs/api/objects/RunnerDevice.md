# RunnerDevice

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

Runner在线状态与本机可执行能力。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `device_id` | [ID](./ID.md) | 是 | 设备 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 注册版本 | 类型约束见对应对象 |
| `display_name` | [NonEmptyText](./NonEmptyText.md) | 是 | 名称 | 类型约束见对应对象 |
| `state` | [ConnectionState](./ConnectionState.md) | 是 | 状态 | 类型约束见对应对象 |
| `capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 执行能力 | 最少项 `0`；最多项 `256` |
| `last_seen_at` | [Timestamp](./Timestamp.md) | 是 | 最近心跳 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "device_id": "example_001",
  "revision": 0,
  "display_name": "example_001",
  "state": "disconnected",
  "capabilities": [],
  "last_seen_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerDevice`。
