# DelegationSpec

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

一次有界委派；独立上下文，不共享可变提示词。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `goal` | [NonEmptyText](./NonEmptyText.md) | 是 | 当前委派目标 | 类型约束见对应对象 |
| `input_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 授权输入 | 最少项 `0`；最多项 `256` |
| `definition_ref` | [Ref](./Ref.md) | 否 | 固定角色版本 | 类型约束见对应对象 |
| `output_contract` | [Contract](./Contract.md) | 是 | 子成果验收标准 | 类型约束见对应对象 |
| `budget` | [Budget](./Budget.md) | 是 | 父预算内切分 | 类型约束见对应对象 |
| `read_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 允许读取范围请求 | 最少项 `0`；最多项 `256` |
| `write_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 允许修改范围请求 | 最少项 `0`；最多项 `256` |
| `creation_key` | [ID](./ID.md) | 是 | 委派幂等键 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 定义权限、父权限、产品旗标、设备权限求交；父预算必须先预留；默认继承父模型。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "goal": "example_001",
  "input_refs": [],
  "output_contract": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
  },
  "budget": {
    "limits": {
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0",
      "currency": "CNY"
    },
    "max_steps": 0,
    "max_depth": 0,
    "deadline": "2026-10-07T02:00:00Z"
  },
  "read_refs": [],
  "write_refs": [],
  "creation_key": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DelegationSpec`。
