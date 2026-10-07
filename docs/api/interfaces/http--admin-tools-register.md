# admin.tools.register

状态：契约0.1，待实现。类别：用户与管理端 HTTP API。所属：工具运行。

注册工具schema与提供方。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/admin/tools`；认证：`admin`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[AdminToolsRegisterRequest](../objects/AdminToolsRegisterRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `spec` | [ToolSpec](../objects/ToolSpec.md) | 是 | 工具版本 |

## 输出

[HttpAdminToolsRegisterResult](../objects/HttpAdminToolsRegisterResult.md) 为完整返回结构。`kind=ok` 的payload是 [ToolSpec](../objects/ToolSpec.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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
- 认证/上下文：`admin`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 检查schema合法、唯一版本、提供方可用；向量索引异步构建且保持目录版本一致。

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
    }
  }
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
