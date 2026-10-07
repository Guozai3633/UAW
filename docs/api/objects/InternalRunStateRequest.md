# InternalRunStateRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

Run 与交互项的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 当前Run，主体及会话关联由服务核验。 | 类型约束见对应对象 |
| `expected_revision` | [Revision](./Revision.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 | 类型约束见对应对象 |
| `transition` | [Transition](./Transition.md) | 是 | 明确from/to状态与真实依据，须满足状态白名单。 | 类型约束见对应对象 |
| `item_patch` | [ItemPatch](./ItemPatch.md) | 否 | 按base_revision应用的交互项增量/替换。 | 类型约束见对应对象 |
| `completion_proposal_ref` | [Ref](./Ref.md) | 否 | Completion Controller的当前成果完成提案。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 本地RunState+关键Event事务提交；外部效果通过Tool账本关联不假定分布式原子。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "expected_revision": 0,
  "transition": {
    "from_state": "queued",
    "to_state": "queued",
    "reason": "example_001",
    "evidence_refs": []
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalRunStateRequest`。
