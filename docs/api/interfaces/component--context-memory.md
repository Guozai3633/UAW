# context.memory

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextMemoryRequest, context: TrustedExecutionContext) -> ComponentContextMemoryResult`。所属入口为 `context.memory`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextMemoryRequest](../objects/InternalContextMemoryRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalContextMemoryRequestRemember](../objects/InternalContextMemoryRequestRemember.md)
- [InternalContextMemoryRequestRecall](../objects/InternalContextMemoryRequestRecall.md)
- [InternalContextMemoryRequestForget](../objects/InternalContextMemoryRequestForget.md)

## 输出

[ComponentContextMemoryResult](../objects/ComponentContextMemoryResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalContextMemoryOutput](../objects/InternalContextMemoryOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Memory记录source、valid_from/to、supersedes与derived_from，Context是唯一写入者。
- 区分显式记住与后台推断候选
- 检查读取/贡献开关、用途、作用域和保留期
- 按具体槽位/条件查重，用户纠正优先，未决冲突保持待确认
- 提交新事实版本后才宣告记住
- 召回时复核有效时间和授权
- 遗忘立即停止召回并传播到摘要/索引/缓存
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 提交失败如实返回not_saved
- 低可信研究结论留任务候选
- 删除部分失败返回待清理项

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "remember",
  "parameters": {
    "id": "example_001",
    "content": {
      "text": "example_001",
      "kind": "preference",
      "source_refs": []
    },
    "origin": "explicit",
    "target_scope": {
      "conversation_id": "example_001"
    }
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "remember",
    "result": {
      "id": "example_001",
      "revision": 0,
      "content": {
        "text": "example_001",
        "kind": "preference",
        "source_refs": []
      },
      "scope": {
        "principal_id": "example_001"
      },
      "policy_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
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
| `context.memory` | [开发设计](../../../docs/design/components/context-memory.md) | `src/uaw/context/memory/facade.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
