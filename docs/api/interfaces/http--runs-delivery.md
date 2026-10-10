# runs.delivery

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：运行与会话。

读取本人Run的最新真实固定交付；无交付返回missing。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`GET /v1/runs/{run_id}/delivery`；认证：`user`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[RunsDeliveryRequest](../objects/RunsDeliveryRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `run_id` | [ID](../objects/ID.md) | 是 | 运行 |

## 输出

[HttpRunsDeliveryResult](../objects/HttpRunsDeliveryResult.md) 为完整返回结构。`kind=ok` 的payload是 [RunDeliveryView](../objects/RunDeliveryView.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `run_id` | [ID](../objects/ID.md) | 是 | 所属Run |
| `bundle_ref` | [Ref](../objects/Ref.md) | 是 | 固定Bundle |
| `artifact_ref` | [Ref](../objects/Ref.md) | 是 | 固定成果 |
| `artifact` | [ArtifactRecord](../objects/ArtifactRecord.md) | 是 | 成果记录 |
| `content` | [ArtifactPreviewText](../objects/ArtifactPreviewText.md) | 是 | 实际正文 |
| `contract_ref` | [Ref](../objects/Ref.md) | 是 | 固定合同 |
| `contract` | [Contract](../objects/Contract.md) | 是 | 原要求合同 |
| `report_ref` | [Ref](../objects/Ref.md) | 是 | 固定报告 |
| `report` | [VerificationReport](../objects/VerificationReport.md) | 是 | 逐项报告 |
| `proposal_ref` | [Ref](../objects/Ref.md) | 是 | 固定提案 |
| `proposal` | [DeliveryProposal](../objects/DeliveryProposal.md) | 是 | 候选提案 |
| `requires_acceptance` | [Bool](../objects/Bool.md) | 是 | 合同要求用户接受 |
| `stale` | [Bool](../objects/Bool.md) | 是 | 相对于当前任务版本过时 |
| `acceptance` | [CompletionAcceptance](../objects/CompletionAcceptance.md) | 否 | 实际用户决定 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "run_id": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "run_id": "example_001",
    "bundle_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "artifact_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "artifact": {
      "id": "example_001",
      "version": "example_001",
      "title": "example_001",
      "format_kind": "example_001",
      "media_type": "example_001",
      "content_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "size_bytes": 0,
      "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provenance_refs": [],
      "verification_refs": [],
      "created_at": "2026-10-07T02:00:00Z"
    },
    "content": "example_001",
    "contract_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "contract": {
      "goal": "example_001",
      "requirements": [],
      "outputs": [],
      "version": "example_001"
    },
    "report_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "report": {
      "id": "example_001",
      "contract_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "target_refs": [],
      "checks": [],
      "verdicts": [],
      "outcome": "succeeded",
      "limitations": [],
      "created_at": "2026-10-07T02:00:00Z"
    },
    "proposal_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "proposal": {
      "run_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "contract_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "outcome": "succeeded",
      "artifact_refs": [],
      "report_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "unresolved_effect_refs": [],
      "created_at": "2026-10-07T02:00:00Z"
    },
    "requires_acceptance": true,
    "stale": true
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
| `ui` | [开发设计](../../../docs/design/components/ui.md) | `apps/web/src/features/workspace/` |
| `run.history` | [开发设计](../../../docs/design/components/run-history.md) | `src/uaw/run/history.py` |
| `workspace.artifacts` | [开发设计](../../../docs/design/components/workspace-artifacts.md) | `src/uaw/workspace/artifacts.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
