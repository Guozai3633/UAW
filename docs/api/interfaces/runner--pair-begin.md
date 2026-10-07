# pair.begin

状态：契约0.1，待实现。类别：本地 Runner 协议。所属：工作区与交付。

本机用户启动配对。

[分类索引](../RUNNER.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

配对/本地选择是专用可信交互；执行类消息走 `RunnerCommand` 信封，其中request_ref解析为下方输入。服务签名和本机范围/权限均有效才执行，响应回传ComponentResult，不能把进程启动当成完成。

## 输入

[RunnerPairBeginRequest](../objects/RunnerPairBeginRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `device_nonce` | [ID](../objects/ID.md) | 是 | 一次随机标识 |
| `display_name` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 本机名称 |
| `capabilities` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 实际能力 |

## 输出

[RunnerPairBeginResult](../objects/RunnerPairBeginResult.md) 为完整返回结构。`kind=ok` 的payload是 [RunnerPairing](../objects/RunnerPairing.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `pairing_id` | [ID](../objects/ID.md) | 是 | 配对事务 |
| `verification_code` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 短期一次码 |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 是 | 截止 |
| `approval_url` | [URL](../objects/URL.md) | 是 | 用户确认入口 |

## 约束与提交

- 效果分类：`credential`。
- 认证/上下文：`runner`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 未配对无项目访问权；一次码只经用户账户页面确认。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "device_nonce": "example_001",
  "display_name": "example_001",
  "capabilities": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "pairing_id": "example_001",
    "verification_code": "example_001",
    "expires_at": "2026-10-07T02:00:00Z",
    "approval_url": "https://example.org/resource"
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
| `workspace.binding` | [开发设计](../../../docs/design/components/workspace-binding.md) | `src/uaw/workspace/binding.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
