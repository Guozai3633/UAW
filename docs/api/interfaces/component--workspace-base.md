# workspace.base

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工作区与交付。

真实采集获准输入状态。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: CaptureRequest, context: TrustedExecutionContext) -> ComponentWorkspaceBaseResult`。所属入口为 `workspace.base`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[CaptureRequest](../objects/CaptureRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `source_ref` | [Ref](../objects/Ref.md) | 是 | 项目/提交 |
| `base_kind` | [BaseKind](../objects/BaseKind.md) | 是 | 提交或目录 |
| `include_rules` | [IncludeRules](../objects/IncludeRules.md) | 是 | 收录 |
| `expected_source_revision` | [Version](../objects/Version.md) | 是 | 基础版本 |

## 输出

[ComponentWorkspaceBaseResult](../objects/ComponentWorkspaceBaseResult.md) 为完整返回结构。`kind=ok` 的payload是 [BaseState](../objects/BaseState.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 快照 |
| `kind` | [BaseKind](../objects/BaseKind.md) | 是 | 来源方式 |
| `source_ref` | [Ref](../objects/Ref.md) | 是 | 来源 |
| `manifest` | [Manifest](../objects/Manifest.md) | 是 | 收录内容 |
| `include_rules` | [IncludeRules](../objects/IncludeRules.md) | 是 | 明确收录策略 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 采集时间 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 基础快照不可变；不改变用户源目录或提交用户改动。
- 按用户选择读取提交或当前目录
- 纳入已授权的未提交修改与未跟踪文件，排除凭据/缓存规则
- 复制时校验文件前后hash检测变化
- 生成文件清单、规则版本与基础来源
- 稳定后发布BaseStateSpec供隔离实例
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 复制中源变化返回snapshot_unstable并有限重试
- 无权文件不偷偷纳入
- 快照空间不足明确失败

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "source_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "base_kind": "commit",
  "include_rules": {
    "include_uncommitted": true,
    "include_untracked": true,
    "include_paths": [],
    "exclude_paths": [],
    "max_total_bytes": 0
  },
  "expected_source_revision": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "kind": "commit",
    "source_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "manifest": {
      "version": "example_001",
      "input_refs": [],
      "dependency_refs": [],
      "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    "include_rules": {
      "include_uncommitted": true,
      "include_untracked": true,
      "include_paths": [],
      "exclude_paths": [],
      "max_total_bytes": 0
    },
    "created_at": "2026-10-07T02:00:00Z"
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
| `workspace.base` | [开发设计](../../../docs/design/components/workspace-base.md) | `src/uaw/workspace/base.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
