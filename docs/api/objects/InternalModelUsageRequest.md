# InternalModelUsageRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

计量与版本记录的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `call_ref` | [Ref](./Ref.md) | 是 | 实际调用记录及固定参数版本。 | 类型约束见对应对象 |
| `provider_usage` | [Usage](./Usage.md) | 否 | 提供方报告的实际账单；无数据则pending而非0。 | 类型约束见对应对象 |
| `reserved_budget_ref` | [Ref](./Ref.md) | 是 | 本次模型调用对应预算预留。 | 类型约束见对应对象 |
| `actual_config_ref` | [Ref](./Ref.md) | 是 | 本次真实使用的模型配置，不能只记录用户希望的配置。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- Model拥有调用记录，Run Budget Ledger是预算余额权威；重复回执不能二次扣账。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "call_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "reserved_budget_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "actual_config_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalModelUsageRequest`。
