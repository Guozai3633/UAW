# ModelRegistration

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

管理员声明模型能力，修订由目录分配。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 稳定名称 | 类型约束见对应对象 |
| `provider_ref` | [Ref](./Ref.md) | 是 | 提供方 | 类型约束见对应对象 |
| `display_name` | [NonEmptyText](./NonEmptyText.md) | 是 | 展示名 | 类型约束见对应对象 |
| `context_limit_tokens` | [PositiveTokenCount](./PositiveTokenCount.md) | 是 | 窗口 | 类型约束见对应对象 |
| `output_limit_tokens` | [PositiveTokenCount](./PositiveTokenCount.md) | 是 | 输出上限 | 类型约束见对应对象 |
| `capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 能力 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "display_name": "example_001",
  "context_limit_tokens": 1,
  "output_limit_tokens": 1,
  "capabilities": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelRegistration`。
