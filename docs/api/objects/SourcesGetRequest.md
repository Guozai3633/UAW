# SourcesGetRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

读取当前资料摄取、解析与发布状态。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `task_id` | [ID](./ID.md) | 是 | 任务 | 类型约束见对应对象 |
| `source_id` | [ID](./ID.md) | 是 | 材料ID | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 未发布时chunk_refs不供检索；pending状态只说明作业已受理。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "task_id": "example_001",
  "source_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.SourcesGetRequest`。
