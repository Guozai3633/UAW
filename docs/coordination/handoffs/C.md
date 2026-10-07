# Session C 交接：MS-T1

日期：2026-10-07。状态：**组件开发与本包验证完成，待 A 审阅/集成；P1-03 未正式验收，MS-T2 未开工。**

## 实际位置和基线

- Session / 包 / 原轮：C / MS-T1 / P1-03。
- 实际 worktree：`E:/UAW/.worktrees/tool`，实际分支：`dev/tool`。
- 首次开工 HEAD 与 `parallel-wave-1^{commit}` 核对相同：`70f2fcccb88650c616920a5630d2caa45d94ad45`。工作区当时干净；未新建分支、worktree 或其他 session。
- 源码/测试/提案提交：`f9622ca88e6d59352e1bb89145ed2795da8819ab`。本交接记录另以仅文档提交追加，A 应审阅当前 `dev/tool` 分支（包含源码提交和交接提交），不需改写已交接历史。
- 公共契约版本0.1；schema SHA256：`c9737069f74331ee5f519eabc1a8bf5c2527389da0e922d46ba892557b522a2c`。
- uv.lock SHA256：`e048aafdcfdd0949b7234a8d381fa0dd1d13450ee70f13b5e01c70b79156f9f4`。shared ports/contracts、原 Intent 提示词也与 DISPATCH 摘要相同，详见 environment.json。
- 允许路径：`src/uaw/tool/`、`tests/unit/tool/`、`tests/integration/tool/`、本交接记录及 `docs/coordination/requests/C/`；本包无需例外。ignored 回执只在本工作区 `tests/.artifacts/C/MS-T1/`。
- 公共提案：[C-001-ms-t1-wiring.md](../requests/C/C-001-ms-t1-wiring.md)，待 A 审阅；未修改 composition/shared/API/schema/锁/配置，未消费 B/D 未交接源码。

## 本包改动文件

- `docs/coordination/requests/C/C-001-ms-t1-wiring.md`
- `src/uaw/tool/__init__.py`
- `src/uaw/tool/contracts.py`
- `src/uaw/tool/discovery.py`
- `src/uaw/tool/errors.py`
- `src/uaw/tool/facade.py`
- `src/uaw/tool/identity.py`
- `src/uaw/tool/invocation/__init__.py`
- `src/uaw/tool/invocation/schema.py`
- `src/uaw/tool/ports.py`
- `src/uaw/tool/registry.py`
- `src/uaw/tool/schema.py`
- `tests/unit/tool/conftest.py`
- `tests/unit/tool/test_access_identity.py`
- `tests/unit/tool/test_gate_ports.py`
- `tests/unit/tool/test_registry_schema.py`
- `docs/coordination/handoffs/C.md`（本交接文档）。

## 实际公开接口与边界

- `ToolRegistry(capacity=128)`：`register(spec, expected_revision=..., binding=...) -> int`、`get(tool_ref)`、`snapshot()`、`revision`、`reference(entry)`、`typed(entry)`。固定版本/内容和 binding 不可变，有界目录与锁保护的 revision CAS；同版本同内容重复幂等，同版本不同内容或绑定冲突。所有读取返回副本，源参数修改不能改登记内容。仅可信管理/组装调用，无新增 HTTP 或模型注册入口。
- `AdapterBinding(provider_ref, environments, implemented=False, test_only=False)`：内部绑定元数据。未绑定、未实现、test_only、环境不符、提供方不可用均不进入模型候选/预检；本包没有真实执行 adapter，也没有自动注册产品工具。真实适配器只能由 A 在已实现且验收后绑定。
- `compile_schema` / `canonical` / `digest`：有界关闭对象 schema 子集及稳定摘要。JSON 64 KiB、深度24、4096节点；有界数组、非循环本地引用。拒绝远端/动态/循环引用、regex、组合 schema、不支持关键字，不联网；unsupported 返回 registration_invalid。仅 JSON 键排序，保持字符串、换行、Unicode、数字、null、字段省略；不补默认值/类型转换。
- `invocation.schema.normalize(request, registry) -> ValidatedCall wire dict`：消费既有 NormalizeCallRequest/ToolCall，加载精确版本/内容 hash，拒绝未知字段和模型 owner/approved/可信上下文注入。这里只确认结构和参数，实际 Ref 定位/当前授权仍依赖预检/复核；不产生业务成功或持久调用引用。
- `ToolFacade.discover(request, ctx)`：消费既有 ToolToolsDiscoverInput，返回既有 RuntimeToolruntimeDiscoverResult。先求角色类别/能力/flag/环境/提供方有效交集，再进行小目录关键词搜索，返回固定候选让模型选择。没有候选为 capability_gap，不泄漏被过滤工具详情。process 必须 code_execution，workspace_write 必须 local_files，其他 spec flag 也必须启用；本包未改 flag。
- `ToolFacade.invoke(request, ctx)`：兼容既有 ToolPort，输出既有 RuntimeToolruntimeInvokeResult；执行 normalize → 当前权限 → action身份 → port预检 → 当前权限 → port复核 → 当前权限。缺任何依赖返回 dependency_unavailable；等待需 port 给真实 wait_ref，禁止布尔 approved 冒充。效应从注册 ToolSpec读取。每次 await 后检查输入未改动、重新检查取消/撤销/deadline。即使两个检查都通过，**MS-T1 仍返回 dispatch 不可用**，没有执行/批准/结算成功路径。
- `ToolAccessPort.snapshot(ctx)`、`PrecheckPort.precheck(validated_call, trusted_spec, ctx)`、`RecheckPort.recheck(validated_call, trusted_spec, precheck_result, ctx)`：本包内部 port；生产适配器尚未提供。检查 port 必须返回已有 ComponentToolInvocationPrecheckResult / ComponentToolInvocationRecheckResult，并由 owning Runtime保存真实预算/审批/call/resource状态。无 wire DTO新增字段。详见 C-001。
- `ActionIdentities.bind(validated_call, ctx) -> bool`：进程内动作身份冲突保护；principal/run/action命名空间，绑定参数、工具版本/内容、scope、agent/task/node、固定模型/能力政策版本。新 action返回False，相同输入换attempt返回True，同ID改参数或绑定版本冲突。容量满拒绝，不TTL清除。不是跨进程或跨重启持久账本，没有 exactly-once承诺。
- `require_safe_recovery(effect, effect_state)`：只作恢复拒绝闸门，不执行重试。EffectState只有confirmed/pending/unknown，非read在这三种状态均不盲重试；没有自行增加 none/未发生状态。后续须实际对账证据与固定恢复政策。未替换提供方、未改变用户模型、原文、权限或运行状态。

## 可执行对接例子及回执

[受控组件 examples.json](../../../tests/.artifacts/C/MS-T1/examples.json) 已通过实际调用并断言；示例只使用本session fixture，不是生产 LLM/Runner/审批/SQL 回执。

1. 成功：`test_discovery_returns_only_candidates_and_invocation_remains_unavailable` 返回 kind=ok 的固定候选/registry_revision；紧接invoke返回precheck不可用。证明目录可发现，不声称已执行工具。
2. 拒绝/失败：`test_feature_flag_and_test_only_or_unimplemented_adapter_are_not_published` 和 `test_effect_is_trusted_spec_and_cannot_omit_mandatory_product_flags`：禁用flag、测试/未实现绑定不发布；直接伪造调用也拒绝。`test_spoofed_context_ref_and_unregistered_version_rejected`拒绝模型自报身份/批准及缺失/过期版本。
3. 重复/版本冲突：`test_verifiable_wait_propagated_and_changed_parameters_conflict` 的受控 port返回waiting；相同action换attempt重复仍waiting，参数count变更返回action_conflict；`test_fixed_version_idempotency_cas_and_immutable_inputs`与并发CAS用例验证目录版本冲突。实际响应在examples.json。

## 验证命令与实际结果

环境：本工作区 `.venv`，Python 3.14.6，editable source指向本工作区；未操作A的共享依赖缓存、数据库、服务、Docker或凭据。

```powershell
Set-Location E:/UAW/.worktrees/tool
.venv/Scripts/python.exe -m ruff check src/uaw/tool tests/unit/tool
.venv/Scripts/python.exe -m mypy --cache-dir .cache/mypy-tool src/uaw/tool
.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider --junitxml=tests/.artifacts/C/MS-T1/unit.xml
git diff --check
```

- Ruff：All checks passed，回执 `tests/.artifacts/C/MS-T1/ruff.txt`。
- Mypy strict：11个源码文件无错误，回执 `tests/.artifacts/C/MS-T1/mypy.txt`。
- Pytest：**52 passed，无失败、无skip**，回执 `tests/.artifacts/C/MS-T1/pytest.txt`、`unit.xml`。
- 组件例子已执行并断言，`examples.json`；共享SHA256、Python位置、基线和验证范围在 `environment.json`。
- git diff/staged diff whitespace检查通过；提交文件均在Session C允许路径。无残留未通过的本包检查。
- 回执为ignored本机文件，未进入源码提交；A可在本worktree读取/另存，并必须在实际集成SHA重跑组合验证。

## 未实现依赖、接线和原轮未通过项

- **没有真实权限快照、审批/预算预检、资源复核、持久意图/效果账本、Runner派发或结算port接线。** 当前生产目录为空，不把声明元数据或测试替身标为产品能力。缺依赖明确失败，测试审批wait_ref标明fixture。
- 尚未运行真实外部模型/Runner/SQL/端到端 Agent 任务；A原73项全量/整链路回归也未由C执行。52个组件检查不等于P1-03 accepted或真实审批/dispatch验收。
- A审阅后接ToolAccess/Precheck/Recheck到公开状态所有者，确认configuration类型tool_ref与真实目录命名空间一致；不得把fixture接入产品。schema安全子集之外的需求交C补实现。完整清单与字段/省略/错误/CAS/消费方影响见C-001。
- Run仍拥有取消、审批与预算；工具组件不另建业务状态。真实CallRef/ApprovalRef/ResourceRef必须由状态所有者产生并复核；未来持久effect账本/迁移/dispatch port由A提供新基线，不用内存guard代替。
- D01存储权威、D03 Runner方式、D06真实模型均未自行设定。EffectState没有已确认未发生写的表达，安全恢复协议待A决定；未使用提议字段。
- **MS-T2以MS-I2新基线为前置，当前不开始。** A合入并发布真实集成SHA后，干净的dev/tool在包边界同步，保留现有提交历史。
- A负责接受、公共冲突、合入、公共实现范围登记、整条链路回归及后续派发；C没有修改DISPATCH/计划状态或自行合入其他分支。

## 影响与回退

本包只新增隔离组件，没有改变现有API/运行行为或启用任何能力。A可独立审阅源码提交 `f9622ca88e6d59352e1bb89145ed2795da8819ab`，再合入当前dev/tool。若退回，由C修本包业务；若需撤销，由A revert该源码提交和后续公共接线提交，不重置其他session。没有已执行的业务外部副作用、迁移或新依赖需要撤销。


# MS-T2a 交接追加

状态：**本包代码与单元检查已交付；真实 SQL 验证受环境阻碍，待 A 审阅与复跑。未进入完整 MS-T2，未接受 P1-03/P1-09。** 上方 MS-T1 历史保持原样。

## 实际基线、分支和提交

- 目录 `E:/UAW/.worktrees/tool`，分支 `dev/tool`。
- 开工工作区干净，实际执行 `git fetch origin --tags` → `git merge --ff-only ms-i2a`；快进成功。同步后 HEAD 与 `ms-i2a^{commit}` 一致：`ac9bf621e3caebf060300b3a628b77dee36f7ab0`，未 reset/改写历史。
- 按新 uv.lock 执行 `uv sync --frozen --extra agent-engine --link-mode copy` 成功，缓存只用本 worktree `.cache/uv`，独立 `.venv` / Python 3.14.6。
- **MS-T2a 源码/测试/提案提交：`e3a19dd2d800b44005c95daabc4a96cecd04892e`**。交接记录另作仅文档提交；A合入当前dev/tool两笔提交，不需修改已交接历史。
- schema SHA256 `e4195d1f89fb82bbc7cf5bd32e1cafdc04f44ba70a87703fc38ff65f45025b0d`；uv.lock SHA256 `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`；shared ports/contracts均与DISPATCH摘要一致。
- 只改C允许路径；未修改公共schema/锁/组装/API/迁移/其他worker文件；未开启flag、启动数据库服务、复制凭据或配置D01/D03/D06。

## 本轮改动清单

- `docs/coordination/requests/C/C-002-ms-t2a-ledger-and-readers.md`
- `src/uaw/tool/approval.py`
- `src/uaw/tool/authority.py`
- `src/uaw/tool/budget.py`
- `src/uaw/tool/errors.py`
- `src/uaw/tool/ledger.py`
- `tests/integration/tool/conftest.py`
- `tests/integration/tool/test_durable.py`
- `tests/unit/tool/test_durable_adapters.py`
- `docs/coordination/handoffs/C.md`（本交接追加）。

## 公开组件接口和状态所有者

- `ToolLedger(store)`：`bind(call, spec, ctx)`原子固定不可变action/attempt；`action/action_key/attempt/effect`读取真实状态；`claim(intent, ctx)`原子记录唯一派发意图与unknown效果；`save`仅写白名单tool阶段及对应命名DTO；`acknowledge`保存实际首个预算回执，不改写accepted/unchanged。
- action按Principal/Run/action分区，attempt按Principal唯一；新attempt/trace不换action，operation/scope/task/agent/node/模型/能力政策或参数变化冲突；原期限不可扩大。ToolSpec/effect/hash由固定注册记录和真实参数核对。工具账本是实际PG RecordStore记录，不使用内存guard代替持久账本。
- `ToolApprovalAuthority(ledger, registry, configuration, access, resources)`满足公共ApprovalAuthorityPort.check；从持久ValidatedCall/ToolSpec、Run/固定模型、当前政策父链/权限/flags/提供方/取消、实际资源Reader导出ApprovalCreateRequest，拒绝模型自报effect/hash/资源或旧授权。缺Reader/角色环境明确不可用；未解析的policy feature_flag_refs也不可用。基线ApprovalService不支持的父政策/规则/持续授权仍拒绝。
- `ActionResourceReaderPort.resolve(call, spec, ctx)`为本包内部 owning-domain 接线port，须覆盖固定动作实际触及的全部资源和当前授权/版本；传入路径/Ref不是权限，缺真实实现不放行。没有新增公共wire字段。
- `ToolApprovalAdapter(ledger, authority, approvals: ApprovalPort)`实现既有PrecheckPort/RecheckPort；`require_approved(ctx)`供预算阶段消费。规范化动作先持久固定；request/get/recheck只使用真实服务记录；waiting引用真实ApprovalRequest当前版本；批准后再次检查当前资源/权限。批准不自动发送、等待不预留预算，拒绝/取消/过期明确返回，错误服务DTO返回dependency_protocol_invalid。
- `ToolBudgetAdapter(ledger, budgets: BudgetPort, approvals)`：`reserve(estimates, ctx)`、`recover_reserved(ctx)`、`release(ctx)`、`mark_dispatch(ctx)`、`settle_unknown(ctx)`、`reservation_ref(ctx)`。消费实际公开服务方法，稳定请求ID和不可变计划用于响应丢失恢复；只有确定CAS冲突才生成下一计划（最多4个），不在超时后换attempt。
- mark_dispatch只做**内部意图/预算记账，无executor调用**；先真实审批复核，再原子claim+unknown，最后调用预算dispatch。claim后中断仅重放账务，不重发动作；重复返回False，不是第二个执行授权。当前ToolFacade连入gates后批准也返回dispatch unavailable，不调用该内部方法、不预留预算。真实发送及fencing仍是后续MS-T2/A接线。
- tool-identities锁负责原子action/attempt固定，tool-run锁负责后续阶段。所有事务回调只读写记录，**不会在持有conversation或tool事务锁时嵌套调用BudgetService**。Authority在ApprovalService会话锁内只普通读取，不申请tool锁/审批/预算锁。跨服务流程是可恢复阶段，未声称单事务。
- Run仍拥有取消、审批和预算，C不另建Run业务状态；tool命名空间拥有调用身份/意图/效果。各持久payload均为已发布的ValidatedCall、ToolSpec、TrustedExecutionContext、ApprovalCreateRequest、EffectRecord、BudgetReserveRequest、BudgetReservation、Ref、Acknowledgement、BudgetSettleRequest、UsageSettlement等命名schema，没有Object隐藏扩展。表/DTO对照详见C-002。
- unknown未回执/不重发/不释放其已claim预留；未dispatch的竞争失败attempt可释放自己的独占预留。settle_unknown只记录billing_state=pending和currency，未知观察字段省略，保留实际未决额度；没有把未观察消耗记为0或成功，没有confirmed效果/真实回执对账能力。

## 成功、拒绝、重复/恢复对接例子

可执行例子位于本轮unit与SQL测试，所有受控fixture均注明不是产品能力。

1. `test_sql_real_wait_approved_restart_missing_executor_no_budget`：真实审批服务pending引用指向存储id/version；用户approve_once后重建服务并复核，facade仍返回dependency_unavailable/dispatch，预算没有预留。
2. `test_sql_approval_hash_resource_effect_policy_and_cancel_change`、`test_sql_policy_revision_and_parameter_changes_cannot_reuse_grant`：批准后参数/hash/effect/资源/权限改变或Run取消拒绝；`test_sql_missing_reader_role_port_and_current_provider_revocation`缺Reader/角色环境或当前提供方撤销拒绝。
3. `test_sql_concurrent_budget_reserve_once_and_no_nested_transaction_deadlock`、`test_sql_two_attempts_cannot_claim_same_action`、`test_sql_release_dispatch_race_keeps_exactly_one_persistent_intent`：并发reserve只持有一次额度，action只提交一个send intent，释放与claim互斥。
4. 四个`test_sql_crash_after_service_commit_recovers_same_budget_request`子例和`test_sql_claim_commit_before_accounting_crash_never_reissues_send`：commit后响应丢失/claim后记账前中断，重启只重放同一个预算步骤；unknown阻止新写attempt，不能把异常当作未发生。

**这些SQL断言尚未在本工作区执行到业务阶段**，不能将用例代码或收集成功标为SQL通过。单元协议替身已运行，验证了当前审批读取、正确等待引用消费、失败DTO脱敏、缺真实权限/Reader拒绝等；不代表真实SQL/LLM/Runner。

## 命令、回执和未通过项

```powershell
Set-Location E:/UAW/.worktrees/tool
.venv/Scripts/python.exe -m ruff check src/uaw/tool tests/unit/tool tests/integration/tool
.venv/Scripts/python.exe -m ruff format --check src/uaw/tool tests/unit/tool tests/integration/tool
.venv/Scripts/python.exe -m mypy --cache-dir .cache/mypy-tool src/uaw/tool
.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider --junitxml=tests/.artifacts/C/MS-T2a/unit.xml
.venv/Scripts/python.exe -m pytest tests/integration/tool -q -p no:cacheprovider --require-postgres --junitxml=tests/.artifacts/C/MS-T2a/sql.xml
```

- Unit：**66 passed，0 failure/skip**；原MS-T1的52项仍通过，新适配协议14项通过。
- Ruff通过，格式22个文件通过，Mypy strict 15个源码文件无错误；git diff/staged diff --check通过。
- SQL：17项已收集；使用--require-postgres实际尝试，**17 setup errors，0 passed/skip，exit 1**。共同原因是`UAW_TEST_DATABASE_URL`未配置；PG连接和业务断言尚未运行。没有从A复制连接URL/凭据，没有自行启动DB/迁移或以SQLite/mock代替。
- ignored回执：`tests/.artifacts/C/MS-T2a/unit.txt`、`unit.xml`、`ruff.txt`、`format.txt`、`mypy.txt`、`sql.txt`、`sql.xml`、`environment.json`。回执没有入源码提交，A可读取/保存。
- 未运行：真实PG本包行为、全量整链路、真实LLM、Runner/IPC/executor、真实领域Reader/角色/环境/账号权限；不宣称产品能力已开放。

## A 接线、公共提案和回退

[C-002-ms-t2a-ledger-and-readers.md](../requests/C/C-002-ms-t2a-ledger-and-readers.md)包含最小composition例子、所有命名阶段schema、消费方、锁/预算恢复顺序、缺口、必要验证和回退方式。

A须安排受控PG及独立测试主体，先在本分支/实际集成SHA运行上述17项SQL检查，再组合审阅；若失败由C修本包业务。A将ToolAuthority注入ApprovalService，将真实Role/Environment/ResourceReader注入Authority；默认缺port仍不可用。批准到发送之间的lease/fence/取消/当前撤销/句柄复核仍需A和实际executor完成，mark_dispatch的布尔值不是Runner权限。不得把fixtures的connected metadata、role/Reader或声明adapter登记为产品能力。

公共缺口：完整MS-T2需要带实际action/attempt/provider/receipt/evidence/Usage绑定的对账port/DTO；confirmed-not-applied不可从超时推出，本包没有消费建议字段。BudgetPort缺状态查询port，当前按A现有storage读取RootBudgetLedger/实际BudgetReservation用于CAS与只恢复已提交预留；若A要求收拢跨域读，应先发布BudgetStatePort。字段与版本决定在C-002交A，C没有直接扩充公共schema。

MS-T2a范围到此；等待SQL回执、A审阅及新基线，不自动进入完整MS-T2。D01/D03/D06保持未决定。A负责合入、公共冲突、配置/事件/实施范围登记和整链路回归。无新依赖或迁移；回退源码提交`e3a19dd2d800b44005c95daabc4a96cecd04892e`与后续A接线提交即可，但不得删除持久unknown意图或用代码revert声称已撤销外部效果。
