# support.configuration

状态：契约0.1，待实现。类别：细分组件私有接口。所属：配置与共享基础设施。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalSupportConfigurationRequest, context: TrustedExecutionContext) -> ComponentSupportConfigurationResult`。所属入口为 `support.configuration`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalSupportConfigurationRequest](../objects/InternalSupportConfigurationRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalSupportConfigurationRequestStage](../objects/InternalSupportConfigurationRequestStage.md)
- [InternalSupportConfigurationRequestActivate](../objects/InternalSupportConfigurationRequestActivate.md)
- [InternalSupportConfigurationRequestConnect](../objects/InternalSupportConfigurationRequestConnect.md)
- [InternalSupportConfigurationRequestRevoke](../objects/InternalSupportConfigurationRequestRevoke.md)

## 输出

[ComponentSupportConfigurationResult](../objects/ComponentSupportConfigurationResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalSupportConfigurationOutput](../objects/InternalSupportConfigurationOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 凭据存在受控CredentialStore，普通配置仅引用；管理API不进入Agent工具目录。
- 管理员发布模型/搜索/提供方/环境/政策配置
- 私人账号连接由用户明确授权，配置身份与执行身份分开
- 校验引用与配置兼容后生成不可变snapshot
- Runtime固定常规版本并实时核验撤销/限额
- 失效通知目录、绑定与缓存
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 无管理员权限拒绝平台改动
- 账号撤销立即禁调用
- 过期配置CAS冲突返回现态

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "stage",
  "parameters": {
    "configuration": {
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
    "action": "stage",
    "result": {
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
