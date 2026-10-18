# QualityObservation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。



[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `schema_version` | 常量 `ms-e1.v1` | 是 | 见类型说明 | — |
| `manifest_id` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `case_id` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `case_version` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `attempt_id` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `logical_request_id` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `attempt_number` | integer | 是 | 见类型说明 | ≥ `1`；≤ `4096` |
| `phase` | enum: `answer` / `reviewer` / `tool` / `preparation` | 是 | 见类型说明 | — |
| `status` | enum: `succeeded` / `failed` / `cancelled` / `unknown` | 是 | 见类型说明 | — |
| `started_at` | string | 是 | 见类型说明 | 最少字符 `20`；最多字符 `40` |
| `finished_at` | string | 是 | 见类型说明 | 最少字符 `20`；最多字符 `40` |
| `active_ms` | integer | 是 | 见类型说明 | ≥ `0`；≤ `1000000000000000000` |
| `wall_ms` | integer | 是 | 见类型说明 | ≥ `0`；≤ `1000000000000000000` |
| `usage` | [QualityUsage](./QualityUsage.md) | 是 | 见类型说明 | 类型约束见对应对象 |
| `output` | 至少一个分支 | 是 | 见类型说明 | — |
| `reviewer` | 至少一个分支 | 是 | 见类型说明 | — |
| `failure_code` | 至少一个分支 | 是 | 见类型说明 | — |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 原来源/回答版本绑定；认证用户独立判断，未知不当作通过。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "schema_version": "ms-e1.v1",
  "manifest_id": "example_001",
  "case_id": "example_001",
  "case_version": "example_001",
  "attempt_id": "example_001",
  "logical_request_id": "example_001",
  "attempt_number": 1,
  "phase": "answer",
  "status": "succeeded",
  "started_at": "example_001xxxxxxxxx",
  "finished_at": "example_001xxxxxxxxx",
  "active_ms": 0,
  "wall_ms": 0,
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "model_calls": 0,
    "tool_calls": 0,
    "money": "0",
    "currency": "CNY",
    "billing_state": "confirmed"
  },
  "output": {
    "decision": "reply",
    "text": "example_001",
    "evidence": []
  },
  "reviewer": {
    "target_attempt_id": "example_001",
    "target_output_sha256": "example_001",
    "verdict": "passed"
  },
  "failure_code": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.QualityObservation`。
