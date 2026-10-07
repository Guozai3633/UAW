# tool.mcp.provider

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

提供方绑定的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolMcpProviderRequest, context: TrustedExecutionContext) -> ComponentToolMcpProviderResult`。所属入口为 `tool.mcp.provider`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolMcpProviderRequest](../objects/InternalToolMcpProviderRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `provider_ref` | [Ref](../objects/Ref.md) | 是 | 管理员配置且当前可用的固定提供方版本。 |
| `account_connection_ref` | [Ref](../objects/Ref.md) | 是 | 用户批准的外部账号连接，须仍active且范围符合。 |
| `expected_config_revision` | [Revision](../objects/Revision.md) | 是 | 连接/提供方预期配置修订；变化重新读取。 |

## 输出

[ComponentToolMcpProviderResult](../objects/ComponentToolMcpProviderResult.md) 为完整返回结构。`kind=ok` 的payload是 [ProviderBinding](../objects/ProviderBinding.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 不复制账号授权到账本作为永久许可。
- 读取当前平台启用状态和私人账号授权
- 校验数据范围、可用凭据引用与传输限制
- 固定普通配置版本，当前撤销单独检查
- 输出仅可连接配置给会话层
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 账号过期返回reauth_required
- 提供方未启用拒绝

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "account_connection_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_config_revision": 0
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
| `tool.mcp.provider` | [开发设计](../../../docs/design/components/tool-mcp-provider.md) | `src/uaw/tool/mcp/provider.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
