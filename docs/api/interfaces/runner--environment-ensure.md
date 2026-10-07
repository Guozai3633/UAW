# environment.ensure

状态：契约0.1，待实现。类别：本地 Runner 协议。所属：工作区与交付。

按批准模板准备环境并核验。

[分类索引](../RUNNER.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

配对/本地选择是专用可信交互；执行类消息走 `RunnerCommand` 信封，其中request_ref解析为下方输入。服务签名和本机范围/权限均有效才执行，响应回传ComponentResult，不能把进程启动当成完成。

## 输入

[ToolEnvironmentEnsureInput](../objects/ToolEnvironmentEnsureInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `workspace_ref` | [Ref](../objects/Ref.md) | 是 | 工作区 |
| `template_ref` | [Ref](../objects/Ref.md) | 是 | 批准模板 |

## 输出

[RunnerEnvironmentEnsureResult](../objects/RunnerEnvironmentEnsureResult.md) 为完整返回结构。`kind=ok` 的payload是 [EnvironmentRecord](../objects/EnvironmentRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 环境 |
| `workspace_ref` | [Ref](../objects/Ref.md) | 是 | 工作区 |
| `template_ref` | [Ref](../objects/Ref.md) | 否 | 初始化模板 |
| `status` | [EnvironmentState](../objects/EnvironmentState.md) | 是 | 准备状态 |
| `dependency_evidence_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 版本/安装证据 |
| `setup_process_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际进程 |
| `failure` | [Failure](../objects/Failure.md) | 否 | 失败 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 状态版本 |

## 约束与提交

- 效果分类：`process`。
- 认证/上下文：`runner`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 网络请求实际为RunnerCommand信封，签名/期限/主体/根/栅栏与业务参数均复核；重复command_id只返回原执行状态。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "workspace_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "template_ref": {
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
    "workspace_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "status": "unprepared",
    "dependency_evidence_refs": [],
    "setup_process_refs": [],
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
| `workspace.environment` | [开发设计](../../../docs/design/components/workspace-environment.md) | `src/uaw/workspace/environment.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
