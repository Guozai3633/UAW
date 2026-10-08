# Session B交接记录

最新状态：MS-C4局部组件已提交；174项单元/静态通过，35项SQL本轮待A实跑，缓存默认关闭。MS-C3已由A在ms-i2e接受（原15项实际SQL通过），两处Ref/Windows兼容修复已保留。下节保留MS-C1/MS-C2/MS-C3各自当时报告。

## MS-C1 历史交接报告

日期：2026-10-07（Asia/Shanghai）。状态：**组件已提交，待 A 审阅与 MS-I1 接线；P1-02 整轮未验收，MS-C2 未开工。**

## 基线与提交

- Session / 包 / 原轮：B / MS-C1 / P1-02。
- 实际目录：`E:/UAW/.worktrees/context`；实际分支：`dev/context`。
- 首次核对：HEAD 与 `parallel-wave-1^{commit}` 同为 `70f2fcccb88650c616920a5630d2caa45d94ad45`。DISPATCH 的 MS-00 为已发布、dispatch_ready=true。
- 本包实现提交：`307a49b3bbb9e72237b9eed61f787164fe6bdea5`，`feat(context): add authorized source rule and budget components`。
- 本交接文档另作后续提交；A 接收 `dev/context` 分支时同时保留实现和交接记录，不改写历史。实际交接记录提交可用 `git log -1 --format=%H -- docs/coordination/handoffs/B.md` 查询。
- 公共摘要复核与 DISPATCH 一致：schema `c9737069f74331ee5f519eabc1a8bf5c2527389da0e922d46ba892557b522a2c`；uv.lock `e048aafdcfdd0949b7234a8d381fa0dd1d13450ee70f13b5e01c70b79156f9f4`；shared ports/contracts、Intent 提示词摘要也一致。
- 允许路径内完成全部修改；未修改 seed.py、intent.py、shared、composition、公共 schema、锁、迁移、根 README、DISPATCH 或其他 session 文件。
- 公共提案：`docs/coordination/requests/B/MS-C1-wiring.md`，待 A 审阅，无已批准公共变更。

## 改动文件

实现提交的八个文件：

- `src/uaw/context/contracts.py`
- `src/uaw/context/facade.py`
- `src/uaw/context/ports.py`
- `src/uaw/context/sources.py`
- `src/uaw/context/rules.py`
- `src/uaw/context/selection.py`
- `tests/unit/context/test_components.py`
- `docs/coordination/requests/B/MS-C1-wiring.md`

后续仅修改本 `docs/coordination/handoffs/B.md`。缓存/日志为忽略的本 session 文件，未进入提交。

## 公开入口及契约

`ContextComponents(readers=..., cancellation=..., rules=None, models=None, counter=None)` 只由 composition 注入：

| 方法 | 请求 / 输出 | 当前能力 |
| --- | --- | --- |
| resolve_sources(request, ctx) | InternalContextSourcesRequest / ComponentContextSourcesResult | 只对注入且实际获准 Reader 解析，固定版本/Location/hash，生成实际来源 manifest |
| resolve_rules(request, ctx) | InternalContextRulesRequest / ComponentContextRulesResult | 可信注册规则、单目标作用域、架构第14节优先级、明确关键冲突及显式用户纠正 |
| select(request, ctx) | InternalContextSelectionRequest(select/allocate) / ComponentContextSelectionResult | 固定模型真实窗口核对、输入/输出/工具及序列化余量分配 |
| build(request, ctx) | ContextRequest / RuntimeContextruntimeBuildResult | **未接线，明确 capability_unavailable，不返回假快照** |

请求和返回沿用共同基线权威 JSON Schema。Python DTO 通过严格 JSON 解码接收数组；未知字段、错误类型/枚举不放行。没有私加公共字段。

内部供 A 编排的类型和方法：

- Reader.check/read：实际读取、当前授权/撤销/删除、固定版本及精确 UTF-8 片段；来源所有权留在原 Runtime。
- Cancellation.is_cancelled：Run 所有的取消状态；未注入不可用。
- RuleProvider.discover → RulePlan：已注册规则、目标路径绑定、根到目标/纠正顺序、可信冲突评估。没有评估能力时 assessment_complete=False，不声称自然语言兼容。
- RuleResolver.assemble → RuleAssembly：InstructionSet、所有被读取规则/目标依赖及被覆盖→生效来源关系；manifest() 可用于 A 后续保存。尚无持久 instruction_set_ref。
- ModelWindowProvider.resolve → ModelWindow：必须解析 ctx.model_policy_ref 的固定实际窗口、最大输出及序列化保留；不能默认另一个模型或伪造窗口。
- Selector.allocate(SelectionRequest, ctx, PreservationSpec=None) → Allocation：内部保护 required_refs/exact_strings/requirement_ids/pending_action_refs；缺绑定明确 missing/不可用。估算方法在 Allocation.estimation 明示，未伪装实际 tokenizer/usage。
- 所有自然语言内容保留原文，资料不升级权限/模型政策。推断冲突和 requirement 绑定均由实际可信适配器提供；组件不使用关键词冒充模型理解。

## 三组可执行接线例子

独立运行：

```powershell
Set-Location E:/UAW/.worktrees/context
./.venv/Scripts/python.exe -m pytest tests/unit/context -q -o cache_dir=.cache/pytest/B
```

- 成功：`test_source_success_exact_text_and_repeat` 固定原文含空格、CRLF、数字与来源；`test_selection_protects_original_output_and_pending_requirements` 保护原文/状态、裁掉大材料且留输出/工具/序列化空间。
- 拒绝/失败：`test_missing_denied_revocation_are_explicit` 验证读前拒绝及读中撤权；`test_external_injection_stays_data_and_cannot_become_rule` 验证资料注入不升权；缺 Workspace/Board/Memory/Web Reader 明确 capability_unavailable。
- 重复/版本冲突：相同 pin/参数不同 attempt 结果一致；`test_source_pin_changes_are_stale` 的版本、hash、位置和身份变化明确 stale/source_changed；`test_rule_audit_retains_suppressed_versions_and_conflict_evidence` 保留覆盖/关键冲突证据。
- 实际 JSON 输入输出回执：`tests/.artifacts/B/MS-C1/examples.json`（成功、denied、重复、stale、预算分配）。这是受控 fixture 的真实执行结果，**不是实际 LLM/Runner 回执**。

## 状态、版本、幂等和取消

- 首包纯读取/确定性装配，没有数据库写入、外部副作用、事件、执行权限或自建持久账本。
- Ref 只来自已读版本；Reader 必须检查真实当前授权，传入 access_scope 或登记 Reader 不等于获权。读前、读后及返回前复核；来源 pin 不一致明确 stale。
- RuleAssembly 版本摘要包含实际规则/被覆盖版本、作用域、能力政策及可信评估元数据；关键冲突带已读取来源 Failure.evidence_refs。显式后续 user_current 纠正需要可信 supersedes 和顺序，其他关键矛盾保持冲突。
- 读取重复请求可安全重算；本包不产生持久请求 ID 状态，未宣称快照 exactly-once。持久快照的 epoch/CAS/request_id 幂等留待 MS-I1/MS-C2。
- 公开组件入口限制 ctx.deadline；开始、port await 前后及输出前检查 Run 取消；Python task cancel 返回 cancelled。实际适配器仍需协作停止 I/O，组件无法终止外部阻塞调用。内部 typed 编排方法由 A 放入同样的 deadline/取消边界。
- 未动固定用户模型、原文、授权和 flags；D01/D03/D06 均保持待确认/配置。

## 实际验证与回执

环境：本 worktree `.venv`，Python 3.14.6，editable 来源为本 worktree；没有启动 PostgreSQL、后台服务、真实模型或 Runner。

以下 `<B files>` 指上述六个 src/uaw/context 新文件，避免扫描/格式化 A 的 seed.py/intent.py。

| 命令 | 实际结果 | 本地回执 |
| --- | --- | --- |
| ./.venv/Scripts/python.exe -m ruff check <B files> tests/unit/context | exit 0 / All checks passed | tests/.artifacts/B/MS-C1/ruff.txt |
| ./.venv/Scripts/python.exe -m ruff format --check <B files> tests/unit/context | exit 0 / 7 files already formatted | tests/.artifacts/B/MS-C1/format.txt |
| ./.venv/Scripts/python.exe -m mypy <B files> --cache-dir .cache/mypy/B | exit 0 / 6 source files 无问题 | tests/.artifacts/B/MS-C1/mypy.txt |
| ./.venv/Scripts/python.exe -m pytest tests/unit/context -q -o cache_dir=.cache/pytest/B --junitxml=tests/.artifacts/B/MS-C1/junit.xml | **39 passed，0 failed，0 skipped，0 warning** | tests/.artifacts/B/MS-C1/pytest.txt、junit.xml |
| git diff --cached --check（实现提交前） | exit 0 | 提交工具回执 |

完整命令、环境/exit_code 位于 `tests/.artifacts/B/MS-C1/validation.json`。回执目录为本 session 忽略文件，A 可从这个 worktree 读取；在集成 SHA 必须重跑，不能以 worker 回执替代。

初次检查发现 fixture 使用不存在 RefKind、严格 DTO 数组解析和静态格式问题；已更正并重跑，最终检查无失败。最终只运行本包检查，未运行全量/共享 SQL/整条链路回归。

## 未实现、未验证与 A 接线要求

- 无真实 History/Workspace/Board/Memory/Web Reader；测试只有受控内存适配器，不证明本地 Runner 文件访问或真实材料能力。
- 无实际规则注册/目录发现/自然语言冲突评估适配器、Run 取消适配器、固定模型窗口适配器；未注入时明确不可用。
- 多目标目录的规则分区与汇合未实现，返回 context.rules.multi_target_partition 不可用。A 必须逐目标构建集合并在 Tool 写前复核，不能把所有目录规则当全局规则。
- 无快照保存、Ref 查询、epoch 仓储/持久 CAS、引用撤销传播或 Composer capability 摘要；build 不成功。MS-C2 只在 MS-I1 发布新共同基线后开始。
- UTF-8 序列化字节估算保守且明确标识；实际提供方 tokenizer、最后完整 prompt/schema 计数与真实模型语义质量未验。输出 reserve 必须大于零并小于实际最大输出，不能因超窗改模型。
- A 接线必须将 ContextRequest.preserve 传入 allocate；Reader 保护原文/硬约束/未决状态并提供真实 requirement 绑定。只做模型窗口数学检查不等于已完成语义选择/压缩。
- 接线提案详见 `requests/B/MS-C1-wiring.md`；不需新增 Python 包或迁移，公共 DTO 未变。A 保留 Intent 专用实现，在 MS-I1 决定迁移、组装根、持久边界及能力启用。
- A 审阅/合入/处理公共冲突并执行原 P1 链路回归，发布实际新集成 SHA；组件接受不等于 P1-02 accepted。未向其他聊天发消息，也未创建其他 session。

## 集成与回退

B 实现提交 `307a49b3bbb9e72237b9eed61f787164fe6bdea5` 可独立审阅；A 按 PARALLEL_WORKFLOW 合入 dev/context，公共接线另作可区分提交。本包没有迁移或已发生的外部效果，可通过 A 的正常 revert 回退实现。禁止直接把 worker 分支当其他 session 的未发布依赖。


## MS-C2：实际交接

日期：2026-10-07（Asia/Shanghai）。状态：**实现已提交，待 A 审阅/接线和真实 SQL 执行；P1-02 整轮未验收。**

### 基线、分支与提交

- 实际 worktree / 分支：`E:/UAW/.worktrees/context` / `dev/context`。
- 从干净的 `0da308fd42a59c8f4bf47a5c19c2932f345d0a85` 快进 `git merge --ff-only ms-i1`；HEAD 与标签均为 `f33d16245619b6d446816a36b65bd5c1fc607593`，保留首包历史。
- 已读新 DISPATCH、Session B 和 A 的 `requests/A/MS-I1-adapters.md`。A 接受 MS-C1 并派发 MS-C2；只消费该已发布快照，未消费 A 后续 MS-I2 未交接源码。
- 本包实现提交：**`c85bf52b283866cfdcad689356faee239152ba1d`**，`feat(context): persist immutable snapshots and resolve read sources`。
- 本交接另作后续提交；使用 `git log -1 --format=%H -- docs/coordination/handoffs/B.md` 取得文档实际 SHA。A 审阅本包时对比 `ms-i1..dev/context`，不要将已快进的 C/D 基线误算为 B 新改动。
- schema/shared ports/contracts/uv.lock 摘要仍与 DISPATCH 一致。未新增迁移/依赖/事件/flags，D01/D03/D06 未自行设定。
- 只修改允许路径；A 的 seed.py、intent.py、Run/Model adapters、composition、共享文件与 DISPATCH 相对 ms-i1 无差异。

### 文件清单

实现提交的九个文件：

- src/uaw/context/contracts.py
- src/uaw/context/ports.py
- src/uaw/context/facade.py
- src/uaw/context/composer.py
- src/uaw/context/repository.py
- src/uaw/context/references.py
- tests/unit/context/test_snapshots.py
- tests/integration/context/test_snapshots_postgres.py
- docs/coordination/requests/B/MS-C2-storage-wiring.md

后续只提交本 handoff。回执/缓存在本 session 忽略目录，未提交。

### 公开接口与实际范围

- `ContextComponents` 增加可选 repository/authority 注入；原 ms-i1 组装默认未传，因此理解专用行为保持，通用 bindings.context 不被启用。
- `build(ContextRequest, ctx) -> RuntimeContextruntimeBuildResult`：依赖齐全时保存真实读取来源的 ContextSnapshot；缺仓储、CompositionAuthority、能力 Reader、目的规则或模型元数据，明确失败/不可用。
- `resolve_reference(RefRequest, ctx) -> RuntimeContextruntimeResolveReferenceResult`：只查本 Run/作用域中由 Composer 已登记的实际来源；没有任意 URL/Ref 造证据。
- `read_snapshot(Ref, ctx)`：内部查询辅助，返回现有 BuildResult 结构；重新检查源/规则/权限/epoch/模型窗口与保护集合。没有自增 HTTP/工具操作。
- `components.references.handle(InternalContextReferencesRequest, ctx)`：实现 resolve/read；Unicode text_span 对整个已读文本取片段，已登记片段不能扩大到 whole。分页与任意 register 明确不可用。
- `ContextRepository(records, TransactionalStore(database))`：消费 ms-i1 现有通用 SQL 存储/事务，未导入其他 Runtime 私有仓储或修改邻域状态。
- 新增 `ContextRequest` Python DTO 完全对应现有 schema。CompositionBinding/PreparedSnapshot/CompositionAuthority 是注入用内部记录与 port，不增加公共 JSON 字段。

CompositionAuthority 必须提供真实 purpose 对应规则、当前 epoch、实际能力源 Ref、原文/重要要求/未决动作保护及额外来源依赖，verify 复核当前权威状态。B 没有默认用理解指令服务 agent_step，也没默认构造空 tools；当前生产这类适配器尚缺，接线提案待 A 审阅。

### 存储、来源与边界

- 命名空间：`context.generic.snapshots`、`instructions`、`bindings`、`scopes`、`requests`、`references`，完整名称均带 context.generic 前缀；与 A 理解专用 context.* 分开。
- 一个事务写快照、InstructionSet、ModelContextBinding、Scope、原始 ContextRequest 及实际读取的 ReferenceRecord；仅成功提交后返回 Context Ref。提交前后重读固定来源并复核授权/取消。
- 自有对象只创建 revision=1。新 operation_id 创建新 ID；新 epoch 必须来自真实 authority，expected_epoch 不符返回 conflict。没有更新旧快照的方法。
- ctx.operation_id 是逻辑 request_id；attempt_id 只代表重试。持久幂等参数含原请求、Run、Scope 与固定模型/能力政策；同键同参重放，同键异参 idempotency_conflict。聚合锁和 RequestRow 来自现有 TransactionalStore，非内存生产账本。
- 快照 Manifest 记录实际选中来源及读取依赖；源 Ref/hash/Location 对应实际读取。manifest.content_hash 是快照非 manifest 字段摘要，Context Ref 的 hash 覆盖完整快照。InstructionSet Ref 也核对固定内容 hash。
- ReferenceRecord 保存首次读取时间、实际来源链和服务端 scope；与下一次快照复用时不覆写。同源版本不同内容明确拒绝。无推测网页 URL、本机绝对路径或虚构 Citation；空 citations 表示未登记论断关系。
- 引用/快照读取再次调用当前 Reader，删除、撤权、取消、版本/hash/位置变化均可使旧 Ref 不可读。Ref/access_scope/快照缓存不授予永久读权。
- ContextRequest.preserve 与 authority 的关键保护合并；request 不提供原文时仍保留 authority 的已受理原文。requirement_ids 没有实际来源绑定时不可用，不能声称语义匹配完成。
- 最后序列化估算覆盖完整 snapshot/manifest/规则/能力及 escaped text，保留输出、工具和额外 envelope 余量；超窗失败，不删关键项或更换模型。仍是保守 UTF-8 估算，实际 Model 发送前沿用 ms-i1 原生请求计数。
- SQL 事务保证 Context 自有对象原子性；不能把其他领域/外部源撤销做成跨系统原子承诺。真实 authority/Reader 必须供当前版本复核；打开时必重查。发生提交与取消竞态时已保存记录不被宣称自动撤销。
- 当前 ms-i1 Run Reader 只支持已受理活动 Run；本包沿用该边界，不扩大到预览或已完成 Run，不修改 Run/Model 状态和执行权限。

### 验证命令与实际回执

环境：本 worktree 的 .venv，Python 3.14.6。未读取/复制凭据，未启动数据库、迁移或第二套后端，没有真实 LLM/Runner 执行。

`<B files>` 为 context 下九个 B 文件：facade/contracts/ports/sources/rules/selection/composer/repository/references.py；不格式化 A 的 seed.py/intent.py。

| 命令 | 实际结果 | 回执 |
| --- | --- | --- |
| ./.venv/Scripts/python.exe -m ruff check <B files> tests/unit/context tests/integration/context | exit 0 / All checks passed | tests/.artifacts/B/MS-C2/ruff.txt |
| ./.venv/Scripts/python.exe -m ruff format --check <B files> tests/unit/context tests/integration/context | exit 0 / 12 files already formatted | tests/.artifacts/B/MS-C2/format.txt |
| ./.venv/Scripts/python.exe -m mypy <B files> --cache-dir .cache/mypy/B | exit 0 / 9 source files | tests/.artifacts/B/MS-C2/mypy.txt |
| ./.venv/Scripts/python.exe -m pytest tests/unit/context -q -o cache_dir=.cache/pytest/B --junitxml=tests/.artifacts/B/MS-C2/unit.xml | **64 passed，0 failed/skipped/warning**；其中原 MS-C1 39 个及 MS-C2 25 个 | tests/.artifacts/B/MS-C2/unit.txt、unit.xml |
| ./.venv/Scripts/python.exe -m pytest tests/integration/context --collect-only -q -o cache_dir=.cache/pytest/B | **9 tests collected，未执行 SQL** | tests/.artifacts/B/MS-C2/sql-collection.txt |
| git diff --cached --check（实现提交前） | exit 0 | 提交工具回执 |

完整命令/环境/exit_code：`tests/.artifacts/B/MS-C2/validation.json`。JSON 成功、重复、参数冲突、引用读取、denied、epoch stale 例子：`tests/.artifacts/B/MS-C2/examples.json`。均为明确的受控组件运行；内存事务不是真实 SQL 回执。

必要用例包括：原文 CRLF/数字不改写、固定 manifest、真实来源登记、同操作并发/重放、参数冲突、新 epoch 新快照、旧 snapshot stale、源删除/变更、当前撤权、作用域/Run 隔离、超窗与缺 requirement 绑定、未知 Workspace、片段不能扩大、取消（含部分写入后的回滚）。

### A 必须执行的真实存储验证

B 当前没有获准 UAW_TEST_DATABASE_URL，未启动或借用共享数据库。已完成真正 PostgreSQL 测试代码，交 A 执行，**收集成功不算存储验收**：

```powershell
./.venv/Scripts/python.exe -m pytest tests/integration/context -q --require-postgres
```

九个用例使用 root database/principal 与已发布 domain/understanding fixture，随机主体清理、无 truncate。实际 Run 原文/权限/取消/固定模型目录及事务使用 ms-i1 已发布适配器；epoch 和空能力集合是标注清楚的测试适配器。没有模型发送，不证明产品 Tool/Runner 或真实 LLM。

SQL 检查覆盖实际原文打开、原子写入、durable replay、参数冲突、并发一次保存、新旧 epoch 不覆写、删除传播、当前政策撤销、取消、Workspace 未接入无提交、登记冲突时整个事务回滚。A 在集成 SHA 上执行这组后，再执行现有 MS-I1 理解接线和全链路回归；若发现业务问题退回 B 修复。

### 接线提案、未通过项与回退

- 提案：`docs/coordination/requests/B/MS-C2-storage-wiring.md`，待 A 决定，无已批准公共变更。
- A 注入可信 CompositionAuthority 和真实 ModelToolSet Reader、明确 purpose 规则/保护/epoch 状态所有者，再决定 Model 输入解析、RuntimeBindings.context 与产品操作登记。B 未改 composition 或 A 的理解专用 builder/new adapters。
- **真实 PostgreSQL 9 项未运行，故实际存储验收尚未通过**；现有理解组合回归和整条链路也由 A 执行。没有将缺连接当默认 skip 的成功记录。
- Workspace/Board/Memory、真实 Runner、任意引用登记、分页/Citation、预览/终态 Run、自然语言多规则评估及通用生产能力摘要仍缺实际依赖，明确不可用。
- 本包不需要 schema 生成、锁更新或迁移；部署权威 D01、Runner D03、真实模型 D06 保持待定。A 接线/权限所有者变化需要独立公共提案和实际新基线。
- A 按 ms-i1..dev/context 审阅本包，实现与接线提交区分。可正常 revert B 实现提交或独立 A 接线提交；已有不可变数据库记录不会被源码 revert 删除，后续读取仍受当前授权约束。
- 未自动创建/联系其他 session。接受状态由 A 在 DISPATCH 维护；MS-C2 组件交付不自动接受 P1-02。


## MS-C3：通用模型输入实际交接

日期：2026-10-08（Asia/Shanghai）。状态：**组件已提交，待 A 审阅、真实 SQL 执行及生产路由/authority 接线；完整 P1-02 / Agent 运行未验收。**

### 基线、环境和实际提交

- 实际目录/分支：`E:/UAW/.worktrees/context` / `dev/context`。
- 从干净的 `c6ae25dc7526f811f2b614508e93a017e09ecdd1` 执行 `git fetch origin --tags`、`git merge --ff-only ms-i2c`，均成功，保留历史。同步后 HEAD 和标签解析 commit 均为 **`1411f6aa477b0d000bee871c0f324fbfd67b4ff5`**。
- 已阅读新 DISPATCH、Session B 和 `requests/A/MS-I2c-ports.md`；A 已接受 MS-C2，本次仅消费 ms-i2c，不消费 C/D 未交接分支。
- 按锁执行 `uv sync --frozen --extra agent-engine --link-mode copy`，exit 0；UV_CACHE_DIR 指向本 worktree `.cache/uv`。新增锁内 cryptography/cffi/pycparser 与本项目重装，未改变 pyproject/uv.lock。
- 本包实现提交：**`396b5481694e4279aa3680edb1c25b84a26b0f02`**，`feat(context): resolve generic snapshots into public model prompts`。
- 本 handoff 另作后续提交；准确文档 SHA 用 `git log -1 --format=%H -- docs/coordination/handoffs/B.md` 查询。A 对比 `ms-i2c..dev/context`，不要把同步后的基线变化算为 B 本轮修改。
- 固定公共摘要符合 DISPATCH：schema `b5d7cdf9df23002e6e3d3965741cbcd82b7efa34ff438b09b236e3b0b886d583`；shared ports `cce4db2349b92a6a2fca815917725cb7bb51fcb5ab9db86c2f456d3df2b679cd`；shared contracts `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b`；lock `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`；理解提示词仍为 `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400`。
- A 保留的 seed.py、intent.py、Model、组装根、shared、公共 schema、锁及迁移相对 ms-i2c 无修改。未改 Runtime 绑定或 flags；D01/D03/D06 不自行定案。

### 本包文件

实现提交的五个文件：

- `src/uaw/context/model_input.py`
- `tests/unit/context/test_model_input.py`
- `tests/integration/context/model_input_fixture.py`
- `tests/integration/context/test_model_input_postgres.py`
- `docs/coordination/requests/B/MS-C3-model-input-wiring.md`

后续仅提交本 handoff。回执在本 session 忽略目录，未进入提交。

### 公开接口及样例

`GenericModelInputs(composer: Composer | None)` 结构兼容 A 的公开 ModelInputPort：

```python
from uaw.context.model_input import GenericModelInputs

inputs = GenericModelInputs(context_components.composer)
prompt = await inputs.resolve(snapshot_ref, trusted_context)
# prompt: uaw.model.contracts.ModelPrompt
# messages: tuple[dict, ...]; tools: tuple[ToolSpec dict, ...]; estimated_tokens: int
```

只读导入公开 ModelPrompt，不导入 ProviderRequest/ProviderResponse，也不调用提供方或 Model 私有 adapter。没有新公共 DTO/字段/HTTP/工具入口。

- 成功：真实固定 InstructionSet 的平台指令为 system 消息；原文 `"  原文 123.40\r\n"` 为完全相同的 user 消息；获准工具 ToolSpec 与实际读取集合一致。
- 外部资料：user 消息内的 JSON 为 `{"context_kind":"data","kind":"material","trust":"external","source_refs":[实际Ref],"text":原文}`；资料中的 role/system/工具字符串不会变成结构性消息/工具定义。
- 项目/技能/角色/偏好：user 消息内 registered_instruction 对象记录 level、scope、source_ref、text；不升为 system。当前用户要求保留原文，同源原文/用户规则只发送一次。
- 失败：缺 Composer/authority/能力 Reader → capability_unavailable；跨 Run/Scope → permission_denied；来源删除 → 明确 missing 对应 DomainError；固定版本/hash、规则/工具/epoch 变化 → stale 对应 DomainError；窗口不足 → context_insufficient；Run/Python 取消 → cancelled；超期 → deadline_exceeded。
- 重复：同一已保存 Ref 即使重新建 repository/解析器或更换模型调用 operation/attempt，在权限及版本有效时得到相同 prompt，不写数据库或新增幂等记录。快照仍严格绑定原 Run/Scope。
- 原始 JSON 成功、重复、跨 Run 拒绝、撤权、stale、预算不足回执：`tests/.artifacts/B/MS-C3/examples.json`，明确受控组件执行，不是真实 LLM/Runner/SQL 回执。

**tools 格式：** ms-i2c ModelGateway 直接消费 ToolSpec，provider adapter 才转换 native function schema。B 返回完整 ToolSpec，包含 id/version/input_schema/output_schema/权限/提供方等固定元数据，不自行构造 provider 函数名或改变结果格式。只有实际读取的集合为空才返回空 tuple，缺来源不能假造空工具。

### 读取、身份、版本与预算

- 使用已有 ContextRepository/Composer/SourceResolver，加载 `context.generic.*` revision=1 快照、InstructionSet、请求与 Run/Scope 绑定，检查快照 hash、manifest 与实际输入块一致；无理解模板 fallback。
- Composer 在读取前后重查当前 epoch、规则、保护、额外依赖、当前政策及固定窗口；解析器重读每个已选固定内容/hash/位置/分类、实际能力集合和有效规则文本。资料信任字段本身不成为指令。
- 工具集合检查 ModelToolSet schema、所属 Run、重复名称及 required_capabilities 对当前 ctx.scope 的子集；实际 flags、角色/资源、提供方 eligibility 来自可信 Reader/CompositionAuthority.verify，仍须 A 注入。
- 最后再次执行 Composer/authority 检查并比较 binding/模型窗口，取消/截止时间覆盖全过程。原文不 trim/归一化/改换行，不把无真实角色/call ID 的历史或工具文本冒充 assistant/tool 消息。
- 估算覆盖 JSON 消息、全部 ToolSpec 输入/输出 schema 和元数据、每项序列化余量，取不低于快照估算；保留输出、工具和模型 envelope 空间。包含针对旧/低估计快照的完整重计数反例。
- 估算不是供应商 tokenizer/计费；A 的 Gateway 必须继续计算包含输出 schema/参数的完整 native 请求并核对当前模型配置。窗口不足不删条件、不换模型。
- 返回是读取结果，不是工具或执行授权；无仓储写入、事件、幂等状态、权限变更。SQL 与外部撤权/发送不原子，最终发送/执行闸门继续复核。未做真实 LLM 语义遵循/注入防护验收。

### 实际验证

本 worktree .venv / Python 3.14.6；无需新增锁外依赖。B 没有 UAW_TEST_DATABASE_URL，未读取或复制凭据/私有 .data，未启动第二套数据库/迁移/服务。

`<B files>` 是十个 B 文件 facade/contracts/ports/sources/rules/selection/composer/repository/references/model_input.py；不检查或格式化 A 保留的 seed.py/intent.py。

| 命令 | 实际结果 | 回执 |
| --- | --- | --- |
| uv sync --frozen --extra agent-engine --link-mode copy（本目录缓存） | exit 0，锁未变，editable 指向本 worktree | 开工工具回执；validation.json 摘要 |
| ./.venv/Scripts/python.exe -m ruff check <B files> tests/unit/context tests/integration/context | exit 0 / All checks passed | tests/.artifacts/B/MS-C3/ruff.txt |
| ./.venv/Scripts/python.exe -m ruff format --check <B files> tests/unit/context tests/integration/context | exit 0 / 16 files already formatted | tests/.artifacts/B/MS-C3/format.txt |
| ./.venv/Scripts/python.exe -m mypy <B files> --cache-dir .cache/mypy/B | exit 0 / 10 source files | tests/.artifacts/B/MS-C3/mypy.txt |
| ./.venv/Scripts/python.exe -m pytest tests/unit/context -q -o cache_dir=.cache/pytest/B --junitxml=tests/.artifacts/B/MS-C3/unit.xml | **107 passed，0 failed/skipped/warning**（原 64 + MS-C3 43） | tests/.artifacts/B/MS-C3/unit.txt、unit.xml |
| ./.venv/Scripts/python.exe -m pytest tests/integration/context/test_model_input_postgres.py --collect-only -q -o cache_dir=.cache/pytest/B | **15 collected；未执行 SQL** | tests/.artifacts/B/MS-C3/sql-collection.txt |
| git diff --cached --check（实现提交前） | exit 0 | 提交工具回执 |

完整环境/命令/exit_code/公共摘要见 `tests/.artifacts/B/MS-C3/validation.json`。组件 fixture 是标注的内存事务、Reader 和 authority；最终检查无失败。早期大描述 fixture 超出 NonEmptyText 16384 上限，已按权威 schema 更正并重新验证；负例失败是预期断言，不计为未通过项。

### 真正 PostgreSQL 用例交 A 执行

`tests/integration/context/test_model_input_postgres.py` 新增 15 项，包括新数据库连接与新 Python 子进程重建。快照、原文、规则/工具/材料/epoch 请求实际存到 PostgreSQL；原文/当前权限/取消/固定模型解析使用 ms-i2c 已发布适配器。通用规则与工具目录及 authority 是测试注册，未声称产品服务已可用；窗口缩小反例是明确受控 Window wrapper。

子进程重新创建数据库、仓储、configuration 与 resolver，使用 Windows `control_plane_loop`；数据库 URL 仅由测试通过 stdin 传递，不进命令参数、文件或回执。无模型/工具/Runner 请求。root database/principal fixture 随机主体清理，不 truncate。

A 在已安排 SQL 环境/集成 SHA 运行：

```powershell
./.venv/Scripts/python.exe -m pytest tests/integration/context/test_model_input_postgres.py -q --require-postgres
```

**15 项尚未实际执行，进程重启/实际 SQL 的运行结果未验证；收集不算通过。** A 实跑后再回归已有 MS-C2、理解输入、Model 原生估算和全链路。B 本次未运行这些 A 负责的全量检查。

### 未通过项、接线要求及回退

- SQL 环境缺失：新 15 项及跨进程恢复仅完成代码/收集，待 A 实跑。真实 LLM/Agent、语义质量、工具/Runner 执行均未验收。
- 通用生产 authority、能力 Reader、目的规则/输入路由缺失：注入不足明确不可用，不能把 SQL fixture 的工具定义或空集合挂成生产服务。
- A 负责 `GenericModelInputs(context_components.composer)` 接线及快照命名空间/purpose 路由。缺通用依赖时保持 unavailable；不修改理解 builder，agent_step 不走 understanding 模板。
- A 的 Model/Tool 发送边界继续核对实际当前权限/flags、fixed model、native body、预算/取消及 lease/fence。本组件只检查已注入的真实 port，不授予权限、不自建 Runtime 入口。
- 真实 assistant/tool 历史角色与工具调用 ID、压缩输入的已验证内容、Workspace/Board/Memory Reader 尚缺，分别保持数据身份或明确不可用；不自行补假字段。
- 最小接线提案：`requests/B/MS-C3-model-input-wiring.md`；无公共接口改动审批被假定为已通过。A 决定与新基线写 DISPATCH。
- 实现与 A 的路由接线应独立提交，正常 revert B 新 adapter/测试不删已有 Context 记录；不修改 D01/D03/D06，不把 MS-C3 组件交付标为完整 P1-02/Agent accepted。
- 未创建、修改或联系其他 session；A 审阅/合入/处理公共冲突并执行整条链路回归。

## MS-C4：上下文纯计算有界缓存交接

日期：2026-10-08（Asia/Shanghai）。状态：**局部组件已提交；B 单元/静态检查通过，35项SQL本轮待A实跑；默认关闭，未标P1-02/P4-04整轮accepted。**

### 实际基线与提交

- 包 / 原轮：B / MS-C4 / P1-02（参考P4-04缓存边界）。
- 实际目录 / 分支：`E:/UAW/.worktrees/context` / `dev/context`。
- 开始前工作区干净，原HEAD `00332fc07de1e72ba97199ac8e25352219ac2606`。执行 `git fetch origin --tags`、`git merge --ff-only ms-i2e`，均exit 0；没有reset/rebase或单独覆盖公共文件。
- 快进后HEAD和 `ms-i2e^{commit}` 一致：**`ba2f3b0d9417e6d695eaa74c2f766217c98b01f1`**。按此固定版本开发，不混入其他worker未交接代码。
- 按锁同步：`UV_CACHE_DIR=.cache/uv` 下执行 `uv sync --frozen --extra agent-engine --link-mode copy`，exit 0，Checked 91 packages。Python **3.14.6**，prefix为本worktree `.venv`；锁未改。
- 本包实现提交：**`acc68fc670ed5edb5186908219408c1bc4c1dfda`**，`feat(context): add optional bounded pure computation cache`。
- 本交接另作单独提交；其实际SHA由 `git log -1 --format=%H -- docs/coordination/handoffs/B.md` 查询，并在最终回执报告。不改写已交接历史，不push。
- A 的MS-C3接受与原15项实际SQL通过见固定基线DISPATCH/MS-I2e；A在 `285258a` 的Ref/Windows测试修复已随快进保留。`tests/integration/context/model_input_fixture.py`、`test_model_input_postgres.py` 与ms-i2e逐字节相同，B本包未修改它们。下面旧MS-C3章节的“待SQL”是当时历史回执。

### 修改清单

源码提交仅8个B允许文件；交接提交只更新本文件：

| 文件 | 本包变化 |
| --- | --- |
| `src/uaw/context/cache.py` | 新增进程内主体分区、有界LRU、不可变bytes、完整摘要键和只对缓存故障的best effort适配 |
| `src/uaw/context/model_input.py` | 可选cache构造注入；原身份/分类验证保留，纯格式化/序列化/完整估算单独复用；最终复查仍执行 |
| `src/uaw/context/selection.py` | 保持count签名/原估算公式；在已验证Reading之后可选缓存整数估算；counter实例/版本纳入键 |
| `src/uaw/context/composer.py` | 向selector内部键材料传实际snapshot/request/epoch/binding/instructions；不缓存授权结论 |
| `src/uaw/context/facade.py` | 可选内部cache参数传selector，既有调用默认关闭 |
| `tests/unit/context/test_cache.py` | 新增67项受控组件检查（含参数化），原107项不改 |
| `tests/integration/context/test_cache_postgres.py` | 新增11项SQL用例，模块名与unit不同；本轮尚未实跑 |
| `docs/coordination/requests/B/MS-C4-cache-wiring.md` | A最小可选接线/关闭示例、消费方影响和待SQL清单；无公共契约缺口 |

没有修改seed.py、intent.py、Model、组装根、API、shared/schema/依赖锁、公共测试fixture、迁移、README/DISPATCH、其他session或worktree。公共五项摘要与固定基线逐字节复核：schema `45161b36f2e81622e73f86c23b048cda8d55686e7045248f0394ab51d13dbe6b`；shared ports `453cd9cd21b92a77c6e370fc6f0463072a3903a2c6b5beee56dec4f93b0c27a5`；shared contracts `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b`；uv.lock `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`；理解提示词 `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400`。

### 接口与缓存边界

公开调用保持：

```python
await GenericModelInputs(composer).resolve(snapshot_ref, ctx)  # -> ModelPrompt
counter.count(reading)  # -> int；TokenCounter protocol没有新增要求
```

可选内部构造：`ContextComponents(..., cache=cache)` / `Selector(..., cache=cache)`；`GenericModelInputs(composer, cache=cache)`。`PureComputationCache(max_entries=..., max_bytes=...)`，`get/put/clear`及只读frozen `stats(entries,size_bytes,hits,misses,evictions)`均是B内部接口，不新增wire对象。两个入口可以各自注入或共享同一有界实例；输入格式化不会自动继承selector缓存。

- 每次依旧读取实际Repository/InstructionSet、current authority、所有实际来源/分类/ModelToolSet和固定窗口；完整scope、Run、epoch、依赖版本、flags/权限、preserve、取消与期限由原port继续验证。所有既有await后和最终composer/authority/window/guard复查保留。
- 缓存只存纯消息格式化bytes、序列化估算及纯counter整数bytes，不存旧Reading、CompositionBinding、访问许可或旧ModelPrompt授权结论。模型输出没有缓存；工具集合仍每次真实解析验证，不假造空tools。
- generic键包括实际snapshot Ref/完整snapshot/request/instructions、binding全字段的摘要材料、全部Reading原文/Ref/location/access_scope/kind/trust/required/requirement_ids、实际capability/完整ToolSpec（含input/output schema）、fixed window/全部预留、formatter类型和算法版本。selector键包括selection/preserve/window/全部Reading及composer传来的snapshot/epoch/规则/工具边界。
- 主体kind/id分区，完整Principal（含auth session）、完整Scope、Run、fixed model/capability/budget refs及agent/node进入键。operation/trace/attempt/deadline不属于纯输入身份；新的当前授权与取消/期限仍检查。相同body但分类/保护元数据改变不命中旧值。
- 来源或snapshot缺hash、键无法完整序列化时绕过；同ID/version不同body先由原读取校验拒绝。cache键只留两个摘要，不保存原始key数据。
- 进程内LRU同时限制条目数和字节；字节accounting为payload＋两个摘要UTF-8字节，额外Python容器开销由条目上限限制，不声称RSS精确上限。超大条目绕过，容量任一为0关闭，默认构造关闭。条目淘汰/clear/进程终止后可重算；没有TTL授权、跨主体共享、Redis、语义命中、持久缓存、负权限缓存或在途合并。
- 返回缓存格式化数据时重新JSON解析成副本；真实tools每次重新解析，ModelPrompt每次新建。调用方修改消息/嵌套tool schema不会修改随后命中或真实来源。
- 缓存启用/get/put或内部不可解析条目故障允许重算；这些小范围best effort不包裹任何实际Reader/authority/模型/纯计算错误。撤销、取消、窗口不足或来源变化依旧原样失败。
- 默认ConservativeTokenCounter依旧UTF-8 bytes＋64估算，内部 `cache_version="1"`。自定义counter默认不缓存；只有具体纯计算实现显式提供覆盖算法/全部配置的非空字符串cache_version才启用。key同时包含类型/name、每个counter实例身份和版本；替换实例或改版本不复用旧计数。

### 可选注入与默认关闭示例

以下变量必须由A提供真实port；不代表生产通用authority已就绪。

```python
from uaw.context.cache import PureComputationCache
from uaw.context.facade import ContextComponents
from uaw.context.model_input import GenericModelInputs


def make_inputs(cache=None):
    components = ContextComponents(
        readers=registered_readers,
        cancellation=current_cancellation,
        rules=registered_purpose_rules,
        models=fixed_model_window,
        repository=context_repository,
        authority=current_composition_authority,
        cache=cache,
    )
    return components, GenericModelInputs(components.composer, cache=cache)


bounded = PureComputationCache(max_entries=128, max_bytes=2 * 1024 * 1024)
components, inputs = make_inputs(bounded)  # 可选启用两个内部入口
components_off, inputs_off = make_inputs()  # 默认关闭
components_zero, inputs_zero = make_inputs(
    PureComputationCache(max_entries=0, max_bytes=2 * 1024 * 1024)
)  # 显式零容量同样关闭；max_bytes=0也关闭
prompt = await inputs.resolve(snapshot_ref, trusted_context)
```

A目前composition和Model路由没有被B修改，产品缓存保持默认关闭；真实通用组件的缺authority/Reader分支仍unavailable。

### 三组真实受控例子

来自本worktree实际运行的 `tests/.artifacts/B/MS-C4/examples.json`，完全是受控内存Reader/authority组件，不是SQL/真实LLM或Runner回执：

1. 成功：原文 `"  原文 123.40\r\n"` 仍为user文本；唯一显式generic平台规则为system `"Follow the user"`；approved.read保留完整ToolSpec。估算和无缓存结果相同，没有模型Token减少。
2. 重复：两次相同纯输入，format累计 **1次**、三个Reading的counter累计 **3次**，第二次新增均为0。两次各自仍执行Reader read **16次**、authority.verify **4次**、window.resolve **6次**、rule provider **2次**；正文/来源/规则读取没有减少。零容量对照单元断言两次format为2、counter为12。只证明本地纯计算次数减少，不证明实际延迟/内存/Provider prompt cache收益。
3. 拒绝/版本：warm后撤销Reader返回 `permission_denied`；warm后取消返回 `cancelled`；旧body/classification/rule/tools/epoch改变拒绝，合法新版本snapshot不复用旧格式化。仅固定窗口增1但仍可容纳，格式化累计变2、counter变6；窗口不足仍budget失败，最终命中后发生撤销/取消/epoch/window变化同样失败。

### 实际验证命令与回执

独立忽略回执目录：`tests/.artifacts/B/MS-C4/`。`validation.json`保存实际命令数组、返回码、Python/prefix、公共SHA256和SQL未运行状态；`unit.xml`/`unit.txt`、`ruff.txt`、`format.txt`、`mypy.txt`、`sql-collection.txt`、`sql-fixture-plan.txt`及 `examples.json`保留原始输出。

| 检查 | 本worktree实际结果 |
| --- | --- |
| Ruff check：11个B源码＋B Context unit/integration | exit0，All checks passed |
| Ruff format --check：同范围 | exit0，19 files already formatted |
| Mypy strict：11个B源码 | exit0，Success |
| Context unit全量 | **174 passed，0 failed/error/skip**（原107＋C4新增67）；最终回执9.35s |
| unit＋SQL跨目录collect-only | exit0，**209 tests collected**＝174 unit＋35 SQL；收集没有执行SQL |
| 新SQL `--setup-plan` | exit0，fixture依赖/Windows control-plane loop图可解析，**no tests ran** |
| git diff / cached --check及允许路径检查 | 通过；实现提交仅上列8个文件 |
| 公共文件及A两处兼容修复与ms-i2e逐字节比较 | 通过，均未改动 |

实际静态命令的路径展开见validation.json，可复跑：

```powershell
$bContextPaths = @('cache', 'contracts', 'facade', 'ports', 'repository', 'sources',
    'rules', 'selection', 'composer', 'references', 'model_input') |
    ForEach-Object { "src/uaw/context/$_.py" }
./.venv/Scripts/python.exe -m ruff check @bContextPaths tests/unit/context tests/integration/context
./.venv/Scripts/python.exe -m ruff format --check @bContextPaths tests/unit/context tests/integration/context
./.venv/Scripts/python.exe -m mypy @bContextPaths --cache-dir .cache/mypy/B
./.venv/Scripts/python.exe -m pytest tests/unit/context -q -o cache_dir=.cache/pytest/B --junitxml=tests/.artifacts/B/MS-C4/unit.xml
./.venv/Scripts/python.exe -m pytest tests/unit/context tests/integration/context --collect-only -q -o cache_dir=.cache/pytest/B
./.venv/Scripts/python.exe -m pytest tests/integration/context/test_cache_postgres.py --setup-plan -q -o cache_dir=.cache/pytest/B
```

开发中已修复局部变量类型名、lint及新SQL错误loop标记；最终静态/单元/收集无未通过项。这不把数据库缺环境改称通过。

### SQL未通过项与A接线要求

- 本worktree `UAW_TEST_DATABASE_URL` **缺失**；本轮 **35项SQL尚未实际执行**：原C2 9＋原C3 15＋C4新增11。原C3已由A在基线实跑15的历史接受保持，本轮改动后仍需A实际回归。collect-only/setup plan不是SQL通过，B没有复制A私有配置/凭据或启动共享数据库。
- 新SQL独立模块 `test_cache_postgres.py`：warm重复和返回变异、实际规则/工具/材料/epoch更新、实际政策撤销、实际Run取消、实际原文删除、cache clear/新缓存实例、固定窗口变化、跨Run。读取用真实PostgreSQL，通用规则/tools/epoch是明确受控fixture；窗口变化wrapper也是受控。新实例不冒充进程重启，原C3独立Python进程恢复用例保持。
- A在实际测试连接/集成SHA运行 `./.venv/Scripts/python.exe -m pytest tests/integration/context -q --require-postgres`（35项），按原随机主体清理，不truncate。随后由A执行Model路由、理解输入/native envelope和整条链路回归。
- A决定内部cache是否注入及具体容量；默认不开产品缓存。缺真实生产purpose authority、capability Reader或窗口/取消来源继续不可用，不能挂fixture或用理解模板兜底。
- 无公共DTO/port/配置新增需求；接线说明见 `requests/B/MS-C4-cache-wiring.md`。B不改composition/API/Model/shared/锁，不启用flag，不决定D01/D03/D06。
- 此包仅局部组件，未验证实际Provider、LLM/Agent质量、Runner执行或P4-04多层缓存。缓存不保存唯一状态；退出/clear即丢，回退本包不删除Context持久记录。A负责审阅、合入、公共冲突和完整链路验收。
- 源码与handoff分别提交；本包交接后停止，不自动开始下一包。没有创建或联系其他session。

## MS-C5 最终交接：通用登记到固定模型输入（2026-10-08）

状态：四个连续里程碑完成，B开发交付待A审阅/合入；不自行标P1-02、P1整轮、Agent或P4-04 accepted。保留之前包及阶段提交，未创建其他session，未访问其他worker开发分支；本包后停止。

### 实际工作区、基线和提交

- worktree：`E:/UAW/.worktrees/context`；实际分支：`dev/context`。
- 固定基线：`ms-i2g-start^{commit}` = `0bd8e2b8387a46e16435dc033956c2b69bb1a859`。开工干净后fetch origin --tags、merge --ff-only成功，合并后HEAD与标签commit相等；`uv sync --frozen`在自身worktree成功。
- 前两里程碑阶段源码/接口提交：`d0ad58fbedd4515511544bb3d63bf5f231dad384`，后两项连续完成，没有等待A最终合并。
- 最终源码/接线提交：`8cc445aa4a05a27c25311f9693b8df2bd2ea8c61`（在上述阶段之后）。本handoff另行提交；实际handoff SHA由最终报告及ignored validation.json记录，不自引用修改提交。
- Python：自身`.venv/Scripts/python.exe`，3.14.6；DB：B自身`uaw-development-b`、loopback **55433**。执行`. ./ops/start-dev-db.ps1 -Session B`及alembic upgrade head；没有复制A私有配置/URL/凭据，不清空或操作其他库。

### 修改清单与公开接口

本包相对基线的13个文件（本handoff是另一个文档文件）：

- 源码：`src/uaw/context/registered.py`、`authority.py`、`readers.py`、`contracts.py`、`ports.py`、`composer.py`、`cache.py`。
- B测试：`tests/integration/context/registered_fixture.py`、`test_registered_postgres.py`、`test_registered_chain_postgres.py`、`tests/unit/context/test_registration.py`。SQL模块和单元模块名不同。
- B接口文档：`docs/coordination/requests/B/MS-C5-stage-interface.md`、`MS-C5-wiring.md`。

完整构造、可执行语法样例与消费方影响见[最终接线说明](../requests/B/MS-C5-wiring.md)；以下方法与实际源码一致：

```python
RegisteredContextInputs(*, controller: Principal, records: RecordStorePort,
    blobs: BlobStorePort, transactions: TransactionalStore,
    runs: RegisteredRunSource | None, tool_validator: RegisteredToolValidator | None = None)
await inputs.register_material(text, ctx, *, authenticated_service, expected_revision, meta) -> Ref
await inputs.register_rule(rule: InstructionRule, ctx, *, authenticated_service, expected_revision, meta) -> Ref
await inputs.register_recipe(request: ContextRequest, rules: RulesRequest, tools: ModelToolSet,
    ctx, *, authenticated_service, expected_revision, meta) -> Ref
await inputs.recipe(ctx) -> RegisteredRecipe  # ref/request/rules/tools/owner 的分离结果
await inputs.current(ctx) -> tuple[Ref, ...]  # 实际 Run 全体原文/补充输入
await inputs.read(pin, ctx) -> Reading
await inputs.revoke(ref, ctx, *, authenticated_service, expected_revision, meta) -> None
RegisteredCompositionAuthority(inputs).resolve(purpose, ctx) -> CompositionBinding
RegisteredCompositionAuthority(inputs).verify(binding, ctx) -> None
RegisteredContextReader(inputs).check(ref, ctx) -> None
RegisteredContextReader(inputs).read(ref, revision_policy, ctx) -> Reading
RegisteredRuleProvider(inputs).discover(request, ctx) -> RulePlan
GenericModelInputs(components.composer, cache=cache).resolve(ref, ctx) -> ModelPrompt
```

后半包保留前三个固定登记签名与GenericModelInputs/TokenCounter签名。`ModelToolSet`是B类型对既有公开schema的严格映射。内部`CompositionBinding.request: ContextRequest | None = None`保持旧消费者默认行为；registered authority给出精确实际配方，Composer拒绝参数绕过，纯计算键覆盖它。未导入Model私有ProviderRequest/Response。

来源读真实命名schema记录和主体隔离FS blob；每次实际Run/政策、完整用户/session/scope/固定模型、epoch、规则/tool版本、取消及期限复查，提交后也复查。材料只能material/external，不由正文升格指令。规则保留level和固定来源；原文包括空格、换行和实际补充输入，保护全体whole pin。绑定不以operation/trace/attempt/deadline/budget reservation冒充长期身份。

登记采用已有事务/advisory lock、CAS/参数幂等，多条明确schema一起提交；完整payload/owner摘要写`context.registered.seals`（Ref），分类/规则level/配方元数据变化也拒绝。撤销tombstone与`context.registered.revoked`（Ref）原子保存，同meta重放仍核对当前授权，改参数冲突；ID不复用。阶段版仅诊断，最终版全链使用新Run重新登记，不把缺seal旧记录补成可信数据。

材料最多64KiB UTF-8；规则还受既有NonEmptyText 16384字符约束；材料/规则每Run最多64登记ID（生命周期上限，撤销不退款），配方最多64实际来源/规则/tool，单登记参数最多256KiB。无新增表/迁移/公共schema。blob先存，SQL失败可能有未引用内容，不授权读取；没有制定新的GC政策。

### 真实回执与原模块回归

自身ignored回执：`tests/.artifacts/B/MS-C5/`。`validation.json`记录分支、基线/阶段/最终源码SHA、命令、原始XML摘要、逐用例去重结果、修正历史、Python/环境、公共文件SHA；`office-input.json`是实际SQL/blob组装样例，包含固定snapshot/配方/原文/材料/规则Ref、实际消息/工具和完整估算，无数据库URL或密码。子进程恢复的URL只经stdin，不进入argv/log/evidence。

| 实际检查 | 结果及回执 |
| --- | --- |
| Context全部单元 | **208 passed**＝原174＋MS-C5新增34；0 failed/error/skip；`final-unit.xml`，11.77s，exit0 |
| 新MS-C5 SQL/FS blob/独立进程 | **39个不同用例全部最终通过**；原始`registered-final.xml`为34 passed/1 failed（第二Run仍queued的测试准备错误），正确调用Run.advance(preparing)后`cross-run-repair.xml` **1 passed**；另外`registered-supplement.xml` **2 passed**、`final-io-recheck.xml` **2 passed**。保留原始失败，不改写成零失败XML |
| 原Context SQL＋理解/Model路由兼容 | `original-regression.xml` **46 passed**＝原C2 9＋C3 15＋C4 11＋A理解/窗口/native envelope/路由11；0 fail/error/skip，516.54s，exit0 |
| 最终逐用例合计 | **208 unit＋74 Context SQL＋11兼容SQL＝293个最终通过**，未解决失败/错误/跳过 **0**。不是一次全量293运行；来源为上述真实XML和针对性修复回执 |
| Ruff check / format --check | 14个精确B允许源码＋B测试，exit0 / exit0，All checks passed / 26 files already formatted |
| Mypy | 14个B源码，exit0，Success；`final-mypy.log` |
| 原文/注入材料办公样例 | SQL实际3条消息（system/user/user），显式0 tools，完整估算6060；是准备输入，无真实LLM成果质量声明；`office-input.json` |
| 允许路径、字节与diff检查 | 通过；shared/schema/锁/A seed/intent/composition/Model/router以及两处accepted Ref/Windows测试兼容修复与基线逐字节相同；`public-boundaries.json`、`allowed-files.json` |
| unit/SQL跨目录收集 | 282 collected＝208 unit＋74 SQL；无重名；仅结构检查，不计实跑通过 |

实跑覆盖：可信完整controller/owner/session；实际Run、原文/patch和固定模型；材料blob及规则实际来源；登记/配方CAS、并发幂等/竞争、独立Python进程重启/重复；build→固定snapshot→ModelPrompt→引用定位；缓存可选/零关闭/返回变异隔离；材料/规则/工具/配方修订与撤销；实际policy/provider撤销和Run取消；blob读后发生删除/取消的最终复查；同revision分类/规则/配方元数据损坏；实际blob缺失/腐坏；跨主体/有效Run；容量回滚、窗口不足；材料注入不升格；原文whole保护及slice不扩大；未知Reader、多规则语义判断缺失明确unavailable。

`ControlledSQLTools`仅是明确受控的当前SQL ToolSpec验证port，用于验证B会复查完整定义/版本/删除；不证明生产ToolAccess/flags/role/资源授权。旧原模块HTTP协议和语义回复也为明确受控fixture。B新的authority/Reader/RuleProvider来自生产目录实现，不借fixture authority成功，不调用LLM或Runner。

实际主要命令（PowerShell，每次新shell重新加载自己的B环境）：

```powershell
. ./ops/start-dev-db.ps1 -Session B
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m pytest tests/unit/context -q --junitxml=tests/.artifacts/B/MS-C5/final-unit.xml
.venv/Scripts/python.exe -u -m pytest tests/integration/context/test_registered_postgres.py tests/integration/context/test_registered_chain_postgres.py -vv --require-postgres --junitxml=tests/.artifacts/B/MS-C5/registered-final.xml
.venv/Scripts/python.exe -u -m pytest tests/integration/context/test_registered_chain_postgres.py -vv -k real_cross_run --require-postgres --junitxml=tests/.artifacts/B/MS-C5/cross-run-repair.xml
.venv/Scripts/python.exe -u -m pytest tests/integration/context/test_registered_chain_postgres.py -vv -k 'injected_material or provider' --require-postgres --junitxml=tests/.artifacts/B/MS-C5/registered-supplement.xml
.venv/Scripts/python.exe -u -m pytest tests/integration/context/test_registered_postgres.py -vv -k final_recheck --require-postgres --junitxml=tests/.artifacts/B/MS-C5/final-io-recheck.xml
.venv/Scripts/python.exe -u -m pytest tests/integration/context/test_snapshots_postgres.py tests/integration/context/test_model_input_postgres.py tests/integration/context/test_cache_postgres.py tests/integration/test_context_wiring.py tests/integration/test_model_input_routing.py -vv --require-postgres --junitxml=tests/.artifacts/B/MS-C5/original-regression.xml
$bContextPaths = @('cache','contracts','facade','ports','repository','sources','rules','selection',
    'composer','references','model_input','registered','authority','readers') |
    ForEach-Object { "src/uaw/context/$_.py" }
.venv/Scripts/python.exe -m ruff check @bContextPaths tests/unit/context tests/integration/context
.venv/Scripts/python.exe -m ruff format --check @bContextPaths tests/unit/context tests/integration/context
.venv/Scripts/python.exe -m mypy @bContextPaths --cache-dir .cache/mypy/B
```

修正记录：阶段首次SQL 6/7通过，缺binding.request接线修正后7/7；新规则边界测试误以为可先构造非法DTO，改为绕过构造的实际再校验边界，最终208单元通过；回归首次写错文件名exit4/no tests ran，改正确文件后46通过；期间自动审批额度失败导致两个SQL运行没有完成回执，未计通过，随后重跑有完整回执；完整SQL中上述queued准备错误用已有Run API修正并定向通过。源码无未解决失败，原始历史回执不隐藏。期间一次自动审查误将B的context/composer.py等同A的composition.py，出示B允许目录证据后通过；不修改A组装根。

### A接线要求与明确未完成依赖

1. A在可信内部组装根提供实际完整service controller和当前认证adapter；当前登录/session真实性需A验证，既有Run记录不保存完整auth_session，B不从body自证登录。不要把登记入口暴露给HTTP/模型或把caller工具字段当授权。
2. 接`RunContextSources`及实际ExecutionPolicyPort、owner-isolated BlobStore、RecordStore/TransactionalStore、FixedModelWindow；以[接线说明](../requests/B/MS-C5-wiring.md)构造ContextComponents和GenericModelInputs，并在已有ContextModelInputs路由中注入通用resolver。seed/intent理解链保持原路由。
3. 非空工具集必须注入`RegisteredToolValidator.check(ModelToolSet, ctx)`的生产adapter，查真实固定目录/version/provider、flags、role/资源与当前权限；缺该来源明确unavailable。B没有消费C未交接Lookup/Reader/executor，受控SQL validator不可挂生产。
4. cache默认None；A可显式选择`PureComputationCache(max_entries=128,max_bytes=2097152)`并同时给components/model inputs；任一容量0关闭。仍读取当前authority/Reader/tool/规则/window/取消并最终复查，只减少已验证内容的纯格式化/估算；不宣称provider prompt cache或Token/延迟收益。
5. 多个规则的真实固定模型冲突判断、skill/memory/Board/本机文件、scope_paths、requirements/pending actions以及分页/压缩来源仍明确不可用；空工具/空或单规则仅限实际显式登记。Model实际网络调用仍待D06。未实现依赖没有空fallback或替身成功。
6. A审阅、合入、处理公共冲突，按最终源码实跑关键链及相关受影响模块；集成里程碑再做全量，不把本包模块293通过当P1整轮验收。不开放flags，不自行决定D01/D03/D06；保留accepted C3/C4及历史handoff，本包交接后停止。
