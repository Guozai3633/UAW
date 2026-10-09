# CompletionAcceptance

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

独立认证用户对确切成果版本的审阅记录。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `bundle_ref` | [Ref](./Ref.md) | 是 | 确切不可变交付Bundle | 类型约束见对应对象 |
| `principal` | [Principal](./Principal.md) | 是 | 真实认证用户 | 类型约束见对应对象 |
| `decision` | [DeliveryDecision](./DeliveryDecision.md) | 是 | 用户决定 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 实际登记时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 当前入口只登记一次；只有accept可满足需要用户接受的合同，拒绝/修订/部分接受不完成Run。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "bundle_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "principal": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "decision": "accept",
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CompletionAcceptance`。
