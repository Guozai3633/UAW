# ApprovalDecision

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

由用户或批准的审查服务签发，LLM工具参数不含批准结果。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `decision` | [ApprovalDecisionKind](./ApprovalDecisionKind.md) | 是 | 单次/限定持续/拒绝/取消 | 类型约束见对应对象 |
| `expected_arguments_hash` | [Hash](./Hash.md) | 是 | 对应动作参数 | 类型约束见对应对象 |
| `expected_resource_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 对应版本 | 最少项 `0`；最多项 `256` |
| `scope_selector` | [ScopeSelector](./ScopeSelector.md) | 否 | 限定持续范围 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 否 | 持续授权截止 | 类型约束见对应对象 |
| `reason` | [Text](./Text.md) | 是 | 理由 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "decision": {
            "const": "approve_scoped"
          }
        },
        "required": [
          "decision"
        ]
      },
      "then": {
        "required": [
          "scope_selector",
          "expires_at"
        ]
      }
    }
  ]
}
```

## 运行时约束

- approve_scoped必需范围和有效期；不能批准原主体没有的权限；审批后必须recheck。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "decision": "approve_once",
  "expected_arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "expected_resource_refs": [],
  "reason": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ApprovalDecision`。
