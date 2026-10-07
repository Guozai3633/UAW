# DraftPreview

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

发送前只读理解提示；发送后不得冒充已执行。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `draft_revision` | [Revision](./Revision.md) | 是 | 对应草稿 | 类型约束见对应对象 |
| `interpretation` | [Interpretation](./Interpretation.md) | 是 | 提示 | 类型约束见对应对象 |
| `model_config_ref` | [Ref](./Ref.md) | 是 | 实际模型 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 提示有效期 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "draft_revision": 0,
  "interpretation": {
    "goal": "example_001",
    "assumptions": [],
    "source_refs": [],
    "missing_facts": []
  },
  "model_config_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expires_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DraftPreview`。
