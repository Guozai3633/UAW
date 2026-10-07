# run.checkpoint

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

只从各域已提交仓储取得版本，pending游标可缺省。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: CheckpointCaptureRequest, context: TrustedExecutionContext) -> ComponentRunCheckpointResult`。所属入口为 `run.checkpoint`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[CheckpointCaptureRequest](../objects/CheckpointCaptureRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `committed_event_seq` | [Revision](../objects/Revision.md) | 是 | 事件提交点 |
| `domain_refs` | [DomainRefMap](../objects/DomainRefMap.md) | 是 | 跨域已提交版本 |
| `pending_call_cursor` | [Cursor](../objects/Cursor.md) | 否 | 未决工具位置 |
| `schema_version` | [Version](../objects/Version.md) | 是 | 格式 |

## 输出

[ComponentRunCheckpointResult](../objects/ComponentRunCheckpointResult.md) 为完整返回结构。`kind=ok` 的payload是 [Checkpoint](../objects/Checkpoint.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 检查点 |
| `run_ref` | [Ref](../objects/Ref.md) | 是 | 运行版本 |
| `schema_version` | [Version](../objects/Version.md) | 是 | 快照格式 |
| `committed_event_seq` | [Revision](../objects/Revision.md) | 是 | 最后提交事件 |
| `domains` | 数组&lt;[DomainCheckpoint](../objects/DomainCheckpoint.md)&gt; | 是 | 各域固定版本 |
| `pending_action_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 待对账动作 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 提交时间 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 引用各领域权威状态，不复制可独立改写的第二套计划/审批；失败保留上个有效点。
- 在可恢复安全边界收集已提交领域版本
- 保存计划/实例/上下文/工作区/预算引用与Tool账本游标
- 检查关键引用可解析，标明未决效果
- 原子发布本地checkpoint指针与事件序号
- 不序列化连接、密钥或隐含思维为恢复权威
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 部分引用未提交不发布
- 损坏checkpoint回上个点并对账
- 外部状态不能凭快照声明原子

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "committed_event_seq": 0,
  "domain_refs": {},
  "schema_version": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "run_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "schema_version": "example_001",
    "committed_event_seq": 0,
    "domains": [],
    "pending_action_refs": [],
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
| `run.checkpoint` | [开发设计](../../../docs/design/components/run-checkpoint.md) | `src/uaw/run/checkpoint.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
