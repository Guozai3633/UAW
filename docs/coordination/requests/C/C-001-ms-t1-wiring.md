# C-001：MS-T1 到 MS-I2 的接线需求

- Session C / MS-T1 / P1-03。
- 开工基线：`70f2fcccb88650c616920a5630d2caa45d94ad45`，固定 `parallel-wave-1`；实际目录 `E:/UAW/.worktrees/tool`，分支 `dev/tool`。
- 状态：提案待 A 审阅，未假定已批准；本包没有修改公共文件，没有注册产品工具或启用 flag。

## 最小集成改动

A 在 `src/uaw/composition.py` 提供 `ToolFacade(ToolRegistry(), access=..., precheck=..., recheck=...)`。暂不提供 dispatch port；即使两个检查均通过，MS-T1 也返回 `dependency_unavailable` / `failed_phase=dispatch`。`shared/ports.py` 的既有 `ToolPort.invoke(request, ctx)` 可直接接 facade，不需要修改签名。注册只供可信管理/组装端调用，没有模型注册入口。

`src/uaw/tool/ports.py` 的本包内部 port 不新增 wire DTO：

1. `ToolAccessPort.snapshot(ctx) -> ToolAccess`：A adapter 按原固定配置与当前配置求交，解析 RoleProfile、CapabilityPolicy、有效 flag、执行环境、提供方撤销及 Run 取消。`scope` 必须是可信 `ctx.scope` 的子集；主/会话/任务/项目不可改变。`allowed_capabilities` 必须已包含所有父政策上限，显式 deny 优先。`enabled_flags` 必须是固定/当前配置、主体范围交集后的结果，缺失关闭，不能直接把配置等同用户授权。`policy_ref` 要与 `ctx.capability_policy_ref` 精确一致。新政策与旧可信上下文冲突返回 stale，让 A 的控制流程重新决策，不自动改用户模型/权限。
2. `PrecheckPort.precheck(validated_call, trusted_spec, ctx)`：消费已有 ValidatedCall、ToolSpec、TrustedExecutionContext，返回已有 `ComponentToolInvocationPrecheckResult`。适配器负责真实预算/权限/资源解析、调用记录与审批绑定；缺依赖返回显式失败。等待返回 `kind=waiting` 和真实存在的 `wait_ref`，不能用 `ok`/布尔 approved 冒充。`allowed=false` 不继续；`approval_required=true` 且没有真实 wait 返回不可用。attempt_id 来自 ctx，action_id 来自已规范 ToolCall；重复 action 不得重复预留预算/创建审批。
3. `RecheckPort.recheck(validated_call, trusted_spec, precheck_result, ctx)`：返回已有 `ComponentToolInvocationRecheckResult`。适配器必须核查存储 call_ref、参数 hash、资源版本、审批期限、主体、撤销与取消，保存真正依据；不能用示例 Ref 假装已持久化。变化返回 stale/denied/cancelled。Facade 在每次 await 后重新读取访问快照，并检查依赖没有修改参数/ToolSpec/ctx。

三个 port 尚无生产实现，因此不依赖 B/D 的未交接源码。本包只消费基线 `shared` 契约/错误/校验函数。

## 目录与 adapter 元数据

ToolRegistry 是有界进程内组件目录，默认 128 个不可变 `(id, version)`；CAS revision 原子更新。同版本同 spec/binding 重复返回现有 revision，同版本不同内容或 binding 冲突。后续真实持久目录的配置读取/刷新由 A 明确；不是 D01 存储决定。

`AdapterBinding(provider_ref, environments, implemented=False, test_only=False)` 为内部元数据，不改变 ToolSpec；`implemented` 只能由可信组装对已实现 adapter 赋值，不能来自模型/HTTP。未绑定、未实现、test_only、非批准环境或提供方不活跃均不发布候选，也拒绝直接调用。本包不会执行 metadata binding。产品目录默认为空；测试的声明绑定只存在于 fixture。执行 API 与真实 adapter 留给 MS-T2。

ToolSpec 的 schema/内容与版本固定；模型 ToolCall 只允许既有字段。读取/发现使用既有 RefKind `configuration` 来引用实际注册的工具配置，含固定 `id/version/content_hash`；不增加未经批准的 `tool` RefKind。A 集成时确认与配置储存命名空间一致；旧入口目前未实现，没有旧运行调用受影响。真实 call/approval/provider refs 仍由相应状态所有者产生。

## schema 范围及效果恢复缺口

目前支持 JSON Schema 2020-12 的显式单类型、关闭对象、必填/枚举/数值/长度/格式限制、有界数组和非循环的本地 `$defs` 引用。64 KiB JSON、深度24、4096结构/展开节点；注册容量最多256；数组 maxItems最多256。拒绝远端引用、动态引用、循环、pattern、组合 schema、不支持的关键字和开放对象，返回 `registration_invalid`，不降级为宽松校验。暂不需要新的 Python 依赖。A 要接复杂现有工具 schema 时先交回 C 扩展可验证的安全子集，不直接开启远端解析。参数只排序 JSON 字段，不 trim/NFKC/改换行，不填默认值，不把省略改 null。真实资源定位由预检/复核 port 完成，schema 通过不代表资源已授权或可用。

process 效果强制 `code_execution`，workspace_write 强制 `local_files`；ToolSpec 的其他 feature_flag 也必须启用。它们只被检查，本包从未修改配置。effect 总从固定 ToolSpec 读取，模型不能自报。ToolAccess adapter 应对其他目录工具的领域 flag 保持既有规则。

当前 EffectState 只有 confirmed/pending/unknown，无“已确认未发生”状态。`require_safe_recovery` 对这三种非 read 效果一律拒绝恢复；没有自动重试或等价工具切换。MS-T2 如需安全写恢复，请 A 决定最小协议（例如独立、可核验的对账结果：actual_not_applied + provider evidence_ref + 固定 retry_policy_ref，而非自行扩充状态）。此建议未获批准，未实现或消费建议字段。

ActionIdentities 只作进程内动作冲突检测，不是持久幂等/效果账本，不跨重启保证 exactly-once。按 principal/run/action 分区，绑定工具版本/内容 hash、参数、scope、agent/task/node、固定模型/能力政策版本；attempt_id 不进入逻辑动作 hash。满容量拒绝，无 TTL 忘记动作。MS-T2 的 durable ledger、dispatch/settle、原 Run 预算和外部幂等仍待 A 给出公开 port，不能沿用内存 guard 冒充。

## 成功/拒绝/重复示例

可执行组件例子：`.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider`。

- 成功：`test_discovery_returns_only_candidates_and_invocation_remains_unavailable` 的受控 catalogue 返回 `kind=ok`、固定候选与目录 revision；模型保留选择权。该 fixture 不表示产品工具已连通。
- 拒绝：`test_feature_flag_and_test_only_or_unimplemented_adapter_are_not_published` 的关闭 local_files 或 test_only adapter 不可发现/调用；模型自报 owner/approved 在 normalize 拒绝。
- 重复/冲突：`test_verifiable_wait_propagated_and_changed_parameters_conflict` 使用受控真实结构 wait_ref；相同 action 换 attempt 保持等待，同 action 换 count 返回 `action_conflict`，不进入后续检查。该审批引用仅为测试替身，不是生产批准回执。

## 消费方、验证与回退

A 的 composition/API/管理配置是接线方，后续 Agent 只消费候选和 ToolPort 结果；Run 仍唯一拥有取消、审批/预算等业务状态，工具组件不会覆写原文、用户模型或 Run。B/D 无需在未合入前消费本包。

无新依赖锁、公共 DTO、数据库迁移、事件类型、系统账号配对、外部写入。A 合入后运行真实 SQL/组合回归再决定能力开放。MS-T2 仍须 MS-I2 新基线；D01/D03/D06 未设定。需要回退时由 A revert 本包源码提交和接线提交，不动其他 session 文件；没有已执行的业务副作用。

A 决定/真实发布 SHA/组合验证：待填写于 DISPATCH；本 session 不维护公共派发表。
