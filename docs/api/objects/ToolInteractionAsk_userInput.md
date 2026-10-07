# ToolInteractionAsk_userInput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

提出必要澄清并挂起等待。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `question` | [NonEmptyText](./NonEmptyText.md) | 是 | 自包含问题 | 类型约束见对应对象 |
| `options` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 否 | 简短选项 | 最少项 `0`；最多项 `256` |
| `blocking` | [Bool](./Bool.md) | 是 | 答案是否执行前提 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 批准动作走ApprovalRequest；澄清不能伪造授权，超时不等于答案。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "question": "example_001",
  "blocking": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolInteractionAsk_userInput`。
