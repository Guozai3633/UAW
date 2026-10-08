# MS-I2g：A 当前来源与阶段接线

日期：2026-10-08。A / E:/UAW / integration。开发基线 ms-i2g-start。

## 1. Run 与用户固定模型

`src/uaw/run/execution_sources.py`：

```python
RunExecutionSources(records, configuration, execution_permissions)
await sources.current(ctx) -> RunSourceSnapshot
await sources.data(ctx) -> RunDataSnapshot
```

current 核对实际 Run/权限链、当前取消/期限、会话/任务范围、实际 run.bindings、固定 model.policies 的 revision/hash、用户选择 InputRecord 和配置。角色的模型候选不会改用户模型。data 读取同一实际归属与固定模型来源，供取消/过期后的结果恢复，不提供执行权限。两个方法都消费由可信入口构建的 ctx，不负责从请求正文认证用户；实际完整 session 由 Tool 登记绑定或 Runner 通道再核对。

## 2. Tool 角色和执行授权

`src/uaw/run/tool_sources.py`：

```python
RunToolAccessSources(records, configuration, run_sources,
    *, environment: str, implemented_flags=frozenset())
await access.register_role(profile: RoleProfile, meta,
    *, authenticated_service: Principal) -> Ref
await access.bind(ctx, role_ref, meta,
    *, authenticated_service: Principal) -> Ref
await access.revoke(ctx, meta,
    *, authenticated_service: Principal) -> Ref
await access.snapshot(ctx) -> ToolAccess
```

这是内部控制入口，没有新增 HTTP 或模型工具。service 必须精确匹配平台 controller 的完整 Principal；登记前核对实际 Run/政策/用户模型。RoleProfile 只提供允许类别，指令/技能的读取由 Context/Skill 自己负责，登记元数据不证明指令已经可读取。

角色在平台主体分区 `run.tool.roles` 保存现有 RoleProfile；版本使用数字 SQL revision，Ref 固定内容 hash。修改角色使旧引用失效。每个 Run/Agent 槽位在 `run.tool.bindings` 保存新的严格 **RunToolAccessBinding**：完整 Principal/session、scope、固定模型/能力政策、role_ref、部署 environment、revision、state。主 Agent 和每个子 Agent 单独登记，未绑定没有默认权限。登记不能转移 owner/session，变更走 CAS，撤销在 Run 取消后仍可执行。

snapshot 从实际权限链取有效能力/deny，从实际角色取类别，提供方同时存在于固定和当前配置且当前 active/revision/hash 一致才可用。功能开关还须部署显式 implemented_flags；默认空集合。最后复查绑定、角色、Run/配置和提供方。它是当前观察，调用器在发送前仍须再次检查；不是租约或永久授权。

新 schema 是添加对象，没有改旧输入输出/枚举/共享 port、依赖锁或数据库表。生成文档在 `docs/api/objects/RunToolAccessBinding.md`。B/C/D 当前包继续固定 ms-i2g-start，最终合入时由 A 提供完整 schema 和装配。

## 3. 资源与恢复读取

```python
PureTextResourceReader(registry, access, exact_tool_ref)
await resources.resolve(call, spec, ctx) -> tuple[Ref, ...]
RunToolRecoveryAccess(resources, ledger, *, provider_ref, provider)
await recovery.check(call, spec, ctx, *, provider) -> None
```

资源 Reader 只承认确切登记的 text.inspect、effect=read、有界且唯一 text 参数、固定 spec/call/hash。它检查当前角色和执行授权后返回空资源集合；任意路径/联网/写入/其他工具需要相应领域 Reader，不能沿用空集合。

恢复接口独立读取原 ledger action/attempt/call/spec、完整当前绑定 session、角色、实际 Run/模型/配置和提供方。provider 是可信构造固定的完整 service Principal，不从 body 取。取消/过期与新执行权限不影响已有纯文本结果的数据读取；角色绑定撤销、主体/session改变、固定来源改变、提供方撤销会阻止读取。只读恢复不 reserve、不 dispatch、不审批、不生成新 attempt。外部资源没有通用恢复放行。

## 4. Runner 归属与装配

`src/uaw/run/runner_mapping.py`：

```python
RegisteredRunnerPrincipalMapping(devices)
await mapping.owner(*, authenticated_principal, device_id) -> Principal
assemble_runner_control(container, *, channels, root_factory, gate, signer)
    -> RunnerControlBindings
```

mapping 实现 D 的既有关键字接口，读 RunnerDevices 的实际设备/通道、完整 actor/session、归属、撤销和有效期，不读命令自报 owner。root_factory 接该实际 mapping，再构造 D 的根适配器。装配复用 A 当前 records/config/policy/budget/lease，返回 devices/principals/commands/authority/receipt_commands。没有自动发布路由或更改 flags；真实通道/本机确认/密钥/动作审批仍由相应 adapter 提供。

Container 默认提供内部 run_sources/tool_access/runner_principals；没有角色登记即明确不可用，Tool/Workspace/Agent 公共入口仍需完整包及实际来源验收。

## 5. 验证与继续条件

A 当前来源的27项用例实际通过，包含真实 SQL：角色登记与重建、审批 authority 消费、kind/session隔离、固定政策/模型/范围、修改失效、撤销后丢失响应重试、并发CAS、取消后结果数据读取、provider撤销、实际设备mapping及装配。实际回执 `docs/implementation/evidence/ms-i2g-sources-tests.xml`。该回执不替代 worker 模块 SQL 或集成里程碑全量。

阶段版分别审阅 C 的 C-005、D 的 R2d-001、B 的 MS-C5-stage-interface；最终组件接受须各自后半包完整回执。A 的边界改动与 worker 的领域实现分别保留提交，公共接线由 A 维护。
