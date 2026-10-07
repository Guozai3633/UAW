# MemoryRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

保存记忆及依赖。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 记忆 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 版本 | 类型约束见对应对象 |
| `content` | [MemoryContent](./MemoryContent.md) | 是 | 内容 | 类型约束见对应对象 |
| `scope` | [Scope](./Scope.md) | 是 | 有效范围 | 类型约束见对应对象 |
| `policy_ref` | [Ref](./Ref.md) | 是 | 写入依据 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 保存时间 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 否 | 有效期 | 类型约束见对应对象 |
| `deleted_at` | [Timestamp](./Timestamp.md) | 否 | 逻辑删除时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "content": {
    "text": "example_001",
    "kind": "preference",
    "source_refs": []
  },
  "scope": {
    "principal_id": "example_001"
  },
  "policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.MemoryRecord`。
