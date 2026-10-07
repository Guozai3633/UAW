# admin.secrets.put

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：配置与共享基础设施。

仅管理端TLS写入秘密，不回显不记录正文。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/admin/secrets`；认证：`admin`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[AdminSecretsPutRequest](../objects/AdminSecretsPutRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `provider_id` | [ID](../objects/ID.md) | 是 | 目标提供方 |
| `secret` | [SecretValue](../objects/SecretValue.md) | 是 | 待加密值 |

## 输出

[HttpAdminSecretsPutResult](../objects/HttpAdminSecretsPutResult.md) 为完整返回结构。`kind=ok` 的payload是 [SecretReceipt](../objects/SecretReceipt.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `credential_handle` | [ID](../objects/ID.md) | 是 | 秘密句柄 |
| `version` | [Version](../objects/Version.md) | 是 | 秘密版本 |

## 约束与提交

- 效果分类：`credential`。
- 认证/上下文：`admin`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 日志/缓存/trace禁止记录secret；前端与模型不可读取秘密。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "meta": {
    "request_id": "request_001",
    "schema_version": "0.1",
    "expected_revision": 0
  },
  "payload": {
    "provider_id": "example_001",
    "secret": "EXAMPLE_ONLY_SECRET"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "credential_handle": "example_001",
    "version": "example_001"
  },
  "output_refs": []
}
```

## 拒绝结构示例

```json
{
  "kind": "denied",
  "output_refs": [],
  "failure": {
    "code": "permission_denied",
    "category": "authorization",
    "message": "当前主体没有本动作所需权限。",
    "retryable": false,
    "failed_phase": "policy_gate",
    "recover_hint": "取得真实授权后重新检查；不能通过换工具绕过。"
  }
}
```

## 模块与目录

| 节点 | 详细策略 | 计划代码位置 |
| --- | --- | --- |
| `support.configuration` | [开发设计](../../../docs/design/components/support-configuration.md) | `src/uaw/shared/configuration.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
