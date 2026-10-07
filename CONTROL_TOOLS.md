# UAW 控制工具与主 Agent 组织方式

状态：v0.2 架构草案。用户确认将子 Agent 创建作为工具调用入口，并希望可执行的控制行为通过工具发现后使用。新增完成核验、引用与云端执行入口，见 [DELIVERY_VERIFICATION.md](DELIVERY_VERIFICATION.md)。本文定义逻辑接口，不绑定具体工具协议/SDK，尚未实现执行器。

## 1. 统一调用与职责归属

所有面向 LLM 的可执行控制动作注册为 ToolSpec，由 Tool Runtime 发现、校验、执行和审计。内部提供方仍由相应 Runtime 实现，统一工具入口不会把业务状态和模块职责都挤进 Tool Runtime。

```text
用户目标 + 当前上下文
  → 主 Agent 答复、检索能力或提出调用
  → Tool Runtime（注册、schema、权限、幂等、调用与结果）
  → 所属 Runtime（Agent / Context / Model / Workspace / Run）
  → 类型化结果和 Item
  → 当前主 Agent 决定继续、修复、询问或交付
```

绑定会话的定义创建用 `agents.create`；启动定义去执行任务用 `agents.invoke`。前者只保存配置，后者才创建 AgentInstance、分配执行预算与上下文。不会因用户说“创建三个角色”就执行三个任务。

## 2. 控制工具目录草案

工具名用于设计讨论，最终命名和 wire schema 随协议实现确定。每个工具有明确副作用、输入/输出、权限和失败分类。

| 工具 | 参数重点 | 实际职责/提供方 |
| --- | --- | --- |
| `tools.discover` | 目标、能力范围、预算内候选数 | Tool Runtime 返回可见候选及可加载 schema |
| `context.read` | 目标、资源引用、purpose、内容预算 | Context Runtime 按授权召回/装配来源 |
| `skills.load` | 技能引用/版本、任务目标 | Agent Runtime 解析依赖，Context Runtime 按需装配方法 |
| `agents.create` | definitions、用户模型意图、整组/独立提交策略 | Agent Runtime 校验并持久化当前会话定义 |
| `agents.update` | definition_id、expected_version、配置 patch | Agent Runtime 版本化更新，不无意覆盖 |
| `agents.list` | 当前允许作用域与过滤 | Agent Runtime 返回可见定义及状态 |
| `agents.invoke` | definition/role 引用、子目标、输入、输出契约、预算 | AgentFactory 创建实例，Scheduler 运行子任务 |
| `agents.wait` | instance IDs、事件 cursor、有限等待 | Run Runtime 返回结果/进度，避免忙轮询 |
| `agents.cancel` | instance_id、理由 | Run Runtime 校验归属并传播取消 |
| `agents.handoff`（扩展预留） | 目标实例/定义版本、expected_control_lease、未完成状态、预算 | Agent Handoff Controller 校验并转交唯一对话控制权；Run 保存关联事件 |
| `tasks.assess` | 当前任务引用、待解决执行问题 | Agent Runtime 按需提出执行评估，不必每次先调用 |
| `tasks.plan` | 已确认目标、steps/dag、输入和完成条件 | Planner 生成/修订计划，Validator 检查，返回 plan_ref |
| `models.list` | 用户可见模型范围、能力要求 | Model Runtime 返回目录与可用性，不修改模型政策 |
| `workspace.changes` | Run/产物/版本范围 | Workspace Runtime 返回 diff 或版本对比 |
| `workspace.revert` | ChangeSet/改动单位、expected_revision | Workspace Runtime 生成反向修改并处理冲突 |
| `references.resolve/read` | ref_id、版本、位置与内容预算 | Context Runtime 按权限解析/读取真实来源 |
| `environment.inspect/ensure` | 环境引用、工具链/依赖要求 | Workspace Runtime 检测并申请受控环境；不授予宿主权限 |
| `process.exec/poll/stop` | workspace/cwd、executable/argv 或显式 shell、超时、进程引用 | Workspace Runtime 执行沙箱命令并记录日志/变更 |
| `verification.run/report` | validator/版本、成果/快照、检查范围 | Completion Controller 协调，Tool/Workspace 执行并记录报告 |
| `tasks.verify` | 当前契约、成果与检查引用 | Completion Controller 返回完成条件状态与缺口 |
| `artifacts.publish` | 工作区/产物版本、交付类型 | Workspace/Run 登记成果并提供预览/下载，不自动公网部署 |
| `interaction.ask_user` | 问题、候选、关联动作/任务 | Run Runtime 生成可定位的用户交互 Item |

`tasks.plan` 返回计划不代表立即调度所有节点；请求后续运行时仍校验依赖、用户偏好和预算。`tasks.assess` 的语义任务本身可能需要 LLM，它只是可调用接口，不会让决策凭空变成确定算法；若主 Agent 已有充分依据，可直接制定步骤或提出获准的委派。

`agents.invoke` 的子 Agent 返回结果，由父 Agent 负责整合；`agents.handoff` 转交后续对话与决策责任，默认不启用。它不会扩大权限或改变模型继承，旧控制者不能用过期租约再提交最终回复/动作。详情见 [ENGINEERING_COMPLETENESS.md](ENGINEERING_COMPLETENESS.md) §5。

Go/Python 等 ValidatorSpec 通过通用执行器运行项目真实检查，不必每条 shell 命令都成为工具。tasks.verify 提供动态语义核对，申请结束仍由 Runtime 核对条件与版本，不能依赖模型主动调用。平台管理员配置 API 不在用户 Agent 工具目录；首版允许授权本地项目经 Local Runner 访问与测试。审批使用 assisted/manual/automatic 暂定映射，模式不扩大权限，见 [LOCAL_APPROVAL_SEMANTIC.md](LOCAL_APPROVAL_SEMANTIC.md)。

普通工具调用不修改 Agent 模型。模型变更必须来自用户明确指令并经 Model Runtime 政策校验。审批请求是执行校验的结果，LLM 不能调用工具自行批准自己的动作。

## 3. 子 Agent 创建参数示意

```json
{
  "definitions": [
    {
      "name": "论文分析员",
      "description": "讨论指定论文的论点、证据与限制",
      "instructions": "阅读实际取得的材料，区分论文结论与待验证假设，引用定位到材料版本和位置。",
      "use_when": ["用户需要论文解释或证据比较"],
      "avoid_when": ["未经授权的外部投稿或发布"],
      "skill_refs": [],
      "tool_categories": ["knowledge", "research"],
      "model_request": {"mode": "inherit", "requested_name": null},
      "output_contract": "带可追溯来源和局限说明的研究笔记"
    }
  ],
  "batch_policy": "independent"
}
```

示例技能/类别须与实际目录匹配。owner、conversation_id、调用来源、有效权限和幂等操作上下文由服务端注入，不能由 LLM 伪造；模型原文指定来源由当前用户输入关联或显式引用核验。新工具 schema 用输入字段表达用户模型意图，Runtime 才产生规范化模型政策。

工具返回每项 `created / needs_resolution / failed`、定义 ID/版本、实际配置与错误；如指定模型不存在，返回 `model_not_found`、原名称和当前可见候选。主 Agent 消费反馈后继续处理，不经过预先固定的多模型串行处理链。已创建项可在同一对话后续回合发现；未解决项不启用。

创建内部可进行原子校验与元数据提交，这是执行正确性的要求；它不规定主 Agent 每次必须先评估、生成计划、调用模型目录和再创建。用户已给出明确参数时可以直接调用 create，只有缺口才追加查找或询问。

## 4. 工具发现的基础入口

主 Agent 常驻很小的基础工具集：`tools.discover`、`context.read`，以及产品可用时的 `interaction.ask_user`。这些入口的 schema 直接提供，不要求先检索到自身。根 Agent 同时看到当前可开放能力域的简短目录，例如子 Agent 管理、规划、工作区和外部检索。

其他工具在 Tool Registry 中登记并写入既定关键词/向量索引。发现时先按用户、角色、产品 flag 和作用域过滤，再混合检索、排序，加载少量完整 schema。工具索引可过期，但实际调用必须重新核验当前权威记录与权限；发现结果不是授权。

相关工具可按任务临时提供：用户正在创建角色时直接加载 agents.create/update；持续修改代码时保留当前编辑工具。无需每次调用都重新搜索，也不把全部控制工具长期塞入每个 Agent 的 prompt。

工具说明按确定顺序渲染，当前阶段保持相关工具集稳定；provider 支持时使用延迟/追加加载适配，减少改写前缀。执行权限仍每次核验，不为模型缓存保留旧许可。工具检索缓存按 registry/index/ACL 版本区分，创建/启动等副作用控制工具不做结果缓存，见 [CACHE_DESIGN.md](CACHE_DESIGN.md)。

子 Agent 默认不拥有创建/修改会话定义和再委派的所有控制能力，只有获准委派范围和预算可开放；控制工具权限与普通文件/网络工具一样受角色、父权限、用户范围和产品 flag 限制。

## 5. 主 Agent 提示词分层

主 Agent 的能力由模型、上下文、工具实现、技能方法、状态与执行反馈共同形成。提示词负责让它理解职责与边界，不用一份不断增长的文本描述所有模块内部实现。

1. 常驻核心：目标执行、工具发现、按需规划/委派、证据与未知、用户控制、交付核验。
2. 动态上下文：原文、当前目标/状态、相关资源、约束、预算、模型政策和角色目录。
3. 按需工具 schema：现在可用工具的参数、返回结果和失败条件。
4. 按需 Skills/角色方法：当前任务的方法和参考，主 Agent 可调用 skills.load。
5. 运行反馈：实际调用结果、失败、用户纠正、版本变化与待确认项。

核心草案见 [main_agent.md](prompts/main_agent.md)。核心长度以行为清楚、无冲突、能评测为准，不设置“越长越强”的目标。长上下文在真实任务需要时加载；可靠性靠实际工具、版本/权限校验、反馈循环和任务验收，不靠让模型口头遵守所有程序规则。

## 6. 执行评估协议的定位

之前的 `ExecutionAssessment` JSON 是按需评估的专用协议，不是主 Agent 每轮的唯一输出格式。主 Agent 正常通过模型工具调用协议返回工具名和参数，或用户可读答复；不要求所有请求先输出评估 JSON。

主 Agent 可以直接调用 agents.create、读取材料或回答；在执行策略不清楚时，才调用 tasks.assess，或在同一次模型调用里提出评估与下一步建议。评估内容可分给 Intent/Agent Runtime 消费，模块仍保持边界；不固定新增一次模型往返。完整 Planner 使用专门输出契约，不与主 Agent 的日常答复混成一个巨大 schema。

## 7. 验收边界

工具 schema 保证参数形状，Runtime 保证授权、引用、版本、幂等和限额；语义理解和工具选择仍需要任务评测。要检查：无需规划的创建能直接调用；模型目录缺失能反馈处理；控制工具能通过发现找到；禁用能力不会因索引召回执行；子 Agent 不能自授权限；失败后不重复创建；主 Agent 能从工具反馈改变下一步而非重复相同流程。
