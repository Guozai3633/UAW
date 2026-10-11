# FileRunSourceBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

Run准入固定原浏览器实例、只读根证据及用户模型；不是权限缓存或可提交的授权。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 原Run | 类型约束见对应对象 |
| `owner` | [Principal](./Principal.md) | 是 | 原完整网页主体 | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 是 | 原会话 | 类型约束见对应对象 |
| `task_id` | [ID](./ID.md) | 是 | 原任务 | 类型约束见对应对象 |
| `configuration_ref` | [Ref](./Ref.md) | 是 | 固定配置 | 类型约束见对应对象 |
| `model_policy_ref` | [Ref](./Ref.md) | 是 | 固定用户模型政策 | 类型约束见对应对象 |
| `fixed_model_id` | [ID](./ID.md) | 是 | 固定用户模型 | 类型约束见对应对象 |
| `provider_ref` | [Ref](./Ref.md) | 是 | 原只读提供方 | 类型约束见对应对象 |
| `launch_id` | [ID](./ID.md) | 是 | 原本机实例 | 类型约束见对应对象 |
| `workspace_ref` | [Ref](./Ref.md) | 是 | 原工作区 | 类型约束见对应对象 |
| `device_ref` | [Ref](./Ref.md) | 是 | 当前设备版本摘要 | 类型约束见对应对象 |
| `root_identity_hash` | [Hash](./Hash.md) | 是 | 原根证据摘要，无目录或正文 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 原根最早期限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "owner": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "conversation_id": "example_001",
  "task_id": "example_001",
  "configuration_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "model_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "fixed_model_id": "example_001",
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "launch_id": "example_001",
  "workspace_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "device_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "root_identity_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "expires_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.FileRunSourceBinding`。
