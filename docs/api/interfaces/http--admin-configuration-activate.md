# admin.configuration.activate

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：配置与共享基础设施。

原子发布配置。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/admin/configuration/drafts/{configuration_id}/activate`；认证：`admin`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[AdminConfigurationActivateRequest](../objects/AdminConfigurationActivateRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `configuration_id` | [ID](../objects/ID.md) | 是 | 已验证草案 |

## 输出

[HttpAdminConfigurationActivateResult](../objects/HttpAdminConfigurationActivateResult.md) 为完整返回结构。`kind=ok` 的payload是 [ConfigurationVersion](../objects/ConfigurationVersion.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 配置域 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 版本 |
| `model_refs` | 数组&lt;[ModelRef](../objects/ModelRef.md)&gt; | 是 | 模型目录 |
| `provider_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 工具/搜索绑定 |
| `environment_template_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 环境模板 |
| `feature_flags` | 数组&lt;[FeatureFlag](../objects/FeatureFlag.md)&gt; | 是 | 能力开关 |
| `approval_policy_ref` | [Ref](../objects/Ref.md) | 是 | 审批政策 |
| `storage_policy_ref` | [Ref](../objects/Ref.md) | 是 | 存储部署政策 |
| `state` | [ProviderState](../objects/ProviderState.md) | 是 | 发布状态 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`admin`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- expected_revision；受影响发现索引和缓存失效，旧在途调用固定旧配置并受撤销闸门控制。
- HTTP meta.expected_revision必填且≥1；过期提交返回conflict，不能自动覆盖。

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
    "expected_revision": 3
  },
  "payload": {}
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "revision": 0,
    "model_refs": [],
    "provider_refs": [],
    "environment_template_refs": [],
    "feature_flags": [],
    "approval_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "storage_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "state": "draft"
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
