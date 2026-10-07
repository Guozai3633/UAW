# ApprovalPolicy

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

三模式在现有权限内应用规则。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 政策 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 修订 | 类型约束见对应对象 |
| `default_mode` | [ApprovalMode](./ApprovalMode.md) | 是 | 默认模式 | 类型约束见对应对象 |
| `allowed_modes` | 数组&lt;[ApprovalMode](./ApprovalMode.md)&gt; | 是 | 可选模式 | 最少项 `0`；最多项 `256` |
| `rules` | 数组&lt;[ApprovalRule](./ApprovalRule.md)&gt; | 是 | 审批要求 | 最少项 `0`；最多项 `256` |
| `reviewer_profile_ref` | [Ref](./Ref.md) | 否 | 辅助审查配置 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 模式不能覆盖require_user的高影响规则；审批结果必须签名来源，模型建议不能自批。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "default_mode": "assisted",
  "allowed_modes": [],
  "rules": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ApprovalPolicy`。
