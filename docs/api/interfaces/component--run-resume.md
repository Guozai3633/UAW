# run.resume

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunResumeRequest, context: TrustedExecutionContext) -> ComponentRunResumeResult`。所属入口为 `run.resume`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunResumeRequest](../objects/InternalRunResumeRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalRunResumeRequestResume](../objects/InternalRunResumeRequestResume.md)
- [InternalRunResumeRequestReplay](../objects/InternalRunResumeRequestReplay.md)

## 输出

[ComponentRunResumeResult](../objects/ComponentRunResumeResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalRunResumeOutput](../objects/InternalRunResumeOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Resume不接管各领域写入；恢复事件关联旧checkpoint与当前版本。
- 先取得运行租约
- 检查业务schema/定义/技能/环境兼容，必要迁移显式记录
- 重建连接并核验当前撤销
- 通过Tool对账pending/unknown效果
- Workspace核对真实文件与环境变化
- 恢复无未决依赖的节点，或返回冲突/受阻
- rerun建立新Run，不将其伪装为历史回放
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 不兼容返回migration_required
- 未决结果无法核实保持blocked依赖
- 双领返回lease_conflict

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "resume",
  "parameters": {
    "run_id": "example_001",
    "checkpoint_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "mode": "resume"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "resume",
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
| `run.resume` | [开发设计](../../../docs/design/components/run-resume.md) | `src/uaw/run/resume/facade.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
