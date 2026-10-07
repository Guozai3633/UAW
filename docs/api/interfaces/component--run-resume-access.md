# run.resume.access

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

重建连接与核验的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunResumeAccessRequest, context: TrustedExecutionContext) -> ComponentRunResumeAccessResult`。所属入口为 `run.resume.access`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunResumeAccessRequest](../objects/InternalRunResumeAccessRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `domain_resource_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 检查点固定的各业务域资源，恢复逐个复核。 |
| `current_principal` | [Principal](../objects/Principal.md) | 是 | 恢复请求的当前认证主体，不继承旧过期权限。 |
| `current_config_revision` | [Revision](../objects/Revision.md) | 是 | 恢复时有效配置版本，含当前撤销与能力开关。 |

## 输出

[ComponentRunResumeAccessResult](../objects/ComponentRunResumeAccessResult.md) 为完整返回结构。`kind=ok` 的payload是 [ResumeAccessResult](../objects/ResumeAccessResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `authorized_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 仍获准资源 |
| `unavailable_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 撤销/删除/断连 |
| `configuration_ref` | [Ref](../objects/Ref.md) | 是 | 当前配置 |
| `blocking_reasons` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 阻碍 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- checkpoint保存引用，当前授权读取原权威。
- 重新核验当前身份、项目绑定、账号与撤销
- 重建连接/进程查询句柄而非复用序列化连接
- 检查已删除来源不重新加载
- 返回可继续的真实访问范围
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 资源撤销返回denied
- Runner断开返回disconnected
- 来源删除不能恢复内容

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "domain_resource_refs": [],
  "current_principal": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "current_config_revision": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "authorized_refs": [],
    "unavailable_refs": [],
    "configuration_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
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
| `run.resume.access` | [开发设计](../../../docs/design/components/run-resume-access.md) | `src/uaw/run/resume/access.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
