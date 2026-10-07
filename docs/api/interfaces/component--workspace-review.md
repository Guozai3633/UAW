# workspace.review

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工作区与交付。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalWorkspaceReviewRequest, context: TrustedExecutionContext) -> ComponentWorkspaceReviewResult`。所属入口为 `workspace.review`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalWorkspaceReviewRequest](../objects/InternalWorkspaceReviewRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalWorkspaceReviewRequestGet](../objects/InternalWorkspaceReviewRequestGet.md)
- [InternalWorkspaceReviewRequestDecide](../objects/InternalWorkspaceReviewRequestDecide.md)

## 输出

[ComponentWorkspaceReviewResult](../objects/ComponentWorkspaceReviewResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalWorkspaceReviewOutput](../objects/InternalWorkspaceReviewOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Workspace记录Delivery审阅状态，Run记录用户动作；AI完成与用户接受独立。
- 固定基础/目标revision供预览diff
- 用户按文件/块/结构单元选择并校验格式能力
- 提交前复核当前revision与改动依赖
- 接受后生成实际新版本及所需重验，不改旧报告
- 位置反馈绑定artifact version并形成新的用户输入
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 过期位置先重新定位或返回stale
- 局部冲突保持待解决
- 格式无块能力明确整版接受

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "get",
  "parameters": {
    "review_id": "example_001"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "get",
    "result": {
      "id": "example_001",
      "revision": 0,
      "target_refs": [],
      "unit_ids": [],
      "feedback_refs": []
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
| `workspace.review` | [开发设计](../../../docs/design/components/workspace-review.md) | `src/uaw/workspace/review.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
