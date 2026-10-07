# agent.definitions

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentDefinitionsRequest, context: TrustedExecutionContext) -> ComponentAgentDefinitionsResult`。所属入口为 `agent.definitions`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentDefinitionsRequest](../objects/InternalAgentDefinitionsRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalAgentDefinitionsRequestCreate](../objects/InternalAgentDefinitionsRequestCreate.md)
- [InternalAgentDefinitionsRequestDiscover](../objects/InternalAgentDefinitionsRequestDiscover.md)

## 输出

[ComponentAgentDefinitionsResult](../objects/ComponentAgentDefinitionsResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalAgentDefinitionsOutput](../objects/InternalAgentDefinitionsOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 唯一name约束绑定owner/conversation；每项client_definition_key保持重试幂等。更新CAS，停用/撤销产生新版本；工厂固定定义版本。
- 主Agent识别用户创建/修改意图，按需加载agent_definition短方法
- 通过agents.create/update提交职责、use_when、avoid_when、技能工具边界和模型意图
- Tool注入主体/会话与幂等键
- Agent Registry检查作用域、名称冲突、依赖与用户授权，Model解析inherit/explicit/auto
- 按整组或独立项策略提交不可变定义版本
- 定义成功后返回可发现摘要，实际执行另走agents.invoke
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 模型不存在返回当前LLM且不启用
- 同名返回conflict，不覆盖
- 原子批量任何一项失败全组不提交

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "create",
  "parameters": {
    "definitions": [
      {
        "client_definition_key": "example_001",
        "name": "example_001",
        "description": "example_001",
        "instructions": "example_001",
        "use_when": [
          "example_001"
        ],
        "avoid_when": [],
        "skill_refs": [],
        "tool_categories": [],
        "input_contract": {
          "goal": "example_001",
          "requirements": [],
          "outputs": [],
          "version": "example_001"
        },
        "output_contract": {
          "goal": "example_001",
          "requirements": [],
          "outputs": [],
          "version": "example_001"
        },
        "model_request": {
          "mode": "inherit"
        }
      }
    ],
    "batch_policy": "atomic",
    "source_input_ref": {
      "kind": "input",
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
    "action": "create",
    "result": {
      "batch_policy": "atomic",
      "items": [
        {
          "client_definition_key": "example_001",
          "status": "created",
          "definition": {
            "definition_id": "example_001",
            "revision": 0,
            "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "owner_id": "example_001",
            "conversation_id": "example_001",
            "draft": {
              "client_definition_key": "example_001",
              "name": "example_001",
              "description": "example_001",
              "instructions": "example_001",
              "use_when": [
                "example_001"
              ],
              "avoid_when": [],
              "skill_refs": [],
              "tool_categories": [],
              "input_contract": {
                "goal": "example_001",
                "requirements": [],
                "outputs": [],
                "version": "example_001"
              },
              "output_contract": {
                "goal": "example_001",
                "requirements": [],
                "outputs": [],
                "version": "example_001"
              },
              "model_request": {
                "mode": "inherit"
              }
            },
            "status": "enabled",
            "source_input_ref": {
              "kind": "input",
              "id": "example_001",
              "version": "example_001"
            },
            "created_at": "2026-10-07T02:00:00Z"
          }
        }
      ]
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
| `agent.definitions` | [开发设计](../../../docs/design/components/agent-definitions.md) | `src/uaw/agent/definitions/facade.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
