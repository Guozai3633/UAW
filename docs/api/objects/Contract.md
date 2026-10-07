# Contract

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

语义目标+结构+证据契约，不写死行业字段。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `goal` | [NonEmptyText](./NonEmptyText.md) | 是 | 目标 | 类型约束见对应对象 |
| `requirements` | 数组&lt;[Requirement](./Requirement.md)&gt; | 是 | 验收条件 | 最少项 `0`；最多项 `128` |
| `outputs` | 数组&lt;[OutputSpec](./OutputSpec.md)&gt; | 是 | 交付物要求 | 最少项 `0`；最多项 `32` |
| `version` | [Version](./Version.md) | 是 | 契约版本 | 类型约束见对应对象 |
| `acceptance_required` | [Bool](./Bool.md) | 否 | Task结束是否需用户接受 | 默认注解 `False`；类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "goal": "example_001",
  "requirements": [],
  "outputs": [],
  "version": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Contract`。
