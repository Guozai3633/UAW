# InstalledLaunchRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

内部持久启动历史；原完整Web主体不能由同账号新session替代，重启不恢复OS进程或授权。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `owner` | [Principal](./Principal.md) | 是 | 原完整Web主体 | 类型约束见对应对象 |
| `view` | [InstalledLaunchView](./InstalledLaunchView.md) | 是 | 无本机路径的进度 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "owner": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "view": {
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InstalledLaunchRecord`。
