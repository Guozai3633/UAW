# InternalAgentCompletionAcceptanceRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

用户接受与迭代的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `review_set_ref` | [Ref](./Ref.md) | 是 | 固定成果/变更版本的用户审阅集合。 | 类型约束见对应对象 |
| `decision` | [DeliveryDecision](./DeliveryDecision.md) | 是 | 真实用户审阅决定；与模型语义核验区分。 | 类型约束见对应对象 |
| `feedback_ref` | [Ref](./Ref.md) | 否 | 用户针对当前成果的实际反馈。 | 类型约束见对应对象 |
| `expected_artifact_version` | [Version](./Version.md) | 是 | 用户审阅时所见成果版本，变化需重新审阅。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 用户接受的权威由Workspace保存，模型无权替用户填写。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "review_set_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "decision": "accept",
  "expected_artifact_version": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCompletionAcceptanceRequest`。
