# admin.providers.revoke

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：配置与共享基础设施。

撤销提供方，固定旧配置不能绕过当前撤销。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`DELETE /v1/admin/providers/{provider_id}`；认证：`admin`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[AdminProvidersRevokeRequest](../objects/AdminProvidersRevokeRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `provider_id` | [ID](../objects/ID.md) | 是 | 提供方 |

## 输出

[HttpAdminProvidersRevokeResult](../objects/HttpAdminProvidersRevokeResult.md) 为完整返回结构。`kind=ok` 的payload是 [ProviderBinding](../objects/ProviderBinding.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 提供方绑定 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 配置版本 |
| `kind` | [ProviderKind](../objects/ProviderKind.md) | 是 | 适配器种类 |
| `state` | [ConnectionState](../objects/ConnectionState.md) | 是 | 当前状态 |
| `config_ref` | [Ref](../objects/Ref.md) | 是 | 非秘密配置 |
| `credential_ref` | [Ref](../objects/Ref.md) | 否 | 密钥库句柄 |
| `account_connection_ref` | [Ref](../objects/Ref.md) | 否 | 用户账号授权 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`admin`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 管理员认证与expected_revision必需；不撤销已发生的外部动作。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "provider_id": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "revision": 0,
    "kind": "runtime",
    "state": "disconnected",
    "config_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
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
