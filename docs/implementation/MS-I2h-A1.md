# MS-I2h-A1：根 Agent 与有限步执行循环

日期：2026-10-09。Session A / `E:/UAW` / `integration`。基于已接受的 MS-I2g；B/C/D 的开工标签仍是 `ms-i2h-start`，不移动。

**本阶段 A 的单 Agent 开发组件及受影响门槛通过，按开发组件范围接受。** B/MS-C6、C/MS-T2e、D/MS-R2e 已报告交付，按用户要求先完成 A，本阶段尚未合入或接受这些新包。完整 MS-I2h 和 P1 产品验收仍未完成。

## 1. 本次实现了什么

此前 Context、Model、Tool 能各自运行，本阶段把它们接成根 Agent 的实际执行循环：

```text
当前 Run / 用户原文和修订 / TaskFrame / 固定模型 / 已登记角色
                          ↓
                    创建唯一根实例
                          ↓
  认领步骤 → 固定 Context → Model 提案 → 当前来源与参数复查
                                      ├─ 回答 / 询问 / 受阻 → 停止本轮
                                      ├─ 工具 → 审批 / 预算 / 一次发送
                                      │          → 真实结果或失败 → 下一步
                                      └─ 完成提案 → 独立验收入口
```

每一步由模型决定是否回答、使用工具或等待。没有按业务词典锁定流程，不为简单任务默认创建子树或任务 DAG。当前一次提案最多调用一个工具；可在后续步骤继续选择。

| 实际目录 | 本阶段职责 |
| --- | --- |
| `src/uaw/agent/contracts.py`、`ports.py` | 严格消费已有公开对象，定义内部当前来源、Context、Model、观察、验收和 engine 注入协议 |
| `sources.py` | 读取实际 Run/TaskFrame/输入集/角色/固定模型/政策/剩余账本，前后复查 |
| `factory.py`、`repository.py` | 一 Run 一根、固定创建来源、CAS 步骤与阶段、取消同步、旧任务未发送步骤失效 |
| `adapters.py`、`tool_access.py` | 实际 Context/Model/ToolResult 读取、原配方恢复、观察保存，以及工具每次 gate 的当前 TaskFrame 约束 |
| `loop.py`、`facade.py`、`assembly.py` | 统一内部入口、有限步动态决策、审批与未知意图恢复、真实依赖装配 |
| `engines/langgraph.py`、`checkpoints.py` | 可信循环上限、LangGraph 私有封装、显式 PostgreSQL 后端及有界纯 JSON 检查点 |
| `src/uaw/resources/prompts/agent-root-v1.txt` | 精炼的根 Agent 行为方法；必须登记成实际规则并由真实 RoleProfile 引用 |

详细方法、输入输出、状态链、命名空间、构造示例和限制见 [A 接线说明](../coordination/requests/A/MS-I2h-Agent-wiring.md)。权威 schema 新增 7 个内部命名对象及字段文档；没有新增公开 HTTP 操作，没有修改 shared ports/contracts 或依赖锁。

## 2. 本阶段的关键策略

1. **固定用户模型。** 工厂与每步均核对受理配置和模型政策；角色的候选模型不能触发自动换模型。当前模型不满足 JSON 协议、能力或窗口要求时明确拒绝，由用户明确改选。
2. **权限从实际来源读取。** Principal/session、Run、Task、scope、角色和政策绑定完整匹配；模型正文不能提交 owner、approved、无限预算或完成状态来取得权限。开发受理/诊断的宽 scope 不直接用于根 Agent。
3. **先保存意图，再推进动作。** 原 ModelCall、原模型尝试、工具尝试和阶段均持久化。审批后恢复同一个工具动作，不重新询问模型换参数；模型调用状态未知时不换 attempt 重发。
4. **观察来自实际结果。** Tool 成功需要当前真实 ToolResult、证明与费用来源一致；失败也作为资料进入下一轮。资料保持 external，不能升级为系统规则。
5. **用户纠正和取消有效。** 当前 TaskFrame 在下一动作前复查；未发送的旧步骤可显式失效。已预留或未知发送的旧意图保留核对，不靠清空 pointer 声称撤销效果。当前取消阻止新调用并同步实例状态。
6. **计算始终有界。** 根最多 32 步，部署/实际 Run 可收窄；循环与观察也最多 32。模型和工具仍走实际 reserve/dispatch/settle 账本；剩余额度扣除 used 与 held。
7. **框架结束不是任务完成。** `respond` 只结束本轮；LangGraph END 只结束图执行。`propose_completion` 缺实际验收来源时明确不可用，不伪造交付或 VerificationReport，不写 Run.completed。

检查点只保存有界 JSON 数据，拒绝对象、bytes、pickle、非有限数值、过深或超过 2MiB 的内容。可信 ctx 不进入图检查点。重新启动先走 UAW 原意图/版本门，不暴露框架 `ainvoke(None)` 自动续跑。完整跨模块 checkpoint 仍属后续工作。

## 3. 验证与失败记录

本阶段使用真实 A 独立 PostgreSQL、真实 Context/Run/政策/账本和实际 `text.inspect` 计算；模型 HTTP 响应和提供方连通元数据受控，不能证明真实 LLM 任务质量。

| 回执 | 范围 | 结果 |
| --- | --- | --- |
| [单元](evidence/ms-i2h-agent-unit-final.xml) | 提案约束、固定模型能力、JSON 检查点限制 | 23 passed |
| [限制与兼容](evidence/ms-i2h-limits-compatibility.xml) | 根创建/身份、并发一步所有权、步数/Task scope 以及原模型默认 fixture | 5 passed |
| [实际工具链](evidence/ms-i2h-tool-chain-task-scope.xml) | 根 → Model → 实际审批 → 重建 loop 后原尝试恢复 → text 结果/费用/观察 → 下一模型输入 | 1 passed |
| [用户修订](evidence/ms-i2h-steer-tests.xml) | 实际追加原文和新理解版本使未发送旧步骤失效 | 1 passed |
| [最终门槛](evidence/ms-i2h-final-gates-tests.xml) | 未知模型意图不重发、取消、实际 PostgreSQL 图检查点、固定模型回答、完成提案拒绝与事件版本 | 5 passed |
| [真实上下文纪元](evidence/ms-i2h-epoch-recovery-tests.xml) | 实际旧配方后运行根步骤，快照纪元与步骤数不同；原未知调用仍不重发 | 2 passed |

23 单元＋12 个 Agent SQL＋1 个原 Model 兼容 SQL，共 **36 个不同通过节点**，最终接受覆盖无失败/错误/跳过。最后 2 项包含 1 个重复的未知调用恢复，聚合选用最新通过结果。Ruff、209 文件格式和 Mypy 131 源码文件通过。接受覆盖采用不同节点去重，不把历史重复回执加到当前计数，不把 1077 的旧完整回执改称当前 Agent 全量。实际查询/权限链在早期工具用例之后未删减；最后调整失败状态、终态恢复复查和修改前事件版本，5 项 SQL 覆盖对应门槛；随后 2 项验证实际 Context 纪元与原未知调用恢复。[证据索引](evidence/ms-i2h-a1.json)与[去重汇总](evidence/ms-i2h-a1-accepted-tests.xml)明确记录较早批次关系，不声称最后修改后重跑全部 36 项；本阶段不重跑 MS-I2g 全量，完整 MS-I2h 集成里程碑再执行全量。

已修复并保留历史失败：初稿误用不存在的 RefKind；测试手工写模型 invocation 而未建立原域请求 receipt；Tool 测试未提供实际 Task scope；受控提供方状态仍 disconnected。修复分别使用既有 `agent_instance`/`content`、实际 Model 域认领事务、完整 Task 身份，以及版本一致的受控连通元数据。生产准入没有放宽，原 fixture 默认行为保持，已定向复验。

最终门槛还验证终态失败与等待区别、实际事件的修改前/后 revision。早期失败和定向修复 XML 保留在 evidence，不以 collect-only、数据库缺失或受控签名替代通过证明。本次 Docker 未运行时没有启动 SQL 测试；用户启动 Docker 后继续实际验证。

## 4. 尚未开放的能力

- 默认公开 Agent/Tool/通用 Context 绑定及 flags 保持原状态；这是一套可显式装配的开发组件。
- 专业验收、完整交付、真实 LLM/管理员提供方与生产认证仍未接好。根回答不是用户任务验收。
- 子 Agent 定义/创建/调用、DAG、技能、办公/学术成果和正式前端仍需后续阶段实现。
- B 的多规则 assessor、C 的真实 embedding/检索以及 D 的 file.read/可信 IPC/用户确认接线待下一步审阅集成。
- 当前 Context 数据链仍有明显读取开销；实际工具链测试耗时约 608 秒，受控 HTTP 几乎不等待，不能声称产品延迟达标。
- 回退代码可用正常 revert；不会删除领域意图、账本或证据，也不代表撤销外部副作用。

## 5. 复验入口

```powershell
# A 自己的隔离开发库；URL 只进入本进程，不打印凭据。
. ./ops/start-dev-db.ps1 -Session A
.venv/Scripts/python.exe -m pytest --require-postgres tests/integration/agent -q
.venv/Scripts/python.exe -m pytest tests/unit/agent -q
# 按 ops/check.ps1 的静态/格式/类型范围验证；fixtures/developer 是故意缺陷任务材料。
```

整批 Agent SQL 命令用于复验，不宣称本阶段已整批重复执行；实际接受依据上表原始批次和去重索引。实际代码/证据提交与固定阶段标签发布后记录于 [DISPATCH](../coordination/DISPATCH.md)。
