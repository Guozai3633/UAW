# ApprovalsDecideRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

用户审批。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `approval_id` | [ID](./ID.md) | 是 | 审批 | 类型约束见对应对象 |
| `decision` | [ApprovalDecision](./ApprovalDecision.md) | 是 | 批准范围 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- expected_revision必需；参数/资源版本不一致返回stale；不能从LLM参数approved读取授权。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "approval_id": "example_001",
  "decision": {
    "decision": "approve_once",
    "expected_arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "expected_resource_refs": [],
    "reason": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ApprovalsDecideRequest`。
