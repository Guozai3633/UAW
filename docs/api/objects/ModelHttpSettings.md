# ModelHttpSettings

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

首批HTTP模型配置profile；注册不意味着完成连通或协议适配。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `model_name` | [NonEmptyText](./NonEmptyText.md) | 是 | 提供方模型名称 | 类型约束见对应对象 |
| `timeout_ms` | [Duration](./Duration.md) | 是 | 超时 | ≥ `1000`；≤ `300000`；类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "model_name": "example_001",
  "timeout_ms": 1000
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelHttpSettings`。
