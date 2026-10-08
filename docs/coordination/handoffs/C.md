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
