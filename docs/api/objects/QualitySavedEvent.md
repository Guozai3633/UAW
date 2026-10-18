# QualitySavedEvent

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

独立质量记录的事务审计，不是任务完成事件。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `review_id` | [ID](./ID.md) | 是 | 审阅包 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 审阅修订 | 类型约束见对应对象 |
| `auth_session_id` | [ID](./ID.md) | 是 | 认证会话 | 类型约束见对应对象 |
| `basis` | enum: `human_evidence_review` / `controlled_test` | 是 | 判断来源 | — |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "review_id": "example_001",
  "revision": 0,
  "auth_session_id": "example_001",
  "basis": "human_evidence_review"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.QualitySavedEvent`。
