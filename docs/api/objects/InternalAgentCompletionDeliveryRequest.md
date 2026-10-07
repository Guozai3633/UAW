# InternalAgentCompletionDeliveryRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

提交交付的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `proposal_ref` | [Ref](./Ref.md) | 是 | 已经核对版本/证据的完成提案。 | 类型约束见对应对象 |
| `expected_run_revision` | [Revision](./Revision.md) | 是 | Run状态CAS修订，过期执行者不能推进新状态。 | 类型约束见对应对象 |
| `artifact_manifest_ref` | [Ref](./Ref.md) | 是 | 本次交付成果的不可变清单。 | 类型约束见对应对象 |
| `proposed_outcome` | [Outcome](./Outcome.md) | 是 | 建议结果；代码完成闸门验证后才提交终态。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 终态与必要事件本地事务提交；外部公开发布另走Tool。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "proposal_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_run_revision": 0,
  "artifact_manifest_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "proposed_outcome": "succeeded"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCompletionDeliveryRequest`。
