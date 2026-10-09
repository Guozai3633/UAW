# ArtifactSourceBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

实际文本成果的原模型输出及工具观察归属。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 可信完整运行关联 | 类型约束见对应对象 |
| `frame_ref` | [Ref](./Ref.md) | 是 | 原TaskFrame | 类型约束见对应对象 |
| `model_output_ref` | [Ref](./Ref.md) | 是 | 已完成实际ModelOutput | 类型约束见对应对象 |
| `observation_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际工具观察 | 最少项 `0`；最多项 `128` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 与ArtifactRecord原子登记；只支持最多64KiB的实际UTF-8文本或Markdown。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "context": {
    "principal": {
      "id": "example_001",
      "kind": "user",
      "auth_session_id": "example_001"
    },
    "scope": {
      "principal_id": "example_001"
    },
    "operation_id": "example_001",
    "trace_id": "example_001",
    "attempt_id": "example_001",
    "deadline": "2026-10-07T02:00:00Z",
    "capability_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  },
  "frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "model_output_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "observation_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ArtifactSourceBinding`。
