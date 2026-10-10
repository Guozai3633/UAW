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


# MS-T2b 交接追加 · 2026-10-08

状态：**本包源码、组件验证和SQL用例已交付；真实SQL本轮尚未通过环境准备，待A复跑与接受。完整MS-T2继续等待。** 上方两包历史保留；MS-T2a已由A在ms-i2c接受并实跑，不改写原worker当时缺连接的回执。

## 实际基线、位置与提交

- 工作目录：`E:/UAW/.worktrees/tool`，分支：`dev/tool`。
- 开工工作区干净；实际执行fetch origin --tags、merge --ff-only ms-i2c成功，没有reset/改写历史。同步后HEAD与标签commit相同：`1411f6aa477b0d000bee871c0f324fbfd67b4ff5`。
- uv sync --frozen --extra agent-engine --link-mode copy通过（91 packages checked），独立缓存`.cache/uv`，本目录`.venv`/Python 3.14.6。
- **源码/测试/提案提交：`c78d37101a4c203cbe487f15cb5cabc063ca5f76`**；本交接记录另作仅文档追加提交，A审阅当前dev/tool两笔提交。
- schema SHA256 `b5d7cdf9df23002e6e3d3965741cbcd82b7efa34ff438b09b236e3b0b886d583`，shared ports `cce4db2349b92a6a2fca815917725cb7bb51fcb5ab9db86c2f456d3df2b679cd`，uv.lock `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`；均保持ms-i2c摘要。
- 只修改C允许目录，不改公共schema/锁/组装/API/迁移/其他worker文件；A的ProviderBinding.active及pending Usage省略未知维度契约保留，无connected字段回退。

## 本轮文件

- `docs/coordination/requests/C/C-003-ms-t2b-reconciliation-wiring.md`
- `src/uaw/tool/authority.py`
- `src/uaw/tool/budget.py`
- `src/uaw/tool/ledger.py`
- `src/uaw/tool/reconciliation.py`
- `tests/integration/tool/conftest.py`
- `tests/integration/tool/receipt_fixtures.py`
- `tests/integration/tool/reconcile_child.py`
- `tests/integration/tool/test_durable.py`
- `tests/integration/tool/test_reconciliation.py`
- `tests/unit/tool/test_port_consumption.py`
- `tests/unit/tool/test_reconciliation.py`
- `docs/coordination/handoffs/C.md`（本追加）。

## 实际接口、数据所有者与接线

- `ToolApprovalAuthority(..., policies: ExecutionPolicyPort | None=None)`：消费当前父链snapshot，检查Run/scope/叶policy版本摘要/capability绑定，不再读取execution.policies或预算私有记录；固定模型、角色、实际资源、固定/当前配置、active提供方、flags和环境校验仍保留。缺policies/access/Reader明确不可用。
- `ToolBudgetAdapter(..., state: BudgetStatePort | None=None)`：由`Container.budgets`明确注入读写两个port，使用get_ledger/get_reservation取真实revision及原attempt所有权；缺state拒绝，禁止私有表回退。查询可用于取消/过期原尝试恢复，但不是新准入，后续写仍CAS。原attempt上下文、operation、trace、模型、参数和期限不改动。
- `ToolLedger.claim(intent, ctx, *, budget, reservation)`：只消费已由读port取得的snapshot，原子保存Tool意图，不授予发送权限，最后BudgetPort仍核验当前状态；公开发送仍不可用，lease/fence/实际executor留给A完整接线。
- 新增`ToolReconciler(ledger, budgets, *, receipts=None, evidence=None).reconcile(receipt_ref: Ref, ctx, *, expected_revision: int)`：内部可信固定Ref入口，输出既有RuntimeToolruntimeReconcileResult；默认没有Reader，返回dependency_unavailable。没有新增公共请求字段或HTTP/产品挂载。
- ToolReceiptReaderPort为A发布接口；Reader独立验证本人范围、来源、签名/协议完整性和固定版本。C核查action_ref、实际attempt、固定provider、实际读取receipt_ref、usage.attempt_id和observed_at，再核对实际证据；同版本内容/版本变化、伪造绑定拒绝。
- `ToolEvidenceReaderPort.check(ref, ctx) -> Ref`为本包内部证据来源port，必须实时读取/核验当前访问、真实版本/摘要并返回实际Ref；没有接口实现不能把Ref当证明。applied/not_applied至少一条证据，证据后再次读取receipt检测来源变化/撤销。Reader的恢复数据权限与新执行准入分开，取消/过期原尝试允许核算，来源拒绝则保留已有unknown/结论和额度。
- 账本新方法`begin_reconciliation/finish_reconciliation/receipt_key/effect_from_attempt`：首次核对EffectRecord revision CAS，同principal receipt kind/id/version唯一；同版本改body/hash/location冲突。固定ToolReconciliationReceipt和当前attempt核对计划、BudgetSettleRequest费用计划、真实UsageSettlement、明确Failure都用已有命名schema持久化，无Object私有扩展。
- 工具事务只操作本owner记录；不在Tool会话锁内调用BudgetService/Reader。预算查询/服务调用在锁外，CAS确定失败才最多4次重读；超时/响应丢失重放同一固定费用请求，不覆盖旧计划、不换attempt或重发动作。前一未决计划阻止新回执抢占；确定费用拒绝保留实际效果并允许随后confirmed账单。旧未完成回执被新证据替代后拒绝重新抢占。
- `settle_receipt`：费用与效果分开；检查结算返回预留kind/id/推进版本和Usage引用，不把跨尝试响应登记为费用完成。pending只记录真实观察字段，未知维度保留原额度。same Usage的新效果证明和历史MS-T2a pending计划桥接复用实际费用回执，不重复记账。费用失败/中断不回滚真实已知效果；confirmed费用也不把unknown效果变成applied。
- **EffectRecord.confirmed表示效果结论确定，不等于工具应用成功。** applied/not_applied区别必须读取严格ToolReconciliationReceipt.outcome；not_applied仍可能有费用，且本包不给retry授权。unknown始终不重发，核对/清理不调用reserve/dispatch推断结果。
- 状态所有者不变：Run拥有审批/预算/取消，C拥有动作/尝试/意图/效果和核对阶段。新tool.reconciliation.*表/DTO对照、实际容器属性`execution_permissions`/`budgets`及最小接线见[C-003](../requests/C/C-003-ms-t2b-reconciliation-wiring.md)。生产Reader/证据/角色/资源/executor未提供，Tool目录/flags/实际dispatch从未开启。

## 可执行例子与边界

1. `test_sql_reconcile_restart_duplicate_and_no_repeated_fees`：受控来源提供严格applied回执，保存效果与实际费用；实例重建后重复回执不多记账。`test_sql_new_process_resumes_same_fee_plan_after_lost_reply`在真实新进程重放已保存费用计划，子进程用公共Windows控制面loop factory和继承环境URL，不传/打印凭据。
2. `test_sql_effect_and_cost_are_independent_and_unknown_dimensions_held`：not_applied可记录非零confirmed费用；applied可保留pending费用；unknown可有已确认费用；缺观察维度继续held，不填0。`test_sql_missing_or_revoked_readers_keep_unknown_and_all_unobserved_holds`缺/撤销来源时不推断未执行。
3. `test_sql_fee_reply_loss_replays_fixed_plan_after_restart`、`test_sql_tool_finish_reply_loss_reuses_completed_receipt`、并发同回执/冲突回执：Budget/Tool提交后响应丢失，重复重放固定计划；同版本冲突/确定结论反转拒绝，不倒退效果或重复费用。
4. `test_sql_recovery_after_cancel_and_policy_revoke_does_not_admit_new_action`与到期恢复用例：原尝试实际费用清理可以继续，未来reserve/dispatch仍拒绝；`test_sql_tool_can_run_with_all_private_budget_policy_reads_blocked`以SQL守卫禁止Tool跨owner读取，`test_sql_tool_parent_chain_is_decided_by_execution_policy_port`验证统一真实父链拒绝。
5. `test_sql_effect_is_not_rolled_back_by_rejected_fee_update`：更丰富pending费用被现有BudgetService明确拒绝，真实applied证据仍保存；后来confirmed账单继续，不伪造完整Usage或旧账单完成。

上述SQL用例均为真实SQL测试代码，但本轮环境未运行到业务断言；受控Reader明确是组件fixture，不是实际provider/Runner回执。已经运行的31个新增单元覆盖真实C算法与端口协议，仍不能代替SQL/真实业务验收。

## 验证、回执与未通过项

```powershell
Set-Location E:/UAW/.worktrees/tool
.venv/Scripts/python.exe -m ruff check src/uaw/tool tests/unit/tool tests/integration/tool
.venv/Scripts/python.exe -m ruff format --check src/uaw/tool tests/unit/tool tests/integration/tool
.venv/Scripts/python.exe -m mypy --cache-dir .cache/mypy-tool src/uaw/tool
.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider --junitxml=tests/.artifacts/C/MS-T2b/unit.xml
.venv/Scripts/python.exe -m pytest tests/integration/tool -q -p no:cacheprovider --require-postgres --junitxml=tests/.artifacts/C/MS-T2b/sql.xml
```

- Unit：**97 passed，0 failure/skip**（原66＋新31），回执unit.txt/unit.xml。
- Ruff通过；28文件格式通过；Mypy strict 16个源码文件无错误；diff/staged diff whitespace通过。对应ruff.txt/format.txt/mypy.txt。
- SQL：**43 setup errors，0 passed/skip，exit 1**（原17＋新26）；共同原因`UAW_TEST_DATABASE_URL`缺失，测试尚未连接PG/执行断言。已实际用--require-postgres尝试，sql.txt/sql.xml保留此失败，未用跳过或mock假冒。
- ignored本机证据目录`tests/.artifacts/C/MS-T2b/`；environment.json保存真实位置、同步命令、基线及共享SHA256/检查范围；源码摘要与实际提交SHA一并保存。原MS-T2a被A接受的记录仍在DISPATCH，不把其17项通过当本包变更已通过。
- 未运行本包真实PG、全量整链路、真实LLM/生产Receipt/EvidenceReader/executor/可信IPC；没有数据库启动/迁移、密码/私有配置/.data复制或共享端口服务。

## A 后续要求、提案与回退

A安排受控PG和独立测试主体，在实际集成SHA重跑43项SQL与组合回归，失败由C修本包业务。A将`Container.execution_permissions`和读写`Container.budgets`明确注入；Reader须真实来源/签名/版本与当前数据访问，不能用tests fixture接产品。真实发送/执行前租约、fence、撤销/取消和句柄仍待完整MS-T2。

C-003的公共缺口待A决定：现有ReconcileRequest仅action_id/revision，真实receipt查找需权威Lookup/独立版本；EffectRecord.confirmed消费方必须查询outcome而非宣告成功；BudgetService新pending增量/最终费用调整与orphan未记账意图的清理规则需公共owner明定。没有私加字段/扩schema/写budget.accounting。本轮不新增事件/迁移/依赖，不启用flags/目录；D01/D03/D06未自行设定。

待SQL/接线接受与A发布下一基线，不自动开始完整MS-T2。回退由A revert源码提交`c78d37101a4c203cbe487f15cb5cabc063ca5f76`及后续公共接线，保留持久unknown/实际费用，代码回退不证明已撤销外部效果。没有真实业务动作发生。


# MS-T2c 交接追加 · 2026-10-08

状态：**统一核对入口、明确outcome读取及组件验证已交付；本工作区真实SQL待A实跑/接受，生产接线和完整MS-T2继续等待。** 原handoff保持原文；MS-T2b已由A合入ms-i2e，97单元＋43真实SQL通过，A仅将SQL模块改为`test_tool_reconciliation_postgres.py`解决同名收集冲突。本包保留这43项和模块名。

## 实际位置、基线与提交

- 目录`E:/UAW/.worktrees/tool`，分支`dev/tool`。
- 开工工作区干净；实际执行`git fetch origin --tags`、`git merge --ff-only ms-i2e`成功。同步后HEAD与`ms-i2e^{commit}`完全一致：**`ba2f3b0d9417e6d695eaa74c2f766217c98b01f1`**。无reset/rebase、历史改写或公共文件覆盖。
- `uv sync --frozen --extra agent-engine --link-mode copy`通过，91 packages checked；独立`.venv`及`.cache/uv`，Python 3.14.6，未重写锁。
- **源码与测试提交：`3d8cda36d1422a70fb877a87868affe587c1441c`**。本交接与C-004作为独立文档提交，A审阅dev/tool这两笔提交；文档提交实际SHA由Git日志及ignored environment.json给出，避免把自引用占位当SHA。
- 公共SHA256保留ms-i2e：schema `45161b36f2e81622e73f86c23b048cda8d55686e7045248f0394ab51d13dbe6b`；shared ports `453cd9cd21b92a77c6e370fc6f0463072a3903a2c6b5beee56dec4f93b0c27a5`；shared contracts `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b`；uv.lock `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`。

## 本轮改动文件

源码/测试提交7文件：

- `src/uaw/tool/receipt_lookup.py`
- `src/uaw/tool/facade.py`
- `src/uaw/tool/reconciliation.py`
- `tests/unit/tool/test_recovery_facade.py`
- `tests/integration/tool/recovery_fixtures.py`
- `tests/integration/tool/recovery_facade_child.py`
- `tests/integration/tool/test_tool_recovery_facade_postgres.py`

独立文档提交：本`docs/coordination/handoffs/C.md`追加与`docs/coordination/requests/C/C-004-ms-t2c-facade-outcome-wiring.md`。只有C允许路径；不改shared/schema/锁/composition/API/迁移、其他worker或其他worktree。A的active provider和pending Usage契约保留。

## 实际接口与行为

- 新内部`ActionReceiptLookupPort.find(action_id, ctx) -> Ref | None`，默认不提供生产实现；owning domain从独立已登记原action/attempt来源查找实际固定回执，复核当下恢复数据权限和完整绑定。查找不是执行权限、效果证明或记账完成。
- `ToolFacade(..., lookup=None, reconciler=None).reconcile(request, ctx)`严格消费已有ReconcileRequest，输出已有RuntimeToolruntimeReconcileResult。先冻结/校验仅action_id与严格整数expected_revision，额外receipt_ref等字段拒绝；Lookup前后校验真实原attempt/action/context，返回Ref仍由原ToolReconciler检查Reader/证据/全部绑定/版本/CAS/原费用计划。缺Lookup/Reconciler/实际Reader不可用；Lookup None仅missing，保留unknown/已有结果/额度。
- 恢复入口不调用新执行`_access`、invoke或discover；当下来源/证据Reader独立授权恢复数据，执行撤销、取消/过期后的原尝试清理与新动作准入区分。不新建action/attempt，不reserve/dispatch/retry、不授权重发。
- `ToolReconciler.check_action`只核对固定账本身份，不授权当前来源。`ToolReconciler.read_outcome(action_id,ctx)`与facade委托方法返回实际已接受ToolReconciliationReceipt wire；失败抛DomainError，async取消传播。
- read_outcome读取EffectRecord.receipt_ref的已接受固定版本和当前attempt核对记录，重新校验实际来源/证据/action/attempt/provider/receipt/Usage绑定，与已接受内容严格比较；同版本变化冲突、并发替代后stale，不跟随Lookup未接受新回执。返回复制，不写账本/调用预算服务。没有已接受回执不推断outcome；费用未完成/回复丢失/明确拒绝不妨碍独立真实效果读取。
- **confirmed和核对ok不等于applied、工具成功或Task完成。** 必须消费实际outcome；not_applied可有非零费用，unknown保留未知维度额度且不重发。费用完成来自BudgetState/实际UsageSettlement，不从效果或receipt Usage推断完成。
- MS-T2b固定原attempt/上下文/费用计划及CAS去重保留，来源和BudgetService均不在Tool会话事务锁内调用；未修改现有账本/预算核心实现。

## 接线、可执行例子与未决边界

[C-004接线说明](../requests/C/C-004-ms-t2c-facade-outcome-wiring.md)给出A实际Container.records/budgets的可选注入、默认不可用、成功/拒绝/重复与版本冲突示例、错误语义及outcome消费表。

1. `test_sql_facade_lookup_explicit_outcome_and_independent_fees`：只输入action_id/revision，经独立已登记受控来源查找；not_applied与0.03费用独立，unknown/pending保留0.01等未知额度，再读真实outcome。
2. `test_sql_facade_model_receipt_ref_rejected_before_lookup`及跨主体/attempt/Run/action/独立登记provider用例：额外或伪造绑定拒绝，没有核对新动作/费用写入。
3. `test_sql_facade_duplicate_restart_and_read_outcome_have_one_fee_plan`、并发、新进程：重建后查找原来源，固定结算去重。新进程只接收既有request/context，不接收receipt_ref或凭据。
4. 执行政策撤销＋取消后允许当前恢复数据读取；Lookup/Receipt/Evidence当前来源撤销拒绝。同版本body变化与未知新Lookup来源不能冒充已接受outcome。
5. 费用响应丢失仍能读已接受not_applied，再重放固定费用计划。新SQL预算守卫禁止reserve/dispatch，原执行阶段记录守卫禁止新增attempt/身份/发送；单元补read_outcome完全不调用预算、费用确定拒绝、超时/取消及并发替代。

以上SQL代码尚未在本工作区执行到业务断言。Lookup/Reader/角色/环境/提供方metadata均明示受控组件；未注册为产品能力，未使用真实LLM、Runner、IPC或executor。

## 验证命令、回执和未通过项

```powershell
Set-Location E:/UAW/.worktrees/tool
.venv/Scripts/python.exe -m ruff check src/uaw/tool tests/unit/tool tests/integration/tool
.venv/Scripts/python.exe -m ruff format --check src/uaw/tool tests/unit/tool tests/integration/tool
.venv/Scripts/python.exe -m mypy --cache-dir .cache/mypy-tool src/uaw/tool
.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider --junitxml=tests/.artifacts/C/MS-T2c/unit.xml
.venv/Scripts/python.exe -m pytest tests/unit/tool tests/integration/tool --collect-only -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests/integration/tool -q -p no:cacheprovider --require-postgres --junitxml=tests/.artifacts/C/MS-T2c/sql.xml
```

- **135 unit passed，0 failure/error/skip**：原97＋本轮38，unit.txt/unit.xml。
- Ruff通过（ruff.txt）；33文件格式通过（format.txt）；Mypy strict 17源码文件通过（mypy.txt）；diff/staged diff --check通过。
- 合并收集**205项**（135单元＋70 SQL），collection.txt，无同名单元/SQL模块冲突；原43 SQL＋本轮27，旧SQL文件未改。
- 真实SQL实际尝试：**70 setup errors，0 passed/failure/skip，exit 1**；唯一共同原因`UAW_TEST_DATABASE_URL`缺失。sql.txt/sql.xml记录原始错误，没有连接PG/执行断言，不以收集或内存fixture宣称SQL通过。
- ignored回执位置`E:/UAW/.worktrees/tool/tests/.artifacts/C/MS-T2c/`，包含unit.txt/xml、sql.txt/xml、ruff.txt、format.txt、mypy.txt、collection.txt及environment.json，后者保存真实基线/源码/文档提交、公共与本轮源码摘要。
- 未运行本包真实PG、全量组合/Agent闭环、生产Lookup/Receipt/EvidenceReader、真实provider/LLM/Runner/executor。未复制连接凭据/.data、未启动共享DB/迁移/端口服务。

## A 接受要求与回退

A在受控PG、随机隔离测试主体及实际集成SHA实跑全部70项SQL（保留原43回归）并组合审阅，失败由C修组件业务。A实现/接入独立已登记原attempt的生产Lookup及可信Reader，核对签名/来源/当前数据访问和固定版本；保留旧版本恢复能力，不能把fixtures登记为产品。当前Tool Runtime仍未绑，shared.ToolPort只有invoke；若挂新操作，公共port/HTTP/组装与实施范围由A处理。

C-003的pending增量预算/最终费用调整、orphan会计协调仍由A决定，本包没有扩EffectRecord或ReconcileRequest、私写预算账本或设定公共规则。没有新依赖/迁移/事件，不开放flags或工具目录；完整MS-T2、生产执行与D01/D03/D06继续等待，不自动扩包。

回退由A revert源码`3d8cda36d1422a70fb877a87868affe587c1441c`及后续接线提交，保留原持久unknown/费用/实际回执；代码回退不证明外部效果已撤销。本包没有真实业务dispatch。


# MS-T2d 交接追加 · 2026-10-08

状态：**四个连续里程碑已完成并交付可审阅源码；162单元与100个不同真实SQL用例通过，生产接线及完整MS-T2/P1-03等待A整链审阅接受。** 不重做此前已接受包；原handoff全部原文保留。没有读取D开发分支或修改其他worktree。

## 位置、固定基线和提交

- 实际目录`E:/UAW/.worktrees/tool`，实际分支`dev/tool`。开工工作区干净，`git fetch origin --tags`和`git merge --ff-only ms-i2g-start`成功；同步时HEAD与标签解析出的commit一致：**`0bd8e2b8387a46e16435dc033956c2b69bb1a859`**。未reset/rebase或覆盖公共文件。
- 按本worktree锁执行`uv sync --frozen --extra agent-engine --link-mode copy`，91 packages checked，Python3.14.6；私有`.venv/.cache/uv`，锁未更改。
- **阶段源码（里程碑1/2）：`27d17a3c2f3d2637ce5c7e386ae6eec3d2a9be63`**；阶段接口/样例文档：**`717c2371c407b6c5a7be083c9b8f601f5fd0d87f`**，C-005保留。阶段141单元＋3真实SQL通过；已向用户报告阶段SHA后继续后两项，没有等待A最终集成。
- **最终源码/测试（里程碑3/4）：`859f5d0f1ac90dc51e8500282b70d1acee924c06`**。A在dev/tool审阅阶段源码、阶段文档、最终源码和本次独立handoff文档提交。文档提交的实际SHA由Git日志和ignored environment.json记录，不以自引用占位假装实际SHA。
- 公共文件与固定基线字节一致：schema SHA256 `cc5dbc6ba7bdaba40529ed196fe1249176b49967f741ecf017e40275417a8c45`，shared ports `fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104`，shared contracts `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b`，uv.lock `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`。无shared/schema/锁/composition/API/迁移/其他worker变更。

## 实际改动文件

本包两笔源码提交合计15文件（最终增量提交14文件）：

- `src/uaw/tool/facade.py`
- `src/uaw/tool/invocation/dispatch.py`
- `src/uaw/tool/ledger.py`
- `src/uaw/tool/ports.py`
- `src/uaw/tool/providers/__init__.py`
- `src/uaw/tool/providers/text.py`
- `src/uaw/tool/receipt_store.py`
- `src/uaw/tool/results.py`
- `tests/integration/tool/test_text_dispatch_postgres.py`
- `tests/integration/tool/test_text_recovery_process_postgres.py`
- `tests/integration/tool/test_text_results_postgres.py`
- `tests/integration/tool/text_pipeline_fixture.py`
- `tests/integration/tool/text_recovery_child.py`
- `tests/unit/tool/test_durable_results.py`
- `tests/unit/tool/test_text_inspect.py`

本次独立文档：`docs/coordination/requests/C/C-006-ms-t2d-results-wiring.md`和本handoff追加；阶段C-005独立文档原文保留。仅C允许目录，ignored缓存/私有DB环境/回执不提交。

## 实现、公开内部接口与接线

- `ToolInvocation(registry,ledger,budgets,approvals,*,access=None,executor=None,estimates=None,results=None,prepare=None)`与可选`ToolFacade(...,invocation=...)`：normalize/固定配置与当前access→真实Approval waiting/批准recheck→原尝试账本→真实Budget reserve→当前gate→持久CAS dispatch意图与记账→当前角色/配置/权限/资源/批准复查→一次executor。所有外部await在Tool会话SQL事务锁外；缺executor/实现校验器/results/权限依赖预留前明确不可用。
- 实际`TextInspectExecutor(source,*,provider,currency)`、`TextInspectVerifier(provider_ref)`、`text_spec(provider_ref)`与`text_estimates(currency)`：唯一text参数，最大32768 UTF-8 bytes，原文不归一化；真实输出characters/utf8_bytes/lines/sha256，严格ProviderReceipt指向真实主体隔离raw blob。完整provider服务Principal固定在可信构造，不能从模型正文提供。固定本地免费计费定义、1次tool_call、实际纯计算wall_time；不从HTTP/Runner/confirmed推断成功或零费用，不联网、不读用户目录、不执行写入/exec。
- `ToolReceiptStore(ledger,blobs,*,provider_ref,provider,access=None,verifier=None)`实现严格`publish(receipt,ctx,*,authenticated_provider)->Ref`、`find(action_id,ctx)->Ref|None`、`read(ref,ctx)->ToolReconciliationReceipt`与实际证据`check(ref,ctx)->Ref`。独立provider记录、实际raw响应、严格usage.attempt_id、固定action/attempt/spec/provider/receipt绑定及当前恢复数据权限反复校验。缺实际来源或验证器不可用；Lookup不是授权，不从预算/EffectRecord生成回执。
- `ToolResults(source,reconciler).ready()/resume(call,ctx)`及`read_result(action_id,ctx)`：固定业务output_schema与独立真实文本核对后发布实际证据；原ToolReconciler分别接受效果和恢复费用，实际settlement usage Ref齐备后保存既有ToolResult，读取返回既有RuntimeToolruntimeInvokeResult。`ToolFacade.reconcile`仍严格接受既有ReconcileRequest，无额外receipt_ref；`read_outcome`返回实际明确ToolReconciliationReceipt。confirmed/reconcile ok不代表applied、工具成功或Task完成。
- 发送意图后的超时/异步取消/未保存响应保持unknown和未知额度；不能从超时、未记Budget dispatch或本地发送回执丢失推断未执行。原尝试只恢复已实际保存响应/固定费用计划，不新attempt/reserve/dispatch/retry。明确无意图的本次已准入reserve/send失败才释放原预留；畸形/冲突请求不能释放原尝试额度。
- 实际结果/Lookup/Reader无需新执行access，使用当前恢复数据权限；原取消/过期不阻止授权的原账务恢复，但权限撤销会拒绝读取旧结果。费用响应丢失时applied可独立读取，不能以效果确认代替实际费用Ref。原not_applied与费用非零、unknown维度保留逻辑由原70项回归覆盖。
- 具体构造、输入输出样例、命名记录/schema、错误与缺口见[C-006](../requests/C/C-006-ms-t2d-results-wiring.md)。新增命名行全部使用已有具体schema，无无约束Object表或迁移。raw/content固定version1，receipt hash固定实际ProviderReceipt＋ctx＋完整provider绑定；首次observed_at与发布Ref重放不变。

## 验证命令与实际回执

在本worktree运行`. ./ops/start-dev-db.ps1 -Session C`，独立Docker project `uaw-development-c`、loopback **55434**、独立volume，随机秘密仅生成于本地ignored `.data/dev-db.env`；未复制A配置、打印/提交URL、修改共享evidence、操作其他库或清除volume。随后`.venv/Scripts/python.exe -m alembic upgrade head`成功。

1. 最终单元：`.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider --junitxml=tests/.artifacts/C/MS-T2d/unit.xml` → **162 passed / 0 failures / 0 errors / 0 skipped**，18.25s。含原135与新27；测试权限/费用替身明确受控，单元不冒充SQL或真实LLM/Runner。
2. 首轮SQL：`.venv/Scripts/python.exe -m pytest tests/integration/tool -q -p no:cacheprovider --require-postgres --basetemp=E:/UAW/.worktrees/tool/tests/.artifacts/C/MS-T2d/tmp --junitxml=tests/.artifacts/C/MS-T2d/sql.xml` → **96 passed / 1 failed / 0 errors / 0 skipped**，624.35s。原70项全部通过。失败来自新测试decision误用deny，公共枚举实际为decline；修正C测试，没有改公共契约。原回执保存为`sql-initial.xml/sql-initial.txt`。
3. 最终新增SQL全量复验：`.venv/Scripts/python.exe -m pytest tests/integration/tool/test_text_dispatch_postgres.py tests/integration/tool/test_text_results_postgres.py tests/integration/tool/test_text_recovery_process_postgres.py -q -p no:cacheprovider --require-postgres --basetemp=E:/UAW/.worktrees/tool/tests/.artifacts/C/MS-T2d/tmp-final --junitxml=tests/.artifacts/C/MS-T2d/sql-new.xml` → **30 passed / 0 failures / 0 errors / 0 skipped**，332.47s。新增缺approval及冲突请求保护和独立新Python进程恢复也通过。
4. **真实SQL覆盖合计100个不同通过用例＝原70＋最终新增30，最终无未通过用例。** 这是两份实际回执的覆盖合计，不是一次100项完整运行；旧70模块与基线字节相同，最终修正只影响新增路径，全数新SQL已复跑。旧cancel/expired/policy/provider/resource变化、主体/attempt/provider隔离、not_applied费用独立、unknown额度、固定CAS费用计划和并发核对保留。新增覆盖实际text输入→审批→预留→一次发送→真实raw/ProviderReceipt→严格输出→publish/Lookup→原reconcile/outcome→ToolResult→重复/重启读取，明确无来源/缺依赖、拒绝/取消/撤销、响应/发布/费用丢失、schema/语义错误、回执/结果篡改、未知不重发和新进程无executor恢复。
5. `.venv/Scripts/python.exe -m ruff check src/uaw/tool tests/unit/tool tests/integration/tool`通过；`ruff format --check` **45 files already formatted**；`.venv/Scripts/python.exe -m mypy src/uaw/tool` **22 source files通过**；`git diff --check`通过。

ignored回执：`tests/.artifacts/C/MS-T2d/{unit.xml,unit.txt,sql-initial.xml,sql-initial.txt,sql-new.xml,sql-new.txt,ruff.txt,format.txt,mypy.txt,environment.json}`；阶段回执保留在`tests/.artifacts/C/MS-T2d-stage/`。未隐藏首轮失败；没有当前未解决测试失败。真实SQL与blob、实际文本计算、独立进程读取是真实实现；角色/资源/恢复权限Reader仍明示受控组件，不是生产授权或真实LLM/Runner回执。

## A尚需接线与未验收边界

- A提供实际ToolAccess/current角色环境、原资源Reader与配置/Run/ExecutionPolicyPort、真实Approval/Budget/State、可信固定provider Principal和当前恢复数据权限；将最终source/Verifier/results/executor注入既有Facade。不能注册C受控测试Reader/role metadata为产品能力。默认Container的Tool Lookup/Reader/executor仍待挂载，缺依赖明确unavailable。
- C-005阶段结果消费port现补`ready()`；A提前组装应按C-006使用实际ToolResults，阶段raw store替换为ToolReceiptStore。不需要修改公共请求或EffectRecord。实际内部本地text工具只有A明确登记固定spec与真实环境绑定后才可用，C未开放产品目录/flags。
- pending增量预算规则、orphan会计协调仍属A；无响应/坏输出保留实际记录与未知额度供可信恢复，不虚构not_applied或自行释放已发送费用。A须保持实际预算currency与本地tariff一致。
- 本包没有真实产品API/用户权限整体接线回归，也没有网络LLM、Runner/IPC或用户文件/写入/exec验证。D01/D03/D06不自行决定，固定用户模型不替换；完整MS-T2/P1-03仍待A整链验收，不扩入下一包。


# MS-T2e 交接追加 · 2026-10-08

状态：**四个连续里程碑已完成，权限先行混合召回与有界SQLite索引组件交付；218单元、124个不同真实SQL用例通过，阶段/原失败回执保留。** 真实embedding提供方、公开Runtime装配及完整MS-T2/P1-03仍待A整链验收。本包后停止，不自动扩包；旧MS-T2d与全部原handoff保留，未读其他worker开发分支。

## 位置、固定基线、阶段与最终SHA

- 实际目录`E:/UAW/.worktrees/tool`，分支`dev/tool`。开工干净，`git fetch origin --tags`与`git merge --ff-only ms-i2h-start`成功，HEAD与标签commit核对一致：**`f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8`**。没有reset/rebase或覆盖公共文件；包中未更换基线。
- 本worktree按uv.lock执行`uv sync --frozen --extra agent-engine --link-mode copy`，91 packages checked；沿用独立`.venv/.cache/uv`，未改锁或复制A依赖/凭据。
- **前两里程碑阶段源码：`ba0d11ef4533e71ad8147d86abaef04bd07c114c`**；固定异步接口/接线样例文档：**`8ed211ecb11fb12a7e644d7809f8e7b5c3831a30`**。已向用户报告实际SHA后继续后半包，没有等待最终集成。C-007原文保留。
- **最终源码/测试：`27fe04f22cf19f734f776da326e79dc52eb7b83e`**。阶段源码4文件，最终增量5文件；两笔源码合计8不同源码/测试文件。C-008与本handoff独立文档提交，文档实际SHA由Git日志及ignored environment.json给出，不使用自引用占位。
- 公共文件与ms-i2h-start字节一致：schema `595ebe8f9173b5a6c8608dfac9f339f1c4c7f8e7e5f0599687f04bf6511ef90d`，shared ports `fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104`，shared contracts `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b`，uv.lock `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`。没有shared/schema/迁移/锁/composition/API/Run/其他worker修改。

## 改动文件

本包源码/测试：

- `src/uaw/tool/embedding.py`
- `src/uaw/tool/facade.py`
- `src/uaw/tool/index.py`
- `src/uaw/tool/registry.py`
- `src/uaw/tool/retrieval.py`
- `tests/integration/tool/test_retrieval_postgres.py`
- `tests/unit/tool/test_retrieval.py`
- `tests/unit/tool/test_vector_index.py`

文档：`docs/coordination/requests/C/C-007-ms-t2e-stage-retrieval.md`（阶段独立提交）、`docs/coordination/requests/C/C-008-ms-t2e-index-wiring.md`与本handoff追加。旧C handoff所有字节原样作为前缀保留，旧失败与接受记录不覆盖。ignored回执、cache、私有DB配置不提交。

## 固定内部接口、行为与A样例

- `ToolRetriever(registry,access,*,mode="semantic-required",embeddings=None,index=None)`与`async discover(query,categories,max_candidates,ctx)->DiscoveryResult`。`ToolFacade(...,retriever=None)`可选注入，同一Registry；默认无retriever完全沿用原小目录，原invoke/result/reconcile接口不改。模式仅可信构造可配；lexical-only显式省略语义，不静默降级，semantic-required缺真实embedding明确unavailable。
- `ToolEmbeddingPort.current(ctx)->EmbeddingBinding`及`embed(texts:tuple[str,...],ctx)->EmbeddingBatch`；binding精确provider/configuration-model Ref/hash、维度1..4096、`tool-projection-json-v1`。batch精确actual UTF-8摘要/顺序/数目，向量有限数值且非零有限norm，拒绝NaN/Inf/bool/维度或绑定变化。没有网络adapter/hash或random伪语义向量；测试NumericalEmbedding仅受控数值协议，不证明语义质量。
- 从实际Registry固定revision/immutable ToolSpec/adapter entries，先当前role/category/有效scope权限/deny、flags、环境与active Tool provider过滤；未允许工具描述不送embedding。query上限8192 UTF-8 bytes、工具上限128、CandidateLimit 1..32；metadata仅允许工具原id/description/categories规范JSON，描述是资料。词法casefold子串与cosine>0向量召回，RRF k60两路等权、按score/id/version确定融合；返回既有ToolCandidate/DiscoveryResult，LLM选择，不执行或授予工具调用。
- `IndexPlan(namespace,binding,documents)`固定工具完整Ref/hash、provider/version、投影text_hash和embedding提供方/model/维度/规范版本，namespace为完整Principal含kind/session摘要。`ToolVectorIndexPort.read(plan)->tuple|None`、`replace(plan,vectors)->None`与`invalidate(namespace)->None`；`SQLiteVectorIndex(trusted_path,*,max_bytes=16MiB,namespaces=8)`实际结构化两表和二进制float64，非注册/权限/业务状态权威。
- SQLite整代原子替换、外键删除、重启完整读、checksum/维度/有限数值复查；metadata不同明确miss重建，损坏/unrecognized明确index_invalid，无静默词法降级。namespace数1..32与文件page硬限，容量包含rollback journal/header预留、无WAL累积，默认128x4096实际保存通过。空间耗尽/失败回滚保留原完整generation，显式invalidate清理。缓存只存索引元数据/向量，不保存用户正文/query、凭据、权限/审批结果或Tool调用结果。
- 每个embedding/current/index await后和返回前重新读取当前ToolAccess完整快照、Registry及embedding绑定；角色/flags/provider变化即使不改变候选集合也拒绝旧观察，工具修订/卸载同样拒绝。索引等待后embedding变化会在文本发送前拒绝。整体期限限异步等待，Timeout明确deadline_exceeded/retrieval_interrupted，异步CancelledError向调用方传播。后台SQLite有限事务可在取消后完成/回滚，但不返回候选、不产生Tool发送或业务执行授权。
- `ToolRegistry.unregister(tool_ref,*,expected_revision)->revision`仅可信内部CAS卸载，没有新公开API；旧index不能恢复安装或权限。非空ModelToolSet验证仍交A实际当前工具来源，不使用检索分数作为授权。ctx/Ref/query不能自证完整session/角色；实际Access及embedding current由A可信来源提供，固定用户模型不改。
- 详细输入/输出、默认兼容、索引格式/容量/失败/取消边界及A实际构造样例见[C-008](../requests/C/C-008-ms-t2e-index-wiring.md)。标准库SQLite无需新依赖或公共DTO/flag提案；若产品需要配置字段由A另行公开发布，本包没有私加公共字段。

## 独立环境、命令和实际回执

在C worktree进程`. ./ops/start-dev-db.ps1 -Session C`，own Docker project `uaw-development-c`/独立volume，loopback **55434**；私有随机配置只在当前ignored `.data/dev-db.env`，未打印URL/密码或复制A配置。按锁`.venv/Scripts/python.exe -m alembic upgrade head`成功；未访问其他session库、共享evidence、其他worktree或执行down -v。

1. 阶段Tool单元：`pytest tests/unit/tool -q -p no:cacheprovider --junitxml=tests/.artifacts/C/MS-T2e-stage/unit.xml` → **186 passed / 0 errors/failures/skips**，24.32s，含原162＋新24。初始185passed/1failed为测试非词法query中短词a被既有词法substring命中，修正测试query为明确无字面命中的unmatchedzyx；不是调整融合以迎合替身。initial-unit.xml/txt及初始Mypy标注失败回执保留。
2. 最终全部Tool单元：`.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider --junitxml=tests/.artifacts/C/MS-T2e/unit.xml` → **218 passed / 0 failure/error/skip**，19.02s＝原162＋检索24＋索引32。实际SQLite覆盖重启/新Python进程、原子并发、损坏、空间失败保留原代、绑定变化、卸载、跨session namespace、query不保存、取消/期限及默认128工具x4096维物理边界。
3. 原调用/结果SQL完整模块：`pytest tests/integration/tool/test_durable.py tests/integration/tool/test_tool_reconciliation_postgres.py tests/integration/tool/test_tool_recovery_facade_postgres.py tests/integration/tool/test_text_dispatch_postgres.py tests/integration/tool/test_text_results_postgres.py tests/integration/tool/test_text_recovery_process_postgres.py -q -p no:cacheprovider --require-postgres --basetemp=E:/UAW/.worktrees/tool/tests/.artifacts/C/MS-T2e/tmp-original --junitxml=tests/.artifacts/C/MS-T2e/sql-original.xml` → **99 passed / 1 failed / 0 error/skip**，740.98s。既有并发一次发送用例触发20秒wait_for TimeoutError，栈停在实际结果source复查；未证实死锁、重复发送或效果错误。原六个SQL模块全部与基线字节一致。
4. 定向复跑原并发模块：`pytest tests/integration/tool/test_text_dispatch_postgres.py -q -p no:cacheprovider --require-postgres --durations=4 --basetemp=E:/UAW/.worktrees/tool/tests/.artifacts/C/MS-T2e/tmp-original-recheck --junitxml=tests/.artifacts/C/MS-T2e/sql-original-recheck.xml` → **3 passed / 0 error/failure/skip**，42.02s，并发15.38s。没有修改原20秒timeout、一次发送断言或源码/原测试；保留首轮失败，不把成功复跑当性能承诺。
5. 新检索SQL：`pytest tests/integration/tool/test_retrieval_postgres.py -q -p no:cacheprovider --require-postgres --durations=6 --basetemp=E:/UAW/.worktrees/tool/tests/.artifacts/C/MS-T2e/tmp-retrieval-frozen --junitxml=tests/.artifacts/C/MS-T2e/sql-retrieval-final.xml` → **24 passed / 0 failure/error/skip**，84.97s，最终冻结源码对应回执。首次21项70.61s通过、补边界后24项72.46s通过的进度回执亦保留，不重复计入节点数。
6. **SQL不同通过节点覆盖124＝原100＋新24，最终没有未通过节点。** 这是实际初始/定向复跑/最终新增回执的去重覆盖，不是一次124项完整运行。原unknown/费用独立/审批/取消/版本/重复/并发/响应丢失/跨进程结果全部回归。新增真实SQL消费已发布RunToolAccessSources/Role绑定/Policy/配置/固定用户模型，覆盖过滤前不外发隐藏工具、角色/绑定/provider/政策/取消在embedding或index等待中变化、完整principal/kind/session/scope/model隔离、cache损坏/并发/重启和版本重建、显式缺embedding模式及deadline/异步取消，无调用/费用状态改变。
7. `.venv/Scripts/python.exe -m ruff check src/uaw/tool tests/unit/tool tests/integration/tool`通过；`ruff format --check` **51文件已格式化**；`.venv/Scripts/python.exe -m mypy src/uaw/tool` **25源码无问题**；`git diff --check`通过。

actual ignored回执`tests/.artifacts/C/MS-T2e/`含unit.xml/txt、sql-original.xml/txt、sql-original-recheck.xml/txt、sql-retrieval-initial.xml/txt、sql-retrieval-progress.xml/txt、sql-retrieval-final.xml/txt、ruff/format/mypy/migration和environment.json；阶段`.artifacts/C/MS-T2e-stage/`的initial-*和通过回执均保留。新SQL模块`test_retrieval_postgres.py`与单元`test_retrieval.py/test_vector_index.py`不同名，不引入测试收集冲突。

开发中一次写入新SQL命令的自动审批审查因账户用量限制未完成，命令未执行；用户继续后重新受审执行，未绕过权限审查。实际SQL/PostgreSQL、结构化SQLite、原Tooltext计算和恢复来源均是真实现；embedding已知数值、连接metadata仍明示受控测试组件，不冒充真实embedding/LLM/Runner或生产用户确认。

## A接线、未验收及性能边界

- A注入实际当前RunToolAccess/角色/权限/flags/环境/provider来源，按C-007实现管理员配置的真实ToolEmbeddingPort；current/embed须独立处理embedding身份/可用性/撤销/授权/自身计费和取消，不把ctx回显当来源。C未改用户固定模型或D06策略，没有真实网络embedding/语义质量回执。
- A以可信配置提供私有index path/容量/namespace与显式lexical-only或semantic-required，注入ToolFacade optional retriever；旧小目录默认兼容，其他invoke/results参数沿用，不改共享schema/依赖/flags或公开API。缓存可重建、不为Tool注册或权限数据权威；ModelToolSet继续A当前适配器验证。
- 当前默认产品目录/flags没有开放，受控NumericalEmbedding不注册为产品能力，不执行/安装/写入/exec。原SQL并发超时后无改动复跑通过，但实际环境延迟需要A后续测量，不能宣称生产性能或真实语义任务已验收。
- 无当前失败节点；真实embedding提供方、整链Agent/公开Runtime/产品用户权限及语义质量未实跑，仍明确待接线/验收。本包停止，完整MS-T2/P1-03、D01/D03/D06不自行接受或设定。


## 2026-10-09：MS-T2f 办公纯参数工具、有限适配器路由与原尝试恢复

- 实际worktree：E:/UAW/.worktrees/tool；实际分支：dev/tool。
- 实际基线：ms-i2i-start / **d8023eb07e1460961782f297697da7428f6ad247**。
  开工干净，fetch origin --tags、merge --ff-only、HEAD/tag核对、uv sync --frozen已成功；没有reset/rebase。
- M1源码：63857e4d684ef3d9581778dc443126a5b84f3f03；M1说明：0f4aa7106f4ba051cadfac029d20736cb4cdbf14。
- M2源码：5387624a69db68297bed78297bcb414463e25fe0；M2说明：bb53f2bbc7bc01ca8bc45280f667cc1e7ebe7a45。
- 最终源码/测试：**b09fb7d789026be69a26b5493aa3a7da13649be5**。
  本handoff与C-010在源码之后独立提交，实际handoff SHA由交付报告和verification-index.json记录。

实际文件：新增src/uaw/tool/providers/{local,arithmetic,json_data,multiplex}.py、
src/uaw/tool/parameter_sources.py；修改src/uaw/tool/results.py的可选依赖ready检查。
新增tests/unit/tool/test_office_calculations.py、test_office_routing.py；新增
 tests/integration/tool/office_pipeline_fixture.py、office_recovery_child.py、
test_office_tools_postgres.py、test_office_recovery_postgres.py。
说明为C-009-ms-t2f-stage-tools.md、C-010-ms-t2f-final-wiring.md及本段；其他session和公共文件未修改。
原text及原70/100/124项SQL文件保留；原handoff的63213字节完整保留后追加。

公开接口：arithmetic_spec/arithmetic_estimates/calculate、ArithmeticExecutor/Verifier；
json_data_spec/json_data_estimates/inspect_json、JsonDataExecutor/Verifier。
ToolExecutorBinding/ToolOutputVerifierBinding、ToolExecutorRouter(bindings)/ToolOutputVerifierRouter(bindings)
固定完整ToolRef/hash/provider及实际实现，沿用execute/verify，executor.check作prepare。
PureParameterResourceReader(registry,access,tool_refs)及PureParameterRecoveryAccess(resources,ledger,authority=)
提供精确三工具空资源来源及原attempt当前数据权威委托；ready仅检查嵌套来源已接线，不是权限缓存。
固定参数/Spec/错误/构造和可消费样例详见[C-009](../requests/C/C-009-ms-t2f-stage-tools.md)与
[C-010](../requests/C/C-010-ms-t2f-final-wiring.md)。没有新增公共DTO/EffectRecord字段/迁移/依赖。

两工具实际有界本地纯计算，不eval、脚本、网络或本机项目文件。34位Decimal/ROUND_HALF_EVEN和
百分比定义固定；JSON拒绝重复键/非有限数/超深/超大/孤立代理字符，不修复用户原文。
规范结果使用原账本/审批/BudgetStatePort/一次发送/ProviderReceipt/实际Blob/发布和Lookup/Reader。
效果和费用分别处理，原attempt与固定计划重启恢复；unknown不换attempt重做、不放弃额度。
不从HTTP/Runner ok推断工具成功/零费用；已核对/confirmed/applied/ToolResult成功不意味着Task完成。
取消后原数据权限允许时可恢复，不转为新执行授权；撤销数据权限仍拒绝。
没有持有Tool会话锁嵌套调用BudgetService，未启用flags或自动登记产品目录/受控Reader。

实际验证（自身55434，dot-source ops/start-dev-db.ps1 -Session C；alembic upgrade head；
所有SQL明确--require-postgres，独立ignored根tests/.artifacts/C/MS-T2f）：

| 范围 | 实际通过/失败回执 |
| --- | --- |
| 全部C单元 | all-unit-final：316通过（原218+新98），0失败/错误/跳过 |
| 原Tool全部SQL | original-sql：124通过，543.42秒，含原检索/索引24 |
| 新工具链初次/复验 | office-sql-initial：30通过/6失败；office-sql-fixed：36通过/3测试字段失败 |
| 最后三节点修复 | mixed-final-sql：3通过/36 deselected；字段为既有tools，非skip |
| 新恢复SQL | office-recovery-sql：15通过，194.55秒，含真实新进程无executor恢复 |
| 原text最终复验 | text-final-sql：30通过，340.53秒，不重复计数 |
| 静态 | Ruff通过，62文件format-check通过，Mypy30源文件通过，diff-check通过 |

新SQL去重54项，全部SQL最后178个不同节点通过，无最终失败/错误/跳过；不伪造一次178全通过。
verification-index.json仅索引原JUnit和去重的最后回执，保留所有失败和修复txt/xml。
初次核心/路由单元的Decimal测试traps写法、Windows超长ID、受控receipt字段等也保留并修正，
未改公共契约。两工具与text覆盖一次发送并发、审批参数变化、当前provider真实SQL撤销、取消、
数据撤销、响应丢失、原费用计划回复丢失、错误验证器/输出篡改、缺Reader/来源及跨主体/session/attempt。
受控角色/provider元数据与当前数据权威明确标注；实际计算/Blob/SQL/ApprovalService/BudgetService
真实实现不能证明真实DeepSeek选择或生产授权已配置。

未通过/接线要求：无未通过的最终组件测试。A仍需合法本地provider/角色/目录/组装与当前完整
Run/owner/session/model/scope/provider数据权限authority；C默认缺来源仍明确不可用。原RunToolRecoveryAccess
的PureText类型可由A在自身域内提取/适配，消费C精确Reader.entry，不扩大为通用空Reader。
同provider可三工具共Source，跨provider由A选择对应Source/facade，不能误接聊天执行器。
真实固定DeepSeek选择、Task交付/终态及完整MS-T2整链验收归A；不依赖D开发分支、不自动扩包。

交付期间自动审批额度耗尽导致一次提交命令未执行，用户“继续”后按同授权重新审查成功。
全部测试结束后额外启动数据库探查因DockerEngine管道缺失失败，后续查询脚本未执行，保留
post-verification-db-start-failure.txt；已通过SQL新进程Database.check确认0003_attempt_identity。
复跑需先恢复Docker，再用C脚本启动本库，不复制A凭据/配置或使用其他端口/库/共享evidence。


## MS-T2g：file.read、实际文件证据与独立原费用恢复（2026-10-10）

Session C / MS-T2g / P1-03组件交付；完整MS-T2及生产整链仍待A接受。
实际目录 E:/UAW/.worktrees/tool，实际分支 dev/tool。开工工作区干净，fetch origin --tags后
merge --ff-only ms-i2j-start；HEAD/tag当时均为 abb4590f2bfe53c601e0f6a4a3b65447ba4ec502。
uv sync --frozen --extra agent-engine --link-mode copy，自己的.cache/uv/.venv，无锁改动。
公共契约0.1；contracts/uaw.schema.json SHA256 019b15c29d05c987ad1242c10ef17e2f825a216df0398ecbf4f70fd80a12232f；
uv.lock SHA256 a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f。
公共schema/shared/锁/composition/API/其他worker均未改。

源码提交：M1 c8b5676d4cb65a65a38391b304095600b0ffed54；阶段说明9195a2e。
M2 6abd666262df449a7e6d3c374613a7326944250b；接线阶段f9b661c。
M3/M4 a9847f9abc0e1780739228b66f9ded7d2874968d；最后源码修正
5b7749d0e80f7576362dd5736e0d89ac779e01a5（实际页范围和显式未知金额上限）。
本次handoff/最终接线说明独立于上述源码提交。

改动文件（相对固定基线）：
- docs/coordination/requests/C/MS-T2g-stage-file-port.md
- src/uaw/tool/ledger.py
- src/uaw/tool/providers/file_read.py
- src/uaw/tool/providers/file_store.py
- src/uaw/tool/receipt_store.py
- src/uaw/tool/results.py
- src/uaw/tool/schema.py
- tests/integration/tool/file_pipeline_fixture.py
- tests/integration/tool/file_recovery_child.py
- tests/integration/tool/test_file_pipeline_postgres.py
- tests/integration/tool/test_file_recovery_postgres.py
- tests/unit/tool/file_evidence_fixture.py
- tests/unit/tool/test_file_evidence.py
- tests/unit/tool/test_file_ports.py
- docs/coordination/requests/C/MS-T2g-final-wiring.md
- docs/coordination/handoffs/C.md（仅追加；原69076字节原样保留）

公开接口/接线：file_read_spec(provider_ref)固定file.read@1、categories=file、workspace.process、
file_access、read与完整ToolRef hash，无自动重试；ToolFileReadBridgePort.ready/resolve/execute/recover
消费完整原call/spec/ctx；FileReadEvidence固定command_ref/receipt_ref、RegisteredReceiptCommand、
实际RunnerReceipt、原immutable完整snapshot、实际selection和独立登记next_cursor。
file_estimates(currency, money_ceiling=actual_bound)要求显式真实货币预留上限，缺失503；
不默认为零、不从Runner ok推收费。A已有实际估算向量可直接注入原ToolInvocation。
FileResourceReader(provider_ref, bridge)接ApprovalAuthority；FileReceiptStore(ledger,blobs,
provider_ref=,provider=,access=current_data_authority,bridge=,signatures=)接原Lookup/Reader/evidence；
source.verifier=FileReadVerifier(source)，FileReadExecutor(source,provider=)及executor.check接原精确路由。
原ToolResults/Reconciler/Facade继续使用；缺真实桥/签名/数据权限/执行器/验证器发送前明确不可用。
read_observation(action_id,ctx)返回经当前数据权限和实际原来源核对的内部证据；read_raw也再验原来源。
内部完整snapshot不可直接暴露模型/HTTP；正文使用实际FileContent片段。
recover_file_accounting(ledger,budgets,ctx)->原UsageSettlement仅重放已接受原费用观察/已有固定计划，
消费当前BudgetStatePort/BudgetPort账务权限，不读正文/root/journal、不新建观察/attempt或发送。

成功例子：真实审批记录approved后invoke返回既有ToolResult，data为实际UTF-8 FileContent；
FileContent.location是实际页/行selection、content_hash是原整个文件hash；usage_ref仍可pending。
拒绝例子：缺port/金额来源503；当前root/device/key/data撤销、跨主体/project/provider/attempt、
旧摘要/坏签名/范围不符不能返回正文或成功。非空project_id保持原Run/Tool边界拒绝。
重复例子：原call/ctx恢复相同ToolResult/原receipt/Usage，不再执行/open；变参数/版本/hash拒绝；
unknown无原journal保留held，新attempt拒绝。核对confirmed/ok/applied不等于Task完成。

持久状态由Tool独占原tool.*账本，新增tool.file.command.refs/commands/owners/receipt.refs/
runner.receipts/snapshot.refs/selections/fragment.refs/contents/observation.refs，分别使用既有
Ref/RunnerCommand/Principal/RunnerReceipt/Location/FileContent；无私有通用Object或新公共DTO。
原全文件与实际返回片段Blob分开；整体hash与fragment Ref摘要语义不同；原观察Ref绑定完整
command/receipt/owner/device/snapshot/selection。固定CAS/原费用计划重启去重；Tool事务内不调用
Bridge/Reader/签名/Blob/BudgetService。await前复制严格嵌套wire，防止端口修改原Usage/正文。
普通输入64KiB边界不扩大；仅具名FileContent/ToolResult输出信封有界512KiB，支持转义后的64KiB原文。
原结果恢复查独立登记/journal/原快照；文件改变/删除不能新读替代，unknown不重发。
取消/过期后的原读取与新执行准入区分；费用plan可在当前账务权限下独立恢复，root/key撤销仍不准
读正文。原pending Usage省略未知维度；明确预留的money/tool_calls保留held，不伪造零费。

实际验证：自己的. ./ops/start-dev-db.ps1 -Session C（loopback55434）；锁定.venv运行
python -m alembic upgrade head。SQL明确--require-postgres，独立basetemp和随机主体清理；
不复制A配置/凭据、不写共享evidence。所有txt/xml在ignored tests/.artifacts/C/MS-T2g。

| 范围 | 实际回执 |
| --- | --- |
| 全Tool单元 | final-unit-ceiling.xml：358通过，21.71秒，0失败/错误/跳过 |
| 原全部Tool SQL | original-sql.xml：178通过，1368.03秒，0失败/错误/跳过；保留原70/检索/索引/text/办公模块 |
| 新文件SQL首次完整 | m4-sql-resumed.xml：36通过/2分页fixture幂等冲突失败，658.38秒 |
| 分页修复与最后实际范围 | page-fixed.xml：2通过114.88秒；page-range-final.xml：2通过105.61秒 |
| await嵌套证据/Usage变更 | mutation-sql.xml：1通过30.55秒 |
| 撤销后独立费用恢复 | accounting-sql.xml首轮1通过/1取消ledger字段断言失败；accounting-sql-fixed.xml：2通过16.61秒 |
| 最后非零未知金额/范围 | final-ceiling-sql.xml：6通过197.91秒，0失败/错误/跳过 |
| 静态 | Ruff通过；71文件format-check；Mypy32源码通过；git diff --check通过 |

新SQL去重41个不同节点，连原178共219个不同真实SQL最终全通过；verification-index.json仅索引
实际JUnit/每节点最后回执，不虚构一次219全通过。358单元包含原316+新增42；重复复验不累加。
单元命令python -m pytest tests/unit/tool -q -p no:cacheprovider；原SQL命令python -m pytest
 tests/integration/tool -v -p no:cacheprovider --ignore=tests/integration/tool/test_file_pipeline_postgres.py
 --ignore=tests/integration/tool/test_file_recovery_postgres.py --require-postgres；新SQL两模块同上述
 --require-postgres，修复选择-k仅受影响节点。首轮M1严格JSON fixture/Windows长ID、M2 Principal缺
 auth_session_id、SQL runner包导入路径错误、中断无XML、分页重复审批request_id和取消ledger断言
全部保留原回执并修复。最后无未通过组件节点；中断记录不计通过。

实际WindowsReadHandle读取临时测试根、真实Ed25519签名核验、SQL/Blob/ApprovalService/BudgetService；
当前角色/provider元数据/root/控制端/分页/key目录为明确受控测试组件。没有生产Runner dispatch/IPC、
真实人机确认、真实LLM或产品能力的本包验收；受控Reader未登记产品，flags/用户固定模型未改。

A接线缺口/要求详见[MS-T2g-stage-file-port](../requests/C/MS-T2g-stage-file-port.md)和
[MS-T2g-final-wiring](../requests/C/MS-T2g-final-wiring.md)。真实控制端、当前owner/session/project/root/
device/key权威、原命令登记/journal/immutable snapshot和cursor registry由A注入；D负责真人本机确认。
基线Runner只支持whole/text_span，生产lines/cursor尚待实际桥；C不读D开发分支。非空project_id须A
发布统一Run/Tool项目准入及恢复权限；C没有单方面解除。新确认费用Reader/pending增量/orphan仍归A。
file.read用专用FileReceiptStore/ToolResults；即使同provider也不能拿它充当text/算术/JSON共用Source；
A按完整原ToolRef/hash/provider选择对应invocation/results/source/reconciler bundle，恢复查原attempt。
旧三个工具原Source和接口兼容，原178SQL已回归。没有新迁移或依赖要求。

最终源码与本handoff分开提交；保留原所有提交和handoff；不reset/rebase、不开放flags/目录/网络/
本机写入exec、不自动扩下一包。整条A↔D用户确认/Agent/Artifact/Task完成链和公共冲突合入由A验收。


## MS-T2h：原文件资料 owning Reader、不可变引用与账务独立恢复（2026-10-10）

Session C / MS-T2h / P1-03、P1-08组件；真实产品Context/Artifact/Task及MS-T2整链由A验收。
实际目录E:/UAW/.worktrees/tool，分支dev/tool。前次查询ms-i2k未正式发布时仅只读，没有代码改动；
本次DISPATCH正式准确SHA及远端tag一致后，干净fetch origin --tags，merge --ff-only ms-i2k-start，
核对当时HEAD/tag准确为b7b79b150470a80f37b28fd52a2177f6de5b3124。uv sync --frozen
 --extra agent-engine --link-mode copy，自己的.cache/uv/.venv，91包锁定；未改锁。
MS-T2g源码5b7749d/交接780d3c4为当前历史祖先；原358单元/219SQL及原失败回执不覆盖。
公共契约0.1；schema SHA256 d54bd0218df40fd988f9d68a1635c051fd38031e47130591562f6d1f94b51056；
uv.lock SHA256 a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f。

提交：M1 5c8854c713c6a9aa1f265016f5d6e875688f10e2 / 阶段说明815544c；
M2 54d474e2f6492bd5877df0cfb4ba358ab3cf867d / 阶段接线f2b55e3；
最终源码3ed6ef3434c024d00e6e7794e5bace28914fe426（含M2运行实现与全部最终测试）。
本次handoff/最终说明独立提交；不reset/rebase/stash，保留所有旧提交/回执。

修改文件（从正式固定基线）：
- docs/coordination/requests/C/MS-T2h-stage-material-reader.md
- src/uaw/tool/providers/file_material.py
- src/uaw/tool/providers/file_store.py
- tests/integration/tool/file_recovery_child.py
- tests/integration/tool/test_file_material_bridge_postgres.py
- tests/integration/tool/test_file_material_postgres.py
- tests/integration/tool/test_file_material_recovery_postgres.py
- tests/unit/tool/test_file_material.py
- docs/coordination/requests/C/MS-T2h-final-wiring.md
- docs/coordination/handoffs/C.md（只追加；原77898字节保持原样）

固定接口：FileMaterialReaderPort.export(action_id,ctx)->FileMaterial / read(material_ref,ctx)->FileMaterial；
FileMaterialAdapter(source:FileReceiptStore|None,limits=FileMaterialLimits())实现当前owning数据Reader，
与A assemble_file_tool(...).receipts对接。M1/M2签名见
[stage-material-reader](../requests/C/MS-T2h-stage-material-reader.md)，具体成功/拒绝/重复样例见
[final-wiring](../requests/C/MS-T2h-final-wiring.md)。默认16384字符/64KiB UTF-8；更小界限拒绝413，
不截断/拼页/Unicode或换行规范化。实际A RegisteredFileBridge只whole≤16384字符，
lines/text_span/cursor保持503；C没有扩大生产能力或从新打开补全原snapshot。

FileMaterial内部不可变canonical bytes，只包既有FileContent/Usage/Principal/Ref；content/text/file_hash、
usage/owner及material_ref/observation_ref/fragment_ref/command_ref/runner_receipt_ref/raw_result_ref/
provider_ref/call_ref。返回dict/model为副本，没有snapshot/绝对路径/新授权字段；不是公共wire DTO。
后续资料消费必须重新read(ref,original_ctx)，缓存/SQL/Ref不是权限。A把正文置于低信任Context资料
分区，规则不从正文升级，引用/Artifact/Task完成归A；C不修改Context/Agent或调用真实模型。

来源核对：source.read_observation/read_raw核对完整原call/spec/ctx/attempt/provider、独立原command/
签名receipt/journal及原完整snapshot、实际selection；导出复核正文/Usage一致，精确观察Ref和片段Ref。
新增source.observation_ref为原相同hash算法的纯pin helper，无授予数据权；original在record await后
再次binding复查当前数据权限。FileContent.content_hash是原整个文件SHA256；fragment_ref是实际
返回UTF-8字节SHA256；material_ref是FileContent canonical字节SHA256，三者不能混用。
原snapshot始终来自同一次原执行，不向模型/HTTP暴露。原文件变化/删除后只查原journal，不再open。

持久状态：Tool独占tool.file.material.refs/observations/fragments/commands/receipts/providers/calls/
owners/usages，使用既有Ref/Principal/Usage；正文沿原FileContent blob，无私有Object/新DTO/迁移。
原attempt短SQL CAS固定Refs/owner/Usage，篡改/冲突拒绝、不覆盖“修复”。发布和读取在CAS之后再核对
真实来源/当前数据权限；所有Reader/Bridge/Blob/BudgetService IO均在Tool会话事务锁外。
资料导出不调用executor/reserve/dispatch/retry/结算，不声明ToolResult/Task成功。

取消/跨用户/session/project/attempt/root/device/key/版本或数据撤销后的资料读取按当前数据权限；
旧approval和Refs不授予新执行。缺source/access/bridge/signatures/verifier明确503，无原观察不可用，
unknown不新attempt重发/不伪造not_applied或零费用。旧recover_file_accounting只重放已接受原Usage/
已有固定计划，当前BudgetState/Budget授权独立于正文；数据/root/key撤销后可清原费用回执，
不读正文/root/journal、不增观察。pending money仍held；material导出不扩大预算或用户固定模型。

实际验证（C独立loopback55434）：. ./ops/start-dev-db.ps1 -Session C；锁定.venv alembic upgrade head；
所有SQL --require-postgres，独立basetemp/XML、随机主体清理；不复制A私有配置/凭据/其他库，不写共享
 docs/implementation/evidence。回执在ignored tests/.artifacts/C/MS-T2h。

| 范围 | 实际结果/回执 |
| --- | --- |
| M1接口单元 | m1-unit.xml：6通过，0.18秒 |
| 全Tool单元 | m2-unit.xml：369通过，20.84秒（原358+新11），0失败/错误/跳过 |
| 资料SQL首次 | material-first.xml：1失败，fixture修改既有frozen Location而被拒绝；原失败保留 |
| 修复后资料SQL | material-fixed.xml：15通过，503.35秒，改为修改wire副本 |
| 已发布A桥样例 | a-bridge.xml：11通过，59.69秒，真实A RunnerCommands/RunnerPipeClient/C Reader接线 |
| 新process/费用/篡改 | material-recovery.xml：6通过，212.88秒；无executor且文件删除后原资料恢复 |
| 最后额外权限范围 | material-extra.xml：4通过，97.75秒；用户ID/UTF8/device版本/key撤销 |
| 原影响回归 | original-affected.xml：45通过，984.98秒，41原文件+4text/办公兼容 |
| 静态 | Ruff通过；Mypy33源码；76文件format-check；git diff --check通过 |

本轮去重81个不同真实SQL最终全通过（新36+原45），没有最终失败/错误/跳过；verification-index.json
索引原JUnit/最后节点，不叠加复验。原219基线回执保留；其余174原账本/检索/索引未改，不声称本轮
全部219重跑。新单元/SQL模块名不同，无同名收集冲突。原child默认输出兼容，只新增显式material_ref
模式；该真实子进程仅消费测试PUBLIC keys，未复制私钥/生产凭据，0发送/0新打开。

命令：python -m pytest tests/unit/tool -q -p no:cacheprovider；新三个
 test_file_material*_postgres.py -v -p no:cacheprovider --require-postgres（按初轮/额外节点分组）；
原影响python -m pytest tests/integration/tool/test_file_pipeline_postgres.py
 tests/integration/tool/test_file_recovery_postgres.py
 tests/integration/tool/test_text_results_postgres.py::test_actual_text_complete_chain_restart_lookup_outcome_and_result
 tests/integration/tool/test_office_tools_postgres.py::test_office_approved_actual_result_fixed_receipt_fresh_objects
 -v -p no:cacheprovider --require-postgres，详细txt/xml均保留。

测试范围：真实SQL/Blob、实际Windows临时根读取、真实Ed25519、A已发布控制登记/预算原ctx/pipe-client
到C owning Reader；transport/role/root/device/provider元数据/key目录为明确受控组件。
没有真人确认、生产bootstrap/账号root来源或真实LLM/Context成果验收；受控来源未注册产品、flags不改。
最终无未通过组件节点；A真实生产当前用户/session/role/model/provider及设备/root/key/channel来源仍缺。
A负责FileDeviceRoutePort/current recovery authority、Context recipe/低信任正文/Artifact/Verification/
Task结论；D负责本机真人确认和helper来源。生产lines/cursor和项目准入仍unavailable，若需公共资料
DTO须A统一设计生成/发布；本包无需新依赖/迁移/共享契约。只在C允许目录交付，不依赖D开发分支。

A合入、公共冲突和整条链路回归由A处理。本包源码和handoff分开提交，干净后停止，不自动进入下一包。


## MS-T2i：有界多资料消费与原恢复（2026-10-10）

### 实际分支、固定输入与源码

- 工作目录 `E:/UAW/.worktrees/tool`，分支 `dev/tool`。
- 干净检查后fetch tags，远端 `git show origin/integration:docs/coordination/DISPATCH.md` 正式准确SHA为 **8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0**，固定标签 **ms-i2l-start**。ff-only成功，开工HEAD/标签/正式SHA完全相同；未合并浮动integration，未reset/rebase/stash。基线内旧准备状态未作为停工条件。
- `.venv` 按uv.lock冻结同步（`uv sync --frozen --extra agent-engine --link-mode copy`，本worktree UV_CACHE_DIR）；uv.lock SHA256 `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`；schema SHA256 `dd1daee24015771cd5e320027a4f45a2ac31bae61f0f1a84bf6ef240c4f9611c`，shared/锁/组装/flags未修改。
- M1接口源码 **ee6645e928bbe7db292de2f1cf053e7acbb07cd4**，阶段说明提交00e4dea；M2实际消费源码 **47bf1269de3a20f0150e88055662c8962ec5c774**，阶段样例提交d0241db，之后继续M3/M4。
- 恢复/桥接测试阶段 **1cc88a876f1ff115b8ad92e4f8d4f2e0cebd10d6**；最终源码及测试 **44122503ecb60a4036a990eeb20e7340b9618394**。最后提交只修正取消前后测试快照基准，运行实现自M2未变。独立handoff提交随后生成，最终报告实际SHA。
- 原MS-T2g/MS-T2h提交祖先、全部旧回执保留。旧handoff原字节86279、SHA256 `00766a5b3f386e39a239cc22ead6680c663305d41820e906f0ea9e3e6f1e9918`精确前缀保留，仅追加本节。

### 改动文件及公开消费接口

运行新增：`src/uaw/tool/providers/file_material_set.py`。
单元新增：`tests/unit/tool/test_file_material_set.py`。
SQL/自身恢复新增：`tests/integration/tool/file_material_set_fixture.py`、`file_material_set_recovery_child.py`、`test_file_material_set_postgres.py`、`test_file_material_set_bridge_postgres.py`。
C文档：`docs/coordination/requests/C/MS-T2i-stage-interface.md`、`MS-T2i-final-wiring.md`和本handoff。没有修改已接受单文件Reader、Context/Agent/composition/shared/schema/锁/其他worker源码。

```python
FileMaterialSetLimits(max_characters=16384, max_utf8_bytes=65536)
FileMaterialSet(materials: tuple[FileMaterial, ...])
FileMaterialSetAdapter(reader: FileMaterialReaderPort | None, *, limits=None)
async FileMaterialSetAdapter.read(refs: tuple[Ref, ...], ctx: TrustedExecutionContext) -> FileMaterialSet
```

- 严格1–8完整Ref tuple，保留完整wire/hash/version/location/access_scope，输入在首await前冻结。缺hash/非法tuple422，重复409，缺owning Reader503；不从Ref猜ctx/provider或获得权限。
- 冻结有序materials tuple；refs返回原完整Refs副本，characters/utf8_bytes为实际正文合计。默认16384字符/65536 bytes，显式只可缩小正整数（bool拒绝），超量413，不截断/Unicode重写/拼接/部分返回。
- 逐项owning read，所有项完成后按原顺序再次逐项owning read，精确Ref/当前Principal/完整冻结值一致才整体返回。撤销、缺项、版本/来源改变、跨主体/provider整体拒绝；错误与CancelledError传播，无后台Reader任务。
- 保留每项原FileContent/Usage和call/provider/command/实际RunnerReceipt/observation/fragment/raw/material绑定。效果/费用分开，unknown不重发，不reserve/dispatch/retry/新attempt/新file.read/open，不调用export或BudgetService。
- 没有集合SQL命名空间或正文缓存，没有自身句柄/连接，无需close；源Reader生命周期由A拥有。最终序列复核不是跨模块原子授权快照，之后的撤销不能收回已返回字节；后续复用必须再owning read。
- 完整原文件hash、实际片段UTF8 hash、规范FileContent JSON/material hash分别保持。whole时前两者可相等；不从重读补snapshot，不增public DTO或EffectRecord。

### 实际验证命令、回执和最终去重

自身PowerShell `. ./ops/start-dev-db.ps1 -Session C`，独立loopback **55434**；`.venv/Scripts/alembic.exe upgrade head` exit0，current复读 **0003_attempt_identity (head)**。
回执全部在ignored **tests/.artifacts/C/MS-T2i**，没有复制A配置/凭据或修改shared evidence/其他库。

| 实际运行/回执 | 结果和覆盖 |
|---|---|
| m2-unit.xml/txt | 首次直接pytest.exe缺tests imports，收集error保留；改python -m pytest |
| m2-unit-fixed.xml/txt | 新集合27单元通过 |
| tool-unit.xml/txt | C全单元396通过，26.24秒 |
| unit-extra.xml/txt | 最终集合28通过，含新增八来源恰好总量节点；单元去重397，不是一次397 |
| set-first.xml/txt | 两原资料顺序/删除/取消重启1真实SQL通过，93.43秒 |
| set-sql.xml/txt | 主批次13通过/2失败，1196.49秒；原UTF8与取消快照断言失败保留 |
| set-a-bridge.xml/txt | 已发布A真实桥代码3SQL通过，89.57秒；transport/current authority受控 |
| original-affected.xml/txt | 原单文件Reader17、恢复6、办公3，共26通过，992.74秒 |
| set-extra-fixed.xml/txt | 等待中原SQL版本变化1通过；UTF8修复遗漏limits导入1失败，159.36秒 |
| set-utf8-final.xml/txt | 修正UTF8真实合计配置/导入1通过，82.67秒 |
| set-fee-final.xml/txt | 取消后固定费用状态基准1通过，69.79秒 |

最终XML去重 **397单元＋46不同真实SQL通过**：新增28单元、20SQL，原受影响26SQL；最终failure/error/skip均0。多个运行组成，不把重试次数叠加。
真实SQL覆盖：有序两个独立原attempt、重复、第二项等待期间第一项data/root/key/SQL版本撤销、缺项/错版本/跨会话主体/provider、实际UTF8总量、回复丢失/并发、删除文件/取消/执行role失效后恢复、独立进程两资料零新打开、数据拒绝与原费用清理、缺Reader和A原签名桥恢复。
旧MS-T2h369/81及更早219SQL保持旧来源，本轮只实际复跑原26SQL，不将其余旧节点冒充本轮复跑；检索/索引等仍含全Tool单元兼容，未另外重复SQL。

完整命令为 `.venv/Scripts/python.exe -m pytest <上述C模块/精确节点> --require-postgres -q --junitxml=<本回执根/...xml>`；主批次排除已运行order_and_restart，原兼容三个模块按`-k 'not office or approved_actual_result_fixed_receipt'`选26节点；定向只重跑UTF8和取消费用失败节点。新SQL带_postgres，与单元模块不重名；final-collection.txt新增48节点无冲突。
静态：ruff全C源码/单元/SQL通过，**82文件格式**通过，**34 Tool源码mypy**通过；git diff --check及公共文件/允许目录/旧提交祖先检查通过。
verification-index.json从实际XML生成每个节点最终状态、原全部failure/error、XML SHA256、实际基线/源码/公共摘要和来源界限；build_index.py不接受缺回执/未通过节点。observed-startup-diagnostics.json另记初始受限shell worktree定位、format前E501和limits导入F821，标明原tool输出与XML区别，未伪造测试结果。

### 未通过项、修复和生产接线要求

原失败均保留：导入启动器问题改本venv python模块入口；UTF8用例两项合计56000实际低于默认65536，明确收紧测试limit50000后实跑，不修改运行默认；后续unused-import自动移除产生NameError，补import后实跑；费用测试原账本取于cancel前，取消合法改变revision/cancel_requested，调整到cancel后固定财务快照，复跑保持held money0.10/pending。不是通过改执行/费用语义规避失败。

```python
from uaw.tool.providers.file_material_set import FileMaterialSetAdapter, FileMaterialSetLimits
materials = await FileMaterialSetAdapter(
    registered_current_owning_reader,
    limits=FileMaterialSetLimits(max_characters=16384, max_utf8_bytes=65536),
).read(original_material_refs, current_ctx)
for item in materials.materials:
    # A Context external低信任材料；Artifact沿原片段/观察来源引用
    text, fragment, observation = item.text, item.fragment_ref, item.observation_ref
```

A已有 `FileToolBindings.materials` 可处理一个原attempt，跨attempt由A已登记来源Router解析各原ctx并核对当前数据权限，再调用单文件Reader；不能把调用方attempt替换当权限，也不能绕C直接Blob/SQL正文。A保存原Refs顺序/recipe，集合不新造plan或receipt。未发布actual多来源production Router则pending/缺Reader503，受控测试Router不注册产品能力。
已验证固定基线的 `RegisteredFileBridge`、`RunnerCommands`、`RunnerPipeClient`、真实签名与original journal；原call/spec/ctx/provider、command/receipt绑定不改。A/D actual installed/native/root/channel/current-key来源、本人目录授权、Context→固定模型→Artifact/Task接受和汇合全量仍pending。A production桥仍只whole16384/64KiB，lines/cursor/nonempty project明确不可用，不重读原文件补snapshot。
数据撤销仍拒绝材料，允许独立已接受原Usage/费用计划恢复时沿已有recover_file_accounting，不反向获得正文；确认/读成功不等于applied、工具成功或Task完成。公共契约/锁本包无新增缺口；多源生产装配归A，默认flags/用户固定模型未更改。
本包仅MS-T2i，源码/独立handoff分开提交，交付后停止；不自动扩大完整MS-T2或替用户/其他会话操作。
