# MS-I2h A：根实例与单 Agent 循环接线

日期：2026-10-09。开发来源为 ms-i2g / 72b987a；worker仍使用自己的 ms-i2h-start，不要求中途同步。本文描述 A实际新增代码，组件接受及回执见实施记录；不表示产品Agent入口已启用。

## 1. 目录和入口

| 模块 | 代码 | 详细策略 |
| --- | --- | --- |
| 统一入口 | `src/uaw/agent/facade.py` | start/step映射已有Runtime结果；未实现definitions/delegate/完成提交明确不可用 |
| 根工厂 | `src/uaw/agent/factory.py` | 每Run确定唯一ID，完整身份/Scope/Task/模型/角色检查，创建键及参数幂等；创建不调用模型、不启动图 |
| 当前来源 | `src/uaw/agent/sources.py` | 真实Run/政策、原用户固定模型、当前TaskFrame及输入版本、实际RoleProfile与剩余额度；角色不能替换模型 |
| 状态仓储 | `src/uaw/agent/repository.py` | AgentInstance/绑定/循环状态/原步骤意图，独立CAS；原模型与工具尝试保持；事件仅在实际事务提交时发布 |
| 动作循环 | `src/uaw/agent/loop.py` | 按模型提案选择答复/一个工具/等待/阻塞/完成提案，保存原上下文后才派发；失败回到观察，不固定行业流程 |
| 实际适配器 | `src/uaw/agent/adapters.py` | 登记→固定Context→Model，当前ModelOutput及ToolResult独立读取验证；结果是资料，不是指令 |
| 工具目标复查 | `src/uaw/agent/tool_access.py` | 用独立登记的原步骤Ref检查原工具上下文、当前活动步骤和TaskFrame；接在ToolRuntime反复执行的gate中 |
| 内部组装 | `src/uaw/agent/assembly.py` | 从Container实际来源、已登记Context及TextTool组件组装；借用原Model客户端，不修改默认绑定或关闭其生命周期 |
| 图引擎 | `src/uaw/agent/engines/langgraph.py` | StateGraph负责局部循环，业务状态仍由自有仓储控制；END只是停止本次执行 |
| 局部检查点 | `src/uaw/agent/engines/checkpoints.py` | 显式PostgreSQL addon生命周期，显式环境准备才setup；只保存有界JSON，无Pickle/工具对象/凭据 |

固定根方法位于 `src/uaw/resources/prompts/agent-root-v1.txt`，必须通过可信controller登记实际InstructionRule并让RoleProfile引用它。不是读取任意用户文件充当系统规则；已有根仅消费实际已登记、固定版本的方法。本轮只接空/单规则；B多规则评估随后按已提交接口接入。

## 2. 可信组装例子

```python
from uaw.agent.assembly import assemble_agent_runtime
from uaw.agent.engines.checkpoints import postgres_checkpoints

assembly = assemble_agent_runtime(container, registered_context_bindings,
                                  actual_text_tool_bindings, registry=tool_registry)
# container必须已有records/run_sources/tool_access/budgets/model_service。
# ctx由可信适配器取得：包含完整user/session、Run、conversation、Task和
# scope.task_id，原固定模型/政策；不能由HTTP/body/模型构造认证。
created = await assembly.runtime.start({
    "run_ref": current_run_ref,
    "task_frame_ref": actual_current_frame_ref,
    "creation_key": stable_creation_key,
    "role_profile_ref": actual_bound_role_ref,
}, ctx)
# 读取created.output_refs[0]，不能猜实例或RefKind；已有kind=agent_instance。
async with postgres_checkpoints(deployment_connection_string) as saver:
    engine = assembly.engine(checkpointer=saver)
    result = await engine.run(actual_instance_ref, ctx, max_cycles=8)
# setup只在可信环境准备显式initialize=True，不是每次运行自动建表。
```

Tool绑定必须已由controller真实登记；工厂不会把新角色或任意类别自动赋权。继承原用户fixed model，不使用auto_model_candidates换模型。当前模型必须支持实际JSON提案协议及角色要求的能力/窗口，缺能力向用户反馈，不启动另一个判断Agent。

## 3. start / step / resume 的输入输出

- `AgentRuntime.start(request, ctx)`：已有AgentStartRequest→RuntimeAgentruntimeStartResult。run_ref与当前实际Run匹配，task_frame_ref与实际TaskFrame和原文集合匹配；角色来自当前独立绑定。最多32步或更低Run/可信部署上限。重复创建参数保持，不创建第二根。
- `AgentRuntime.step(request, ctx)`：已有AgentStepRequest→RuntimeAgentruntimeStepResult。instance_ref需确切当前版本/hash，observations只能是实例已登记列表；remaining_budget需与实际账本相同，不是模型预算授权。一个步骤认领一个模型尝试，计数先持久化，重复或并发不能新发。
- `AgentLoop.resume(operation_ref, ctx)`：内部恢复入口，operation_ref必须来自实际LoopState.active_operation_ref或当前仓储。读取原operation.context/model_request/tool_context；caller的新attempt/deadline不能改原发送参数。当前角色/模型/TaskFrame/资源仍须通过；未知意图保持等待核对。
- `AgentRepository.discard_stale_unsent(operation_ref, ctx)`：当前用户实际新TaskFrame已发布后，显式失效旧的未发送步骤；模型未完成意图或工具预留/计划存在时拒绝，保留回执与预算，不声称撤销效果。没有实际新理解版本时不可调用。

模型提案为严格AgentDecision：`action/text/proposed_calls`；call_tools恰好一个调用，其他动作没有调用，额外approved/owner/completed等字段拒绝。工具参数仍由其ToolSpec和ToolRuntime校验。更复杂的规划、委派和专业技能依赖尚未实现，模型不能借文本绕过。

## 4. 持久状态和阶段链

```text
Root：实际来源 → CAS创建实例/绑定/LoopState → ready
Step：认领claimed → Context登记/固定快照 → prepared（原ModelCall）
      → ModelRuntime原尝试 → 实际ModelOutput复查 → decided
      ├─ respond / wait / blocked → 保存结果 → waiting（Run不completed）
      ├─ call_tools → 登记原工具来源 → ToolRuntime审批/预算/一次发送
      │              ├─ waiting/unknown → 保存原尝试 → 显式resume
      │              └─ 真实成功/失败 → 保存观察 → ready → 下一模型步骤
      └─ propose_completion → 当前CompletionPort；缺源明确不可用
```

命名记录分别为 `agent.instances`=AgentInstance、`agent.root.bindings`=AgentRootBinding、`agent.loop.states`=AgentLoopState、`agent.loop.operations`=AgentLoopOperation、`agent.observations`=AgentObservation、`agent.context.preparations`=AgentContextPreparation、`agent.tool.origins`=Ref。复用现有SQL记录设施；没有新的业务表迁移。JSON字段使用已有具体公共对象，不把控制状态存成无约束Object。

Context准备保存原配方和expected_epoch；若材料/配方/快照已提交但操作尚未记prepared，恢复使用原幂等参数，而非猜新epoch。材料始终external，实际用户原文由Context独立保护。Model请求使用单独固定attempt/trace；工具另有固定尝试但继承同一用户模型与权限。

内部 `AgentContextPort.prepare` 返回 `PreparedAgentContext(snapshot_ref, epoch)`，epoch取自实际Context.build的固定快照。LoopOperation与AgentInstance保存该值，不用根步骤数代替；若此前已登记其他配方，实际快照纪元可以与根步骤数不同。

工具当前数据验证独立于历史“ok”：成功观察复读当前ToolResult、原提供方/费用/结果证据；失败明确存入下一轮资料。Runtime输出的model_output_ref来自ModelRuntime实际输出和原invocation.finished；不是Agent自己登记假模型输出。

## 5. 取消、版本、恢复与预算

- 当前Run/输入集/TaskFrame/政策/角色/配置/工具始终复查。根必须有完整Task上下文；原理解/Model诊断允许的较宽Scope不能直接拿来调用工具。
- 当前用户取消会阻止新动作，并同步实例cancelled；原意图、费用和观察保留。Python任务中断传播，不把中断当作没有发送。
- 原模型claimed但无finished时，ModelRuntime返回unknown，不切换attempt重发。审批恢复只重新检查原工具动作，不重新调用LLM生成不同参数。
- TaskFrame变化不能复用旧模型决定：ToolRuntime重复gate核对独立原步骤与当前理解；旧图不会自行恢复。已有预留/未知执行先核对，不靠删除active pointer当作效果撤销。
- 单根步数/循环/观察均有界（32步/32次循环/32观察），模型和工具仍各由实际Run账本reserve/dispatch/settle。剩余额度计入used及held；权限、模型与来源不做TTL缓存。
- 框架checkpoint只有局部图位置；重新启动应先由UAW恢复门检查领域版本/原意图，engine不提供`ainvoke(None)`自动续跑。完整跨模块checkpoint为后续阶段。

## 6. 实施边界

默认公开Agent/Tool/通用Context绑定及flags不变。代码使用已有LangGraph addon，没有更新uv.lock或强迫worker中途安装新依赖。真实PostgreSQL/实际text计算/受控HTTP协议与实际LLM语义质量分开记证据。

CompletionPort默认缺失；完成提案没有实际专业质量、交付和当前证据来源时返回不可用，不登记虚构VerificationReport或DeliveryProposal，也不直接写Run.completed。子Agent定义/实例、DAG、网页/办公成果、生产认证、可信IPC及真实用户确认仍按后续包/门槛建设。
