# BaseState

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

输入基础版本：提交、当前目录快照或成果。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 快照 | 类型约束见对应对象 |
| `kind` | [BaseKind](./BaseKind.md) | 是 | 来源方式 | 类型约束见对应对象 |
| `source_ref` | [Ref](./Ref.md) | 是 | 来源 | 类型约束见对应对象 |
| `manifest` | [Manifest](./Manifest.md) | 是 | 收录内容 | 类型约束见对应对象 |
| `include_rules` | [IncludeRules](./IncludeRules.md) | 是 | 明确收录策略 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 采集时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "kind": "commit",
  "source_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "manifest": {
    "version": "example_001",
    "input_refs": [],
    "dependency_refs": [],
    "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "include_rules": {
    "include_uncommitted": true,
    "include_untracked": true,
    "include_paths": [],
    "exclude_paths": [],
    "max_total_bytes": 0
  },
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.BaseState`。
