# InstalledLaunchView

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

原网页会话拥有的本机实例进度；ready只表示原生回调与当前根来源完成，不授予文件工具权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 原启动身份 | 类型约束见对应对象 |
| `request_id` | [ID](./ID.md) | 是 | 原RequestMeta.request_id | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 状态持久CAS版本 | 类型约束见对应对象 |
| `state` | enum: `starting` / `waiting_device` / `connecting` / `selecting_directory` / `ready` / `closed` / `failed` / `unavailable` | 是 | 实际生命周期 | — |
| `workspace_ref` | [Ref](./Ref.md) | 是 | 管理员安装配置中的逻辑工作区；不是本机路径 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 原启动时间 | 类型约束见对应对象 |
| `updated_at` | [Timestamp](./Timestamp.md) | 是 | 本次状态时间 | 类型约束见对应对象 |
| `enrollment_id` | [ID](./ID.md) | 否 | 原设备登记 | 类型约束见对应对象 |
| `device_ref` | [Ref](./Ref.md) | 否 | 当前实际通道绑定的设备版本与摘要 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 否 | 原通道期限，不从轮询重新计时 | 类型约束见对应对象 |
| `failure_code` | [ID](./ID.md) | 否 | 有界错误码；不输出路径/proof/凭据 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "state": {
            "const": "ready"
          }
        },
        "required": [
          "state"
        ]
      },
      "then": {
        "required": [
          "device_ref",
          "expires_at",
          "enrollment_id"
        ]
      }
    }
  ]
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "request_id": "example_001",
  "revision": 0,
  "state": "starting",
  "workspace_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "created_at": "2026-10-07T02:00:00Z",
  "updated_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InstalledLaunchView`。
