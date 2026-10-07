# workspace.environment

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工作区与交付。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalWorkspaceEnvironmentRequest, context: TrustedExecutionContext) -> ComponentWorkspaceEnvironmentResult`。所属入口为 `workspace.environment`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalWorkspaceEnvironmentRequest](../objects/InternalWorkspaceEnvironmentRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalWorkspaceEnvironmentRequestInspect](../objects/InternalWorkspaceEnvironmentRequestInspect.md)
- [InternalWorkspaceEnvironmentRequestEnsure](../objects/InternalWorkspaceEnvironmentRequestEnsure.md)
- [InternalWorkspaceEnvironmentRequestRelease](../objects/InternalWorkspaceEnvironmentRequestRelease.md)

## 输出

[ComponentWorkspaceEnvironmentResult](../objects/ComponentWorkspaceEnvironmentResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalWorkspaceEnvironmentOutput](../objects/InternalWorkspaceEnvironmentOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- EnvironmentManifest记录模板、工具链、锁文件、平台、实际隔离和ready证据。
- 先检测本地项目现有工具链与依赖
- 满足要求直接记录实际版本
- 不足时在授权项目环境安装，系统级安装另申请范围
- 初始化动作同样通过Tool策略
- 健康检查后ready，失败保留日志
- 终止/回收遵守用户保留服务与产物策略
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 安装失败标preparation_failed
- 网络/系统权限不足返回范围缺口
- 不能用空目录冒充可测试环境

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "inspect",
  "parameters": {
    "workspace_ref": {
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
    "action": "inspect",
    "result": {
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
| `workspace.environment` | [开发设计](../../../docs/design/components/workspace-environment.md) | `src/uaw/workspace/environment.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
