# DefinitionPatch

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

可修改配置的白名单字段，省略表示不变，null不默认删除。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `name` | [NonEmptyText](./NonEmptyText.md) | 否 | 新名 | 类型约束见对应对象 |
| `description` | [NonEmptyText](./NonEmptyText.md) | 否 | 新职责 | 类型约束见对应对象 |
| `instructions` | [NonEmptyText](./NonEmptyText.md) | 否 | 新方法 | 类型约束见对应对象 |
| `use_when` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 否 | 新条件 | 最少项 `0`；最多项 `32` |
| `avoid_when` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 否 | 新排除 | 最少项 `0`；最多项 `32` |
| `skill_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 否 | 替换技能列表 | 最少项 `0`；最多项 `32` |
| `tool_categories` | 数组&lt;[ID](./ID.md)&gt; | 否 | 新能力请求 | 最少项 `0`；最多项 `64` |
| `output_contract` | [Contract](./Contract.md) | 否 | 新验收 | 类型约束见对应对象 |
| `model_request` | [ModelRequest](./ModelRequest.md) | 否 | 用户明确模型修订 | 类型约束见对应对象 |
| `enabled` | [Bool](./Bool.md) | 否 | 启停 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 至少一个字段；模型/权限变动须有效用户来源；CAS提交。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "name": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DefinitionPatch`。
