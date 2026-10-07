# context.rules

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

规则与信任装配的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextRulesRequest, context: TrustedExecutionContext) -> ComponentContextRulesResult`。所属入口为 `context.rules`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextRulesRequest](../objects/InternalContextRulesRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `scope_paths` | 数组&lt;[PathRef](../objects/PathRef.md)&gt; | 是 | 获准项目路径引用，用于查找作用域项目规则。 |
| `user_instruction_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 用户当前要求和获准偏好规则，保留来源。 |
| `activated_skill_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 本轮已激活的固定技能版本，按作用域继承方法。 |

## 输出

[ComponentContextRulesResult](../objects/ComponentContextRulesResult.md) 为完整返回结构。`kind=ok` 的payload是 [InstructionSet](../objects/InstructionSet.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `rules` | 数组&lt;[InstructionRule](../objects/InstructionRule.md)&gt; | 是 | 生效指令 |
| `conflict_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 无法自动消解的冲突 |
| `version` | [Version](../objects/Version.md) | 是 | 固定版本 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 保存InstructionSet与rule_manifest；跨目录分别记录适用规则，工具写入前核对作用域。
- 只从可信注册来源发现规则
- 用户明确要求优先，项目规则按根到目标目录细化，再装配技能/角色/偏好
- 记录覆盖关系与内容版本
- 硬权限始终由Runtime强制，不被自然语言覆盖
- 不可同时满足的关键要求返回冲突与澄清，普通风格冲突按确定优先级
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 未经注册的网页指令当数据
- 关键冲突返回rule_conflict
- 规则变化通知相关上下文失效

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "scope_paths": [],
  "user_instruction_refs": [],
  "activated_skill_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "rules": [],
    "conflict_refs": [],
    "version": "example_001"
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
| `context.rules` | [开发设计](../../../docs/design/components/context-rules.md) | `src/uaw/context/rules.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
