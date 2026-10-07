# ProjectsBindRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

绑定可信选择器结果。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `device_id` | [ID](./ID.md) | 是 | 设备 | 类型约束见对应对象 |
| `selection_token` | [NonEmptyText](./NonEmptyText.md) | 是 | Runner签发一次根选择凭据 | 类型约束见对应对象 |
| `display_name` | [NonEmptyText](./NonEmptyText.md) | 是 | 名称 | 类型约束见对应对象 |
| `requested_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | read/write/exec | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 根不由网页任意path字符串指定；一次凭据绑定当前用户和设备；批准后能力只能缩窄。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "device_id": "example_001",
  "selection_token": "example_001",
  "display_name": "example_001",
  "requested_capabilities": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ProjectsBindRequest`。
