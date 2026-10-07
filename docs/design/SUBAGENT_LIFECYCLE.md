# 子智能体：创建、发现、调用与验收的完整开发设计

状态：v0.10，2026-10-07。这是设计策略与实现路径，尚未实现。主要依据用户已确认的工具式创建、模型继承、会话绑定和隔离要求，并参考 Notion 多Agent、Model/Skills、Tool、Runtime 题集。

## 1. 谁帮助用户设计子 Agent

**默认就是当前主 Agent。** 它需要时加载 Agent Design Skill（方法正文位于 [agent_definition.md](../../prompts/agent_definition.md)），然后调用 `agents.create/update`。不强制再串一个“设计 Agent → 审批 Agent → 创建 Agent”。

可选 `agent_designer` 职能用于用户明确要求复杂角色设计时：其职责是提出定义草案/调用条件/验收要求，工具范围只包括可见角色/技能/模型目录读取，默认不能启动业务子任务。主 Agent核对用户授权后通过同一create工具提交。它同样继承会话模型；没有明显收益时直接由主 Agent完成设计。

用户说“创建两个供以后使用的助手”只授权持久定义；“帮我完成任务，按需要分工”可以创建临时运行实例，但不自动授权把临时角色存为长期会话配置。持久配置与一次运行实例分开。

## 2. 功能模块与计划目录

```text
src/uaw/agent/
  definitions/
    facade.py          # 定义 create/update/list/disable/revert
    contracts.py       # AgentDefinitionDraft/Version/DefinitionResult
    designer.py        # 加载短方法和合法动态输入，不固定多模型链
    validator.py       # 名称、边界、依赖、来源与引用校验
    repository.py      # 幂等、会话归属、版本、名称唯一约束
    discovery.py       # 当前会话定义摘要、语义候选发现
    model_intent.py    # 保留用户指定意图，经Model解析，不自行选型号
    change_service.py  # 配置diff、停用、反向修订
  factory.py           # 唯一实例工厂；定义不是实例
  assessment.py        # planning/delegation/parallel分别判断
  collaboration/
    facade.py          # delegate/join/handoff统一入口
    contract.py        # 子目标、输入、输出、验收与权限预算交集
    instance.py        # 固定定义/模型、私有上下文/工作区
    channel.py         # 有限消息与结果引用
    join.py            # 必需结果核验和父汇总
    handoff.py         # 唯一ControlLease，可选能力
    cancel.py          # 子树取消回执与未决效果关联
src/uaw/tool/control/agents.py  # ToolSpec注册与Agent facade适配
prompts/agent_definition.md
prompts/subagent_invocation.md
```

这些是计划代码位置，目前真实存在的是提示词和设计文档。定义目录是大模块内部的实现分工；图谱 `agent.definitions` 一份文档包含该目录的全部创建职责。

## 3. 定义对象及版本

```text
AgentDefinitionVersion:
  definition_id, version, content_hash
  owner_id, conversation_id             # 可信服务端注入
  name, description, instructions
  use_when[], avoid_when[]              # 正例/排除条件，不是词典路由
  capability_tags[], skill_refs[]
  tool_categories[], delegatable_scope
  input_contract, output_contract
  model_request                        # inherit / explicit / auto
  source_input_ref                     # 用户创建/修改授权来源
  status = enabled|disabled|pending_resolution
```

Definition只记录方法与能力边界，不存上一次执行的临时prompt/目录/结果。`AgentInstance`另有instance_id、definition_ref、parent_agent_id、task/plan revisions、goal、input_refs、预算预留、实际模型政策、ContextSnapshot、workspace_ref和生命周期。实例只读取创建时固定的定义版本；安全撤销对后续动作当前生效。

同名策略：当前 owner+conversation 名称唯一。相同请求重发返回原结果；不同请求重名返回现有定义及冲突，不静默改名/覆盖。用户明确更新使用definition_id与expected_version。显式copy可由用户指定新名。

## 4. 创建完整步骤

1. 主Agent读取用户原文，识别“创建/修改供以后调用的角色”，核对当前会话及已有定义摘要。
2. 信息足够时加载短设计方法，填写职责、正反调用条件、必要输入、输出验收和工具/技能边界；关键歧义才问用户。
3. 用户未指定模型填写inherit；用户明确指定保留原名称及原文引用；明确要求自动选择才填写auto。不先猜可用型号。
4. 提交 `agents.create`：包含definitions、每项稳定client_definition_key和batch_policy；owner、scope、request_id由Tool注入。
5. Tool参数/权限校验后进入Agent定义facade；检查用户授权来源、名称/内容、可见依赖、权限交集。
6. Model Runtime验证模型意图。精确可用才启用；不存在/歧义/能力不满足返回类型结果给当前主LLM，不暗改另一型号。
7. independent批量允许逐项成功；atomic批量先全校验再事务提交。无相互引用定义默认允许独立结果，用户要求整组才atomic。
8. 提交后生成definition_id/version与配置ChangeSet，Run生成可见Item；主Agent仅宣告已确认项，失败项说明原因。
9. 当前/下次回合Context读取会话定义摘要，角色可被发现；长instructions按需读，不每轮全量加载。

```json
{
  "tool": "agents.create",
  "arguments": {
    "batch_policy": "independent",
    "definitions": [
      {
        "client_definition_key": "paper-reader",
        "name": "论文分析助手",
        "description": "阅读用户提供的论文并核对论点、证据和局限",
        "use_when": ["需要形成可定位的论文分析笔记"],
        "avoid_when": ["只有一句通用概念解释", "未提供材料且不能取得来源"],
        "instructions": "区分原文结论与推测，给出实际版本和位置；材料不足说明缺口。",
        "skill_refs": [],
        "tool_categories": ["document.read", "references.read"],
        "input_contract": {"required": ["goal", "material_refs"]},
        "output_contract": {"required": ["summary", "evidence_refs", "limitations"]},
        "model_request": {"mode": "inherit"}
      }
    ]
  }
}
```

工具类别是待注册的能力标签示例，Registry未提供时不凭空允许。完整字段schema由实现落实到Agent contracts与ToolSpec；示例不是可直接调用当前项目Runtime的请求。

## 5. 何时发现、何时调用

**每个需要能力判断的Agent回合都可以发现，不必先固定跑Planner。**

Context提供可见定义的ID、版本、简短职责、use_when/avoid_when、输入输出摘要、当前可用状态。定义多时按角色/能力/访问范围缩小候选再做语义检索；LLM阅读少量候选决定，不用关键词词典写死“论文→论文Agent”。

调用有三个时点：首次执行评估；规划节点需要独立成果；运行中出现新证据/能力缺口。每个时点都先问：

| 决策 | 需要判断的证据 |
| --- | --- |
| 自己做还是委派 | 是否有清晰独立目标与可验收输出，当前角色是否足够 |
| 只并发工具还是多Agent | 是否需要独立推理/上下文/专业方法；单次读取通常不需要Agent |
| 顺序还是并行 | 输入是否已具备、是否依赖别的结果、是否有共享写冲突 |
| 是否值得成本 | 子调用、复制上下文、汇总/审查是否在总预算内，是否有已验证收益 |
| 哪个定义 | 职责/正反条件/契约/有效工具与模型能力是否匹配，不只比名字 |

LLM产生调用建议与简短依据，代码只检查合法性和资源，不用固定复杂度分数代替语义。难以判断收益时单Agent起步，按实际观察再扩展。工具/定义不可用返回缺口，不能生成不存在的子Agent名字。

## 6. 实际委派步骤

1. 提交 `agents.invoke(definition_ref, goal, input_refs, output_contract, proposed_budget, expected_task_revision)`，或使用允许的RoleProfile创建一次临时实例。
2. Tool核对工具schema/有效scope，Agent Delegation Controller确认父子关系、flag、定义启用状态、最大深度/总数与契约。
3. 子权限 = 父有效权限 ∩ 定义/角色边界 ∩ 产品政策 ∩ 可委托范围 ∩ 资源当前授权；新敏感动作照常审批。
4. Run账本预留子预算与预期汇总费用；工厂固定定义版本，Model解析父模型继承/用户显式覆盖。
5. Context按subagent_handoff只取子目标、必要原文、上游结果与来源；不复制完整父prompt和兄弟临时状态。写任务分配隔离工作区。
6. 在持久分配边界创建instance及creation_key记录后调度，返回instance_ref；可立即完成的小任务也返回真实结果引用。
7. 父Agent继续不依赖子结果的工作，或通过有界 `agents.wait` 等待。依赖子结果的步骤必须等待，不靠“并发更快”跳过依赖。
8. 子Agent返回NodeResult：状态、summary、output_refs、evidence_refs、limitations、依赖版本、usage，不返回隐藏思维全文。
9. Join核对实际成果/契约、来源、版本与必需检查。失败、缺输入或stale回父Agent修复、重派、缩小目标或部分交付。
10. 父Agent整合并申请Completion；用户仍看到唯一负责整体对话的Agent。真正handoff需另转ControlLease，默认关闭。

## 7. 模型继承与隔离示例

会话选A，论文角色未指定模型→A；用户明确给代码角色B→B；代码角色再委派且未指定→B。会话下次选C，inherit角色的新实例→C，显式B角色仍B。改变正在运行实例模型需用户明确控制请求、安全边界与政策修订。

两个会话同时使用同一个可见定义时各自产生实例、上下文和工作区。默认定义绑定当前会话；跨会话共享或复制必须明确范围授权。共享Task只共享受控引用与确认结果，CAS处理目标变化；工作区隔离不能替代Task目标冲突处理。

## 8. 创建、调用失败与撤销

| 情况 | 处理 |
| --- | --- |
| 模型名称不存在 | 当前LLM解释/推荐；没有替代授权不能改成inherit或Auto |
| 重复create/invoke回执丢失 | 按原稳定键查状态，禁止启动重复实例 |
| 定义并发更新 | 返回新revision/diff，重新基于用户意图修订 |
| 定义停用 | 阻止新实例；运行中普通配置固定，安全撤销立即约束后续动作 |
| 子实例失败/过期 | 父收到类型结果；重试是新attempt并计成本，不抹掉失败 |
| 用户新约束 | TaskFrame/plan revision更新，依赖旧目标结果标stale |
| 父取消 | 取消子树，未决外部动作继续Tool对账，已确认成果保留 |
| 撤销角色配置 | Agent ChangeService生成反向配置修订，不撤销该角色已经发生的外部动作 |

## 9. 开发验收与参考

至少覆盖：创建不执行、同名冲突、批量部分成功、模型不存在反馈、继承树、重复invoke、共享Task目标stale、兄弟隔离、父子取消、缺必需结果不能Join、预算不足不启动、配置撤销保留版本。

单/多Agent使用同任务、同总预算、同验收比较质量/用户返工/全部费用；输入文字长不自动多Agent。提示词草案见 [subagent_invocation.md](../../prompts/subagent_invocation.md)。细分实现见 [agent.definitions](components/agent-definitions.md)、[协作入口](components/agent-collaboration.md) 和 [执行评估](components/agent-assessment.md)。

参考：[Notion 多Agent题集](https://app.notion.com/p/3ec6ccd32c8780d6b4f9d357a257bfd9) 的角色、发现、委派、通信、状态与成本章节；[Model/Skills题集](https://app.notion.com/p/3ec6ccd32c87807bb032da89a48c45ae) 的模型/技能权限与版本；[Tool题集](https://app.notion.com/p/3e96ccd32c8780fab75dd0b4c21fe7fb) 的可信调用上下文与幂等。具体UAW策略由上述用户约束决定，参考不自动取代已确认选择。
