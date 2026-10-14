# RunClarificationAnswerRequest

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

原Run回答；身份和expected_run_revision来自meta。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 路径中的原Run | 类型约束见对应对象 |
| `question_item_id` | [ID](./ID.md) | 是 | 路径中原问题稳定Item | 类型约束见对应对象 |
| `expected_question_revision` | [Revision](./Revision.md) | 是 | 问题预期CAS版本 | ≥ `1`；类型约束见对应对象 |
| `expected_input_revision` | [Revision](./Revision.md) | 是 | 原有效输入版本 | ≥ `1`；类型约束见对应对象 |
| `text` | [Text](./Text.md) | 是 | 用户真实回答 | 类型约束见对应对象 |
| `attachment_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 本人获准材料，真实权限另查 | 最少项 `0`；最多项 `16`；去重 `True` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## anyOf结构规则

```json
{
  "anyOf": [
    {
      "properties": {
        "text": {
          "minLength": 1,
          "pattern": "\\S"
        }
      },
      "required": [
        "text"
      ]
    },
    {
      "properties": {
        "attachment_refs": {
          "minItems": 1
        }
      },
      "required": [
        "attachment_refs"
      ]
    }
  ]
}
```

## 运行时约束

- 请求+附件总字节有界；客户端引用不赋予权限；真实同用户会话、Run/问题/输入CAS、幂等和终态/取消复核。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "question_item_id": "example_001",
  "expected_question_revision": 1,
  "expected_input_revision": 1,
  "text": "example_001",
  "attachment_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunClarificationAnswerRequest`。
