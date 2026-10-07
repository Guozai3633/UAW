# ControlLease

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

写控制权有期限与栅栏，阻止过期执行者继续提交。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 租约ID | 类型约束见对应对象 |
| `holder_ref` | [Ref](./Ref.md) | 是 | 当前控制实例 | 类型约束见对应对象 |
| `resource_ref` | [Ref](./Ref.md) | 是 | 受控任务/节点 | 类型约束见对应对象 |
| `fencing_token` | [Revision](./Revision.md) | 是 | 单调栅栏 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 截止时间 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 控制域版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "holder_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "resource_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "fencing_token": 0,
  "expires_at": "2026-10-07T02:00:00Z",
  "revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ControlLease`。
