# quality.reviews.export

状态：契约0.1，待实现。类别：用户与管理端 HTTP API。所属：配置与共享基础设施。

认证网页质量审阅/反馈入口。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`GET /v1/quality/reviews/{review_id}/export`；认证：`user`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[QualityReviewsExportRequest](../objects/QualityReviewsExportRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `review_id` | [ID](../objects/ID.md) | 是 | 本人已提交包 |

## 输出

[HttpQualityReviewsExportResult](../objects/HttpQualityReviewsExportResult.md) 为完整返回结构。`kind=ok` 的payload是 [QualityExport](../objects/QualityExport.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `review_id` | string | 是 | 见类型 |
| `revision` | integer | 是 | 见类型 |
| `packet_sha256` | string | 是 | 见类型 |
| `submission_sha256` | string | 是 | 见类型 |
| `authenticated_reviewer_id` | string | 是 | 见类型 |
| `basis` | enum: `human_evidence_review` / `controlled_test` | 是 | 见类型 |
| `files` | [QualityFiles](../objects/QualityFiles.md) | 是 | 见类型 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 本人归属；写入要求独立对象 CAS/幂等；不修改 Run。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "review_id": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "review_id": "example_001",
    "revision": 1,
    "packet_sha256": "example_001",
    "submission_sha256": "example_001",
    "authenticated_reviewer_id": "example_001",
    "basis": "human_evidence_review",
    "files": {
      "suite": "example_001",
      "manifest": "example_001",
      "observations": "example_001",
      "reviews": "example_001"
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
| `support.evaluation` | [开发设计](../../../docs/design/components/support-evaluation.md) | `src/uaw/shared/evaluation.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
