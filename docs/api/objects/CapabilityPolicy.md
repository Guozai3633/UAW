# CapabilityPolicy

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

有效权限交集上限，配置不等于新用户授权。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 政策 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 修订 | 类型约束见对应对象 |
| `allowed_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 允许能力 | 最少项 `0`；最多项 `256` |
| `denied_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 显式禁止 | 最少项 `0`；最多项 `256` |
| `resource_scope` | [ScopeSelector](./ScopeSelector.md) | 是 | 资源范围 | 类型约束见对应对象 |
| `network_allowlist` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 批准网络域 | 最少项 `0`；最多项 `256` |
| `feature_flag_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 能力开关 | 最少项 `0`；最多项 `256` |
| `parent_policy_ref` | [Ref](./Ref.md) | 否 | 父政策 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- deny优先；子策略只能收窄；Runner执行能力还须本机实际批准。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "allowed_capabilities": [],
  "denied_capabilities": [],
  "resource_scope": {
    "conversation_id": "example_001"
  },
  "network_allowlist": [],
  "feature_flag_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CapabilityPolicy`。
