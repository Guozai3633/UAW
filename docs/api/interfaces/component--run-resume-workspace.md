# run.resume.workspace

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

工作区实际版本的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunResumeWorkspaceRequest, context: TrustedExecutionContext) -> ComponentRunResumeWorkspaceResult`。所属入口为 `run.resume.workspace`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunResumeWorkspaceRequest](../objects/InternalRunResumeWorkspaceRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `workspace_ref` | [Ref](../objects/Ref.md) | 是 | 获准工作区和实际文件树版本。 |
| `expected_revision` | [Version](../objects/Version.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 |
| `expected_environment_ref` | [Ref](../objects/Ref.md) | 是 | 恢复时要求的实际环境版本；不匹配需重新准备和核验。 |

## 输出

[ComponentRunResumeWorkspaceResult](../objects/ComponentRunResumeWorkspaceResult.md) 为完整返回结构。`kind=ok` 的payload是 [CompatibilityReport](../objects/CompatibilityReport.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `compatible` | [Bool](../objects/Bool.md) | 是 | 能否恢复 |
| `missing_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 不可用资源 |
| `stale_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 版本不符 |
| `migration_ref` | [Ref](../objects/Ref.md) | 否 | 批准迁移 |
| `blocking_reasons` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 阻碍 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 不将checkpoint文件镜像直接覆盖当前磁盘。
- 让Workspace/Runner检查目录、实际文件hash和环境状态
- 比较用户并发编辑与保存版本
- 冲突返回ChangeSet定位并保留用户改动
- 受测依赖改变让旧验证失效后再继续
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 目录丢失返回workspace_missing
- 环境变化要求重准备
- 冲突保持等待

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
  "expected_revision": "example_001",
  "expected_environment_ref": {
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
    "compatible": true,
    "missing_refs": [],
    "stale_refs": [],
    "blocking_reasons": []
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
| `run.resume.workspace` | [开发设计](../../../docs/design/components/run-resume-workspace.md) | `src/uaw/run/resume/workspace.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
