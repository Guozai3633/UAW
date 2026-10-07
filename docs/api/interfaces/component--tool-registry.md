# tool.registry

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

工具注册与版本的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolRegistryRequest, context: TrustedExecutionContext) -> ComponentToolRegistryResult`。所属入口为 `tool.registry`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolRegistryRequest](../objects/InternalToolRegistryRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `tool_id` | [ID](../objects/ID.md) | 是 | 工具稳定名，固定version后才可以执行。 |
| `version` | [Version](../objects/Version.md) | 是 | 不可变工具/方法/对象版本，不作为单调整数比较。 |
| `spec` | [ToolSpec](../objects/ToolSpec.md) | 是 | 已按固定schema声明的完整工具契约。 |
| `provider_ref` | [Ref](../objects/Ref.md) | 是 | 管理员配置且当前可用的固定提供方版本。 |
| `expected_registry_revision` | [Revision](../objects/Revision.md) | 是 | 工具目录CAS修订，发布后再更新派生索引。 |

## 输出

[ComponentToolRegistryResult](../objects/ComponentToolRegistryResult.md) 为完整返回结构。`kind=ok` 的payload是 [ToolSpec](../objects/ToolSpec.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 稳定工具名 |
| `version` | [Version](../objects/Version.md) | 是 | 固定schema版本 |
| `description` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 用途、限制和适用条件 |
| `input_schema` | [Schema](../objects/Schema.md) | 是 | 参数schema |
| `output_schema` | [Schema](../objects/Schema.md) | 是 | 业务结果schema |
| `categories` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 类别 |
| `required_capabilities` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 权限需求 |
| `effect` | [EffectKind](../objects/EffectKind.md) | 是 | 效果类别 |
| `provider_ref` | [Ref](../objects/Ref.md) | 是 | 有效提供方 |
| `equivalence_contract_ref` | [Ref](../objects/Ref.md) | 否 | 严格等价替代约束 |
| `retry_policy_ref` | [Ref](../objects/Ref.md) | 是 | 恢复上限 |
| `feature_flag` | [ID](../objects/ID.md) | 否 | 产品开关 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- ToolSpec为权威；向量表示可重建，不能储存唯一schema或凭据。
- 校验schema、效果类别、权限、超时、幂等与等价声明
- 平台启用提供方后注册不可变spec
- 生成只含允许元数据的关键词/向量表示
- 索引发布绑定tool_id/version，发现阶段复核权威记录
- 关闭/撤销先拒绝执行，再异步清理索引
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 重复同版本不同hash拒绝
- schema不兼容返回registration_invalid
- 索引滞后显式记录不破坏执行授权

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "tool_id": "example_001",
  "version": "example_001",
  "spec": {
    "id": "example_001",
    "version": "example_001",
    "description": "example_001",
    "input_schema": {},
    "output_schema": {},
    "categories": [],
    "required_capabilities": [],
    "effect": "read",
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "retry_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  },
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_registry_revision": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "version": "example_001",
    "description": "example_001",
    "input_schema": {},
    "output_schema": {},
    "categories": [],
    "required_capabilities": [],
    "effect": "read",
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "retry_policy_ref": {
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
| `tool.registry` | [开发设计](../../../docs/design/components/tool-registry.md) | `src/uaw/tool/registry.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
