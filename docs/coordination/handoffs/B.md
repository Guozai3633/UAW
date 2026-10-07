# Session B：MS-C1 实际交接

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
