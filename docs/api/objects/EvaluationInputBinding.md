# EvaluationInputBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

有界评估输入；固定用户模型且不递归展开Context。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 原评估操作身份 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 不可变输入版本 | 类型约束见对应对象 |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 可信完整运行关联 | 类型约束见对应对象 |
| `frame_ref` | [Ref](./Ref.md) | 是 | 实际TaskFrame版本和摘要 | 类型约束见对应对象 |
| `role_ref` | [Ref](./Ref.md) | 是 | 实际角色版本 | 类型约束见对应对象 |
| `sources` | 数组&lt;[EvaluationSourcePin](./EvaluationSourcePin.md)&gt; | 是 | 实际对象来源 | 最少项 `0`；最多项 `128` |
| `instruction` | [NonEmptyText](./NonEmptyText.md) | 是 | 评估职责指令 | 类型约束见对应对象 |
| `data` | [Object](./Object.md) | 是 | TaskFrame与该职责的候选内容 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 总输入最多96KiB；读取和派发前复查当前来源。模型输出不授予权限。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
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
  "role_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "sources": [],
  "instruction": "example_001",
  "data": {}
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.EvaluationInputBinding`。
