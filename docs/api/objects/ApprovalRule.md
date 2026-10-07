# ApprovalRule

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

可匹配动作的审批规则。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 规则 | 类型约束见对应对象 |
| `effects` | 数组&lt;[EffectKind](./EffectKind.md)&gt; | 是 | 效果类别 | 最少项 `0`；最多项 `256` |
| `capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 能力 | 最少项 `0`；最多项 `256` |
| `scope` | [ScopeSelector](./ScopeSelector.md) | 是 | 适用范围 | 类型约束见对应对象 |
| `require_user` | [Bool](./Bool.md) | 是 | 必须用户决定 | 类型约束见对应对象 |
| `allow_assisted_review` | [Bool](./Bool.md) | 是 | 是否可辅助审查 | 类型约束见对应对象 |
| `max_grant_duration_ms` | [Duration](./Duration.md) | 是 | 授权有效期上限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "effects": [],
  "capabilities": [],
  "scope": {
    "conversation_id": "example_001"
  },
  "require_user": true,
  "allow_assisted_review": true,
  "max_grant_duration_ms": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ApprovalRule`。
