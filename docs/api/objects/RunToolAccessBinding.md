# RunToolAccessBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

可信控制入口登记的Run/Agent工具角色绑定；不是模型可提交的授权。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 实际Run | 类型约束见对应对象 |
| `agent_id` | [ID](./ID.md) | 否 | 单个Agent槽位 | 类型约束见对应对象 |
| `principal` | [Principal](./Principal.md) | 是 | 完整用户与认证会话 | 类型约束见对应对象 |
| `scope` | [Scope](./Scope.md) | 是 | 固定执行范围 | 类型约束见对应对象 |
| `model_policy_ref` | [Ref](./Ref.md) | 是 | 固定用户模型 | 类型约束见对应对象 |
| `capability_policy_ref` | [Ref](./Ref.md) | 是 | 实际权限版本 | 类型约束见对应对象 |
| `role_ref` | [Ref](./Ref.md) | 是 | 实际角色版本及摘要 | 类型约束见对应对象 |
| `environment` | [ID](./ID.md) | 是 | 部署环境 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | CAS版本 | 类型约束见对应对象 |
| `state` | [NonEmptyText](./NonEmptyText.md) | 是 | active或revoked | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 仅内部已认证controller可登记/撤销；HTTP和模型工具不接受此对象。
- Run/Agent槽位、完整Principal/session、scope和固定政策逐次匹配。
- 角色类别不授权资源，不替换固定模型；当前Run/权限/配置/提供方均须复查。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "principal": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "scope": {
    "principal_id": "example_001"
  },
  "model_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "capability_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "role_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "environment": "example_001",
  "revision": 0,
  "state": "active"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunToolAccessBinding`。
