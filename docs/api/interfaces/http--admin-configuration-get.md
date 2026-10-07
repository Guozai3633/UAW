# admin.configuration.get

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：配置与共享基础设施。

有效配置。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`GET /v1/admin/configuration`；认证：`admin`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[AdminConfigurationGetRequest](../objects/AdminConfigurationGetRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |

## 输出

[HttpAdminConfigurationGetResult](../objects/HttpAdminConfigurationGetResult.md) 为完整返回结构。`kind=ok` 的payload是 [ConfigurationVersion](../objects/ConfigurationVersion.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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

- 效果分类：`read`。
- 认证/上下文：`admin`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{}
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
