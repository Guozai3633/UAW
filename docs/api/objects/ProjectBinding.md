# ProjectBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

通过本地可信选择器绑定的项目，云端仅存根句柄。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 项目绑定 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 绑定版本 | 类型约束见对应对象 |
| `device_id` | [ID](./ID.md) | 是 | 设备 | 类型约束见对应对象 |
| `display_name` | [NonEmptyText](./NonEmptyText.md) | 是 | 展示名 | 类型约束见对应对象 |
| `root_handle` | [ID](./ID.md) | 是 | 本地根句柄 | 类型约束见对应对象 |
| `capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | read/write/exec批准范围 | 最少项 `0`；最多项 `256` |
| `state` | [ConnectionState](./ConnectionState.md) | 是 | 设备连接状态 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 路径字符串不能自行产生绑定；Runner对realpath与链接再次校验。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "device_id": "example_001",
  "display_name": "example_001",
  "root_handle": "example_001",
  "capabilities": [],
  "state": "disconnected"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ProjectBinding`。
