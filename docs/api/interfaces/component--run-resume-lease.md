# run.resume.lease

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

取得运行租约的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunResumeLeaseRequest, context: TrustedExecutionContext) -> ComponentRunResumeLeaseResult`。所属入口为 `run.resume.lease`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunResumeLeaseRequest](../objects/InternalRunResumeLeaseRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `run_id` | [ID](../objects/ID.md) | 是 | 当前Run，主体及会话关联由服务核验。 |
| `node_id` | [ID](../objects/ID.md) | 否 | 任务图中的具体节点；租约范围可为整个Run。 |
| `expected_revision` | [Revision](../objects/Revision.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 |
| `lease_ttl` | integer | 是 | 毫秒；必须>0，不得超过Run deadline。 |

## 输出

[ComponentRunResumeLeaseResult](../objects/ComponentRunResumeLeaseResult.md) 为完整返回结构。`kind=ok` 的payload是 [ExecutionLease](../objects/ExecutionLease.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 租约 |
| `run_id` | [ID](../objects/ID.md) | 是 | Run |
| `node_id` | [ID](../objects/ID.md) | 否 | 可选节点 |
| `holder` | [Principal](../objects/Principal.md) | 是 | 当前执行服务/worker |
| `fencing_token` | [Revision](../objects/Revision.md) | 是 | 单调栅栏 |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 是 | 过期 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 租约修订 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- lease是有限执行权，不是持久工具授权。
- 读取现有效lease
- 通过事务/CAS取得owner与递增fencing版本
- 执行期间有界续租
- 结果提交检查lease版本，失租即停止新动作
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 已被领走返回lease_conflict
- 过期提交返回stale_lease

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "run_id": "example_001",
  "expected_revision": 0,
  "lease_ttl": 1
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "run_id": "example_001",
    "holder": {
      "id": "example_001",
      "kind": "user",
      "auth_session_id": "example_001"
    },
    "fencing_token": 0,
    "expires_at": "2026-10-07T02:00:00Z",
    "revision": 0
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
| `run.resume.lease` | [开发设计](../../../docs/design/components/run-resume-lease.md) | `src/uaw/run/resume/lease.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
