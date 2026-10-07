# run.history

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunHistoryRequest, context: TrustedExecutionContext) -> ComponentRunHistoryResult`。所属入口为 `run.history`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunHistoryRequest](../objects/InternalRunHistoryRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalRunHistoryRequestAppend](../objects/InternalRunHistoryRequestAppend.md)
- [InternalRunHistoryRequestRead](../objects/InternalRunHistoryRequestRead.md)

## 输出

[ComponentRunHistoryResult](../objects/ComponentRunHistoryResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalRunHistoryOutput](../objects/InternalRunHistoryOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- History为用户原文权威；云/本地存储权威选择独立于本地执行位置，适配器接口一致。
- 验证消息归属并追加不可变Turn
- 原文、附件引用、显式用户配置一起登记
- steer/审批答复以新输入和关联Item记录，不改过去原文
- 按授权读取顺序和版本
- 删除按保留政策标不可再读取并传播派生依赖
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 重复Turn幂等返回
- 越权会话拒绝
- 缺失历史显式返回，不能拼凑猜测原文

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "append",
  "parameters": {
    "id": "example_001",
    "conversation_id": "example_001",
    "turn_id": "example_001",
    "text": "example_001",
    "attachment_refs": [],
    "created_at": "2026-10-07T02:00:00Z"
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
      "id": "example_001",
      "conversation_id": "example_001",
      "turn_id": "example_001",
      "text": "example_001",
      "attachment_refs": [],
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
| `run.history` | [开发设计](../../../docs/design/components/run-history.md) | `src/uaw/run/history.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
