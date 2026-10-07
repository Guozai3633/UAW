# run.events

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunEventsRequest, context: TrustedExecutionContext) -> ComponentRunEventsResult`。所属入口为 `run.events`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunEventsRequest](../objects/InternalRunEventsRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalRunEventsRequestAppend](../objects/InternalRunEventsRequestAppend.md)
- [InternalRunEventsRequestReplay](../objects/InternalRunEventsRequestReplay.md)
- [InternalRunEventsRequestSubscribe](../objects/InternalRunEventsRequestSubscribe.md)

## 输出

[ComponentRunEventsResult](../objects/ComponentRunEventsResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalRunEventsOutput](../objects/InternalRunEventsOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 关键事件不可因Trace采样而丢失；保留/快照压缩策略保持可恢复边界。
- 追加关键事件并分配单调序号
- 增量绑定Item/base/new revision
- 订阅按cursor续接并按event_id去重
- 缺序号/历史被裁剪返回快照+新cursor
- replay只重建状态和UI，不发起工具调用
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 未知类型通用显示
- cursor过期返回snapshot_required
- 事务失败不能提前播成功事件

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "append",
  "parameters": {
    "stream_id": "example_001",
    "event_id": "example_001",
    "event_type": "input.committed",
    "payload_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "append",
    "result": {
      "event_id": "example_001",
      "stream_id": "example_001",
      "seq": 0,
      "type": "input.committed",
      "schema_version": "example_001",
      "occurred_at": "2026-10-07T02:00:00Z",
      "payload_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      }
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
| `run.events` | [开发设计](../../../docs/design/components/run-events.md) | `src/uaw/run/events.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
