# ui

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalUiRequest, context: TrustedExecutionContext) -> ComponentUiResult`。所属入口为 `ui`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalUiRequest](../objects/InternalUiRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalUiRequestSubmit](../objects/InternalUiRequestSubmit.md)
- [InternalUiRequestControl](../objects/InternalUiRequestControl.md)
- [InternalUiRequestReview](../objects/InternalUiRequestReview.md)

## 输出

[ComponentUiResult](../objects/ComponentUiResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalUiOutput](../objects/InternalUiOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 草稿可短期本地保存；Run/审批/成果以服务端或已明确的历史权威为准，缓存不提交执行状态。
- 输入保持用户原文，预览请求另带draft_revision
- 发送使用稳定turn_request_id，反馈丢失先查询发送状态
- 按Item ID/revision更新消息，工具、审批和变更用结构化卡片
- 重连先续事件，缺序或revision不匹配拉取权威快照
- 用户评论和局部接受绑定实际产物版本，不把当前屏幕文本当资源版本
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 草稿旧响应丢弃
- 未知Item类型展示通用内容
- 旧版本审阅返回stale并显示差异，不默默接受

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "submit",
  "parameters": {
    "conversation_id": "example_001",
    "text": "example_001",
    "attachment_refs": []
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "submit",
    "result": {
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
| `ui` | [开发设计](../../../docs/design/components/ui.md) | `apps/web/src/features/workspace/` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
