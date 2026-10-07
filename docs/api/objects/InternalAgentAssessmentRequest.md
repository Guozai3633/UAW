# InternalAgentAssessmentRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

按需执行评估的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `task_frame_ref` | [Ref](./Ref.md) | 是 | 当前任务理解，包含原文和明确约束来源。 | 类型约束见对应对象 |
| `capability_snapshot` | [Ref](./Ref.md) | 是 | 当前有效能力及旗标版本，用于缩小候选。 | 类型约束见对应对象 |
| `existing_agent_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 当前可用实例/角色摘要，避免无必要新增Agent。 | 最多项 `256` |
| `decision_question` | [Text](./Text.md) | 否 | 需要本次复评的具体问题，避免重做全部理解。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- Assessment是建议记录，不直接创建实例或把全部步骤标记ready。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "task_frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "capability_snapshot": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "existing_agent_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentAssessmentRequest`。
