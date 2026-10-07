# RunnerPairing

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

配对凭据仅用户与Runner交互，禁止进入模型。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `pairing_id` | [ID](./ID.md) | 是 | 配对事务 | 类型约束见对应对象 |
| `verification_code` | [NonEmptyText](./NonEmptyText.md) | 是 | 短期一次码 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 截止 | 类型约束见对应对象 |
| `approval_url` | [URL](./URL.md) | 是 | 用户确认入口 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "pairing_id": "example_001",
  "verification_code": "example_001",
  "expires_at": "2026-10-07T02:00:00Z",
  "approval_url": "https://example.org/resource"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerPairing`。
