# support.evaluation

状态：契约0.1，待实现。类别：细分组件私有接口。所属：配置与共享基础设施。

离线质量评测的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalSupportEvaluationRequest, context: TrustedExecutionContext) -> ComponentSupportEvaluationResult`。所属入口为 `support.evaluation`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalSupportEvaluationRequest](../objects/InternalSupportEvaluationRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `candidate_manifest` | [Ref](../objects/Ref.md) | 是 | 待测候选系统/方法/适配器版本清单。 |
| `baseline_manifest` | [Ref](../objects/Ref.md) | 是 | 同任务预算基线的系统版本清单。 |
| `dataset_version` | [Ref](../objects/Ref.md) | 是 | 固定任务样本版本，候选与基线须一致。 |
| `fixture_environment` | [Ref](../objects/Ref.md) | 是 | 固定评测环境、输入初态与允许副作用。 |
| `grader_config` | [Ref](../objects/Ref.md) | 是 | 固定评分方法与人工/语义评审政策。 |

## 输出

[ComponentSupportEvaluationResult](../objects/ComponentSupportEvaluationResult.md) 为完整返回结构。`kind=ok` 的payload是 [EvaluationResult](../objects/EvaluationResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 评测 |
| `candidate_manifest_ref` | [Ref](../objects/Ref.md) | 是 | 候选 |
| `baseline_manifest_ref` | [Ref](../objects/Ref.md) | 是 | 基线 |
| `dataset_ref` | [Ref](../objects/Ref.md) | 是 | 固定样本 |
| `accepted_count` | [Count](../objects/Count.md) | 是 | 可接受成果数量 |
| `attempt_count` | [Count](../objects/Count.md) | 是 | 所有尝试 |
| `total_usage_ref` | [Ref](../objects/Ref.md) | 是 | 总消耗 |
| `report_ref` | [Ref](../objects/Ref.md) | 是 | 质量/耗时报告 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 评测输入、评分器和报告版本不可变；一次运行验收不替代离线系统比较。
- 固定真实输入、初态、权限与工具fixture
- 开发/回归/隐藏集分开并查近重复
- 隔离跑新旧版本，外部写禁用或模拟
- 先真实状态与硬约束，再事实/语义评分和人工校准
- 按办公/开发/学术与失败类型报告接受、返工、全成本/延迟
- 用证据决定发布门槛，不只看总分
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 零接受数成本比不可计算
- 裁判不确定抽检
- 被评输出不能改变裁判指令
- 不完整fixture标不可比

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "candidate_manifest": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "baseline_manifest": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "dataset_version": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "fixture_environment": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "grader_config": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "candidate_manifest_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "baseline_manifest_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "dataset_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "accepted_count": 0,
    "attempt_count": 0,
    "total_usage_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "report_ref": {
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
| `support.evaluation` | [开发设计](../../../docs/design/components/support-evaluation.md) | `src/uaw/shared/evaluation.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
