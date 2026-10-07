# IngestionRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

资料发布与索引版本必须一致。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 摄取作业 | 类型约束见对应对象 |
| `source_ref` | [Ref](./Ref.md) | 是 | 原材料 | 类型约束见对应对象 |
| `parser_version` | [Version](./Version.md) | 是 | 解析器版本 | 类型约束见对应对象 |
| `chunk_profile` | [ID](./ID.md) | 是 | 切分参数 | 类型约束见对应对象 |
| `embedding_profile` | [ID](./ID.md) | 是 | 向量模型/配置 | 类型约束见对应对象 |
| `active_revision` | [Revision](./Revision.md) | 是 | 已发布索引 | 类型约束见对应对象 |
| `chunk_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 发布块 | 最少项 `0`；最多项 `256` |
| `status` | [IngestionState](./IngestionState.md) | 是 | 摄取作业状态；published才成为可检索active版本。 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 失败原因 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "source_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "parser_version": "example_001",
  "chunk_profile": "example_001",
  "embedding_profile": "example_001",
  "active_revision": 0,
  "chunk_refs": [],
  "status": "pending"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.IngestionRecord`。
