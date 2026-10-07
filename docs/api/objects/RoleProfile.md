# RoleProfile

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

平台角色能力上限，可与用户子Agent定义组合。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 角色ID | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 不可变版本 | 类型约束见对应对象 |
| `description` | [NonEmptyText](./NonEmptyText.md) | 是 | 职责 | 类型约束见对应对象 |
| `instructions_ref` | [Ref](./Ref.md) | 是 | 方法来源 | 类型约束见对应对象 |
| `tool_categories` | 数组&lt;[ID](./ID.md)&gt; | 是 | 工具类别上限 | 最少项 `0`；最多项 `256` |
| `skill_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 技能候选 | 最少项 `0`；最多项 `256` |
| `output_contract` | [Contract](./Contract.md) | 是 | 角色验收 | 类型约束见对应对象 |
| `model_capability_requirements` | [CapabilityRequirements](./CapabilityRequirements.md) | 否 | 可选角色能力要求，固定模型不满足时反馈，不能暗换。 | 类型约束见对应对象 |
| `auto_model_candidates` | 数组&lt;[ID](./ID.md)&gt; | 否 | 仅Auto已授权时进一步收窄候选，explicit/inherit不使用此列表替换模型。 | 最少项 `0`；最多项 `64` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "description": "example_001",
  "instructions_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "tool_categories": [],
  "skill_refs": [],
  "output_contract": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RoleProfile`。
