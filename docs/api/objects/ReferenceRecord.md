# ReferenceRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

引用登记不等于声称证据支持结论。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `ref` | [Ref](./Ref.md) | 是 | 稳定引用 | 类型约束见对应对象 |
| `title` | [NonEmptyText](./NonEmptyText.md) | 是 | 人可读标题 | 类型约束见对应对象 |
| `source_url` | [URL](./URL.md) | 否 | 获准网页原URL | 类型约束见对应对象 |
| `content_ref` | [Ref](./Ref.md) | 是 | 实际读取的内容 | 类型约束见对应对象 |
| `retrieved_at` | [Timestamp](./Timestamp.md) | 是 | 读取时间 | 类型约束见对应对象 |
| `provenance_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 来源链 | 最少项 `0`；最多项 `256` |
| `access_scope` | [Scope](./Scope.md) | 是 | 服务端授权范围 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "title": "example_001",
  "content_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "retrieved_at": "2026-10-07T02:00:00Z",
  "provenance_refs": [],
  "access_scope": {
    "principal_id": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ReferenceRecord`。
