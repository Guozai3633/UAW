# TurnsSubmitRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

提交原文并受理Run。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `conversation_id` | [ID](./ID.md) | 是 | 会话 | 类型约束见对应对象 |
| `text` | [Text](./Text.md) | 是 | 用户原文 | 类型约束见对应对象 |
| `attachment_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 附件 | 最少项 `0`；最多项 `256` |
| `task_id` | [ID](./ID.md) | 否 | 继续已有任务 | 类型约束见对应对象 |
| `expected_task_revision` | [Revision](./Revision.md) | 否 | 继续任务必需 | 类型约束见对应对象 |
| `budget` | [Budget](./Budget.md) | 否 | 用户预算上限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## anyOf结构规则

```json
{
  "anyOf": [
    {
      "properties": {
        "text": {
          "minLength": 1
        }
      }
    },
    {
      "properties": {
        "attachment_refs": {
          "minItems": 1
        }
      }
    }
  ]
}
```

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "required": [
          "task_id"
        ]
      },
      "then": {
        "required": [
          "expected_task_revision"
        ]
      }
    }
  ]
}
```

## 运行时约束

- 同request_id+相同规范请求重放返回原Run；同键不同原文冲突；输入正文或附件至少一个非空。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "conversation_id": "conversation_1",
  "text": "帮我检查这次API修改的兼容性，运行已有测试，保留我的未提交修改。",
  "attachment_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.TurnsSubmitRequest`。
