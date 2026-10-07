# run.trigger

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

未来触发器的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunTriggerRequest, context: TrustedExecutionContext) -> ComponentRunTriggerResult`。所属入口为 `run.trigger`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunTriggerRequest](../objects/InternalRunTriggerRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `trigger_spec_ref` | [Ref](../objects/Ref.md) | 是 | 获准触发规则、目标、范围和重叠策略版本。 |
| `occurrence_key` | [Text](../objects/Text.md) | 是 | 定时/事件这一次触发的稳定去重键。 |
| `target_task_ref` | [Ref](../objects/Ref.md) | 是 | 定时触发所绑定任务版本。 |
| `overlap_policy` | enum: `queue` / `skip` / `parallel` | 是 | 已有运行未结束时排队、跳过或获准并行。 |

## 输出

[ComponentRunTriggerResult](../objects/ComponentRunTriggerResult.md) 为完整返回结构。`kind=ok` 的payload是 [RunRecord](../objects/RunRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | Run |
| `task_id` | [ID](../objects/ID.md) | 是 | 任务 |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 入口会话 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 状态版本 |
| `status` | [RunStatus](../objects/RunStatus.md) | 是 | 当前状态 |
| `root_agent_ref` | [Ref](../objects/Ref.md) | 否 | 根实例 |
| `frame_ref` | [Ref](../objects/Ref.md) | 否 | 当前任务理解 |
| `plan_ref` | [Ref](../objects/Ref.md) | 否 | 可选图 |
| `budget` | [Budget](../objects/Budget.md) | 是 | 上限 |
| `outcome` | [Outcome](../objects/Outcome.md) | 否 | 终态 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 受理时间 |
| `ended_at` | [Timestamp](../objects/Timestamp.md) | 否 | 实际结束 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 每次触发与授权版本留记录，节点Scheduler不负责决定定时唤醒。
- 只消费已被用户授权的TriggerSpec
- 按时区/来源生成稳定触发occurrence键
- 当前授权/预算再次校验
- 重叠按queue/skip/parallel明确处理
- 创建或唤醒指定Run并按 meaningful变化通知
- 首版预留不默认提供定时能力
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 重复触发幂等返回
- 目标已撤销不启动
- 配额不足按策略记录skip或等待

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "trigger_spec_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "occurrence_key": "example_001",
  "target_task_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "overlap_policy": "queue"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "task_id": "example_001",
    "conversation_id": "example_001",
    "revision": 0,
    "status": "queued",
    "budget": {
      "limits": {
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 0,
        "child_agents": 0,
        "wall_time_ms": 0,
        "money": "0",
        "currency": "CNY"
      },
      "max_steps": 0,
      "max_depth": 0,
      "deadline": "2026-10-07T02:00:00Z"
    },
    "created_at": "2026-10-07T02:00:00Z"
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
| `run.trigger` | [开发设计](../../../docs/design/components/run-trigger.md) | `src/uaw/run/trigger.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
