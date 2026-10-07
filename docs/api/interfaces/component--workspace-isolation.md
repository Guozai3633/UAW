# workspace.isolation

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工作区与交付。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalWorkspaceIsolationRequest, context: TrustedExecutionContext) -> ComponentWorkspaceIsolationResult`。所属入口为 `workspace.isolation`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalWorkspaceIsolationRequest](../objects/InternalWorkspaceIsolationRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalWorkspaceIsolationRequestAllocate](../objects/InternalWorkspaceIsolationRequestAllocate.md)
- [InternalWorkspaceIsolationRequestRelease](../objects/InternalWorkspaceIsolationRequestRelease.md)

## 输出

[ComponentWorkspaceIsolationResult](../objects/ComponentWorkspaceIsolationResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalWorkspaceIsolationOutput](../objects/InternalWorkspaceIsolationOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- WorkspaceHandle绑定Run/Agent与基础版本；分支合并不自动发布外部动作。
- 按任务所需与实际后端能力选择工作副本
- 并行写实例分配独立目录/分支，只读共享稳定基础
- native模式明确实际权限并限制同目标并发写
- 记录隔离类型/根/基础revision
- 释放前保存产物和未处理改动，按租约停止进程
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 不支持的隔离模式返回unsupported
- 目录分配失败不标ready
- 存在未处理改动禁止直接删除

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "allocate",
  "parameters": {
    "base_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "mode": "isolated_copy",
    "writer_agent_ref": {
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
    "action": "allocate",
    "result": {
      "id": "example_001",
      "revision": "example_001",
      "base_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "mode": "isolated_copy",
      "writer_agent_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "root_handle": "example_001",
      "state": "allocating"
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
| `workspace.isolation` | [开发设计](../../../docs/design/components/workspace-isolation.md) | `src/uaw/workspace/isolation.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
