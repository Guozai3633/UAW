# RunInputApplication

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

原模型实际消费补充的不可变证据；不是执行授权。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_id` | [ID](./ID.md) | 是 | 原Run | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 实际模型输入版本 | ≥ `1`；类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 原模型attempt | 类型约束见对应对象 |
| `context_snapshot_ref` | [Ref](./Ref.md) | 是 | 实际调用固定上下文 | 类型约束见对应对象 |
| `model_output_ref` | [Ref](./Ref.md) | 是 | 实际完成模型输出 | 类型约束见对应对象 |
| `decision_record_ref` | [Ref](./Ref.md) | 是 | 所属有效Agent决策 | 类型约束见对应对象 |
| `source_input_refs` | 数组&lt;[UserInputRef](./UserInputRef.md)&gt; | 是 | 原文及全部实际消费补充 | 最少项 `2`；最多项 `17`；去重 `True` |
| `patch_input_refs` | 数组&lt;[UserInputRef](./UserInputRef.md)&gt; | 是 | 本事务从accepted变applied的原Input | 最少项 `1`；最多项 `16`；去重 `True` |
| `applied_at` | [Timestamp](./Timestamp.md) | 是 | 可信服务提交时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 只有原ModelInvocation/Output/LoopOperation与快照、当前输入/来源和已登记decision全部一致才标生效。
- patch、不可变应用证据、Run版本及Outbox同事务；重读/重启不重复应用，不更新ModelOutput或旧输入。
- 不创建预算、权限、续期、唤醒或自动接受；仅证明原模型已消费。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "protocol": "conversation-v1",
  "run_id": "run_1",
  "input_revision": 2,
  "attempt_id": "model_attempt_2",
  "context_snapshot_ref": {
    "kind": "context",
    "id": "snapshot_2",
    "version": "1"
  },
  "model_output_ref": {
    "kind": "content",
    "id": "output_2",
    "version": "1"
  },
  "decision_record_ref": {
    "kind": "content",
    "id": "model_attempt_2",
    "version": "1"
  },
  "source_input_refs": [
    {
      "kind": "input",
      "id": "input_create_roles",
      "version": "1"
    },
    {
      "kind": "input",
      "id": "input_answer_2",
      "version": "1"
    }
  ],
  "patch_input_refs": [
    {
      "kind": "input",
      "id": "input_answer_2",
      "version": "1"
    }
  ],
  "applied_at": "2026-10-16T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunInputApplication`。
