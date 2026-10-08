# MS-I2f1：A 的设备归属、命令登记和当前权威

日期：2026-10-08。开发基线 `ms-i2e / ba2f3b0`。这是 MS-I2f 的首个可独立验收子包；完整 MS-I2f 还包含真实通道、根来源、角色/资源审批和签名密钥后端接线。

## 工作包在哪里定义

| 位置 | 定义什么 |
| --- | --- |
| `planning/parallel_catalog.py` 的 PACKAGES | 包编号、功能目标、负责人、前置包、任务和验收；并行计划的维护源 |
| `docs/plan/sessions/A.md` 等 session 页 | 该 session 的文件归属及各包摘要，由维护源生成 |
| `docs/coordination/requests/A/MS-I2e-next-packages.md` | B/C/D 当前包的详细输入输出、策略及边界 |
| 本文件 | A 首个子包的具体实现范围、接口、状态和验证 |
| `docs/coordination/DISPATCH.md` | 实际开工、基线、交付、接受和接续状态 |

工作包按可以独立交付与验收的功能目标划分，不等于 Python package、单个目录或一次聊天。一个目标可以跨模块；文件写入归属仍唯一。计划中的完整阶段与一个组件包的接受分开。

## 1. 目录与对象

- `src/uaw/run/runner_devices.py`：真实 PostgreSQL 设备/当前通道拥有者记录与撤销。
- `src/uaw/run/runner_commands.py`：不可变业务请求、已签名命令登记、恢复读取和命令撤销。
- `src/uaw/run/runner_authority.py`：以登记数据重建当前 AsyncRunnerAuthority，不从收到的命令上下文取得拥有者。
- `src/uaw/run/budget.py`：增加一次 MVCC 查询的执行账务快照，保留已有读写 port。
- `src/uaw/shared/ports.py`、`contracts/interface_catalog.py`：新增严格命名对象及内部 port；所有持久 payload 有命名 schema。
- `src/uaw/composition.py`：组装服务；通道/根/动作闸门/签名后端缺失时拒绝，不挂载新 HTTP、Runner 或模型工具。
- `tests/integration/test_runner_control.py`：A 独立 SQL/真实签名/当前状态验证，不修改 B/C/D 的测试。

设备/请求/命令记录由平台主体的 `runner.*` 命名空间持有；绑定中保存原用户拥有者，平台分区不是用户读取权限。签名只保存公开签字值；私钥和凭据不进入记录、日志或请求 DTO。

## 2. 方法与来源

| 服务 | 方法 | 输出 / 约束 |
| --- | --- | --- |
| Devices | bind(request, meta, authenticated_service) | RunnerDeviceBinding；读取独立当前 channel 来源，服务身份固定匹配，CAS，owner 不可转移 |
| Devices | current(device_id, authenticated_principal) / owner(principal, device_id) | 当前绑定 / 原用户；每次读取通道、主体/会话、拥有者、key/配对来源和期限，不缓存权限 |
| Devices | revoke(device_id, expected_revision, meta, authenticated_service) | 持久撤销；允许清理，不重新授权 |
| Commands | register_request(request, meta, ctx, authenticated_service) | 固定 Ref；保存真实原 ctx/parameters，版本1，不接受模型/网络自报可信上下文 |
| Commands | register(request, meta, authenticated_service) | RunnerCommandRecord；读取已登记 request/device、实际根、权限/模型/配置、预算、lease，再签名和复核 |
| Commands | read(command_ref, authenticated_principal) | 固定已登记命令；独立设备/当前数据权限校验，允许取消/过期 Run 的原记录恢复，不创建执行准入 |
| Commands | revoke(command_id, expected_revision, meta, authenticated_service) | 持久禁止新准入，原签字正文保留供恢复 |
| Authority | current(command, authenticated_principal) | 既有 RunnerAuthoritySnapshot；从平台命令索引定位独立登记源，收到的所有字段仅作精确比较 |
| Budget | execution_state(reservation_id, ctx) | BudgetExecutionSnapshot；同一查询返回实际 ledger/reservation/attempt deadline/dispatch 意图，查询不授权发送 |

通道、根、动作闸门和签名 port 是独立可信来源。缺任一 port 不返回“默认批准”。动作闸门负责当前角色、所有实际资源及需要的审批；它不能由命令参数或模型输出替代。通道 port 的产品后端仍需要真实配对/认证/IPC；本包不发布配对 V2。

### 2.1 内部来源 port

实际 Python 签名见 `src/uaw/shared/ports.py`，JSON 返回值必须通过对应命名 schema；这些是内部注入边界，不是 HTTP 或模型控制工具。

| Port | 输入 / 返回 | 来源与约束 |
| --- | --- | --- |
| RunnerChannelSourcePort.read | `channel_ref: Ref`，keyword `device_id: str` → RunnerChannelSnapshot | 独立认证通道/配对/key 注册来源；不能把请求 body 的 owner/actor 包装返回。当前连接与期限校验，单次读取30秒上限 |
| RunnerRootSourcePort.current | `device_id: str, workspace_ref: Ref, ctx: TrustedExecutionContext` → RunnerRootSnapshot | 实际本机授权根的 owner/workspace/version/action/期限；root_handle 为 opaque ID，不接受本机路径授权 |
| RunnerActionGatePort.check | `request: RunnerRequestRecord, ctx: TrustedExecutionContext` → `None` | 复核当前角色、所有实际资源及需要的用户同意；拒绝抛 DomainError。非 None 返回也拒绝，不能将模型判断当真实审批 |
| RunnerCommandSigningPort.sign | `draft: RunnerCommandDraft`，keyword `device_id: str` → RunnerCommand | 控制服务 key 的实际签名；仅增加 signature，任一业务字段变化拒绝；签字等待受 command 期限约束 |
| RunnerCommandSigningPort.verify | `command: RunnerCommand`，keyword `device_id: str` → `None` | 当前 control key/device/domain/撤销与真实密码学验证；非 None 返回拒绝，不从收到的文档读取授权 key |
| BudgetExecutionStatePort.execution_state | `reservation_id: str, ctx: TrustedExecutionContext` → BudgetExecutionSnapshot | 真实已拥有 Run/ledger/reservation/accounting 同一 MVCC 查询；原 operation/trace/attempt 必须匹配。查询允许取消后恢复，不授权外发 |

### 2.2 固定引用、失败与版本

- request Ref：`kind=check`、`version=1`、`content_hash=parameter_hash(RunnerRequestRecord)`；签字 command Ref：`kind=content`、`version=1`、摘要覆盖原 RunnerCommand。缺摘要、正文/版本变化拒绝，不是只校验 DTO 类型。
- device Ref：`kind=device`、当前 revision 与完整 RunnerDeviceBinding 摘要；lease Ref：既有 `kind=lease` 和实际 lease revision/fence，沿用根租约精确 Ref 规则。
- state revision 与不可变签字正文的版本分开：撤销 command 增加状态 revision，原 command Ref 保持版本1。撤销不改写签字内容。
- 幂等参数覆盖实际请求/控制服务或原 ctx；相同 RequestMeta.request_id + 相同参数恢复真实原响应，再做当前检查；换参数冲突。原 attempt 唯一命令身份独立于 request_id。
- `runner_service_denied/runner_actor_denied/runner_owner_transfer_denied/runner_root_denied` 等身份/范围错误为403；固定来源变化一般412；CAS/终态/预算或期限拒绝一般409；未登记资源404；缺实际能力 `capability_unavailable` 为503。严格 schema 错误不能当作授权通过。
- `asyncio.timeout` 产生 TimeoutError，取消传播 CancelledError；本包没有 HTTP 映射入口。后续适配器应按超时/取消展示，不能据此推断命令未登记、未发送或允许重试。

## 3. 当前权威策略

1. 只接 file.read/file.list 的授权检查；写入、进程和安装仍不可用。
2. 对已登记 command/request/device 做精确版本/正文/主体绑定校验；业务参数或 ctx 变化冲突，不能换 command ID 绕过同一原 attempt/action 的身份。
3. 从存储 request 取得 Run/ctx，检查实际 Run 与固定用户模型、当前父子政策、资源范围、当前/固定 local_files 开关及独立动作闸门。
4. 预算快照必须属于原 operation/trace/attempt，仍持有额度且实际账本已有 dispatch 意图；这个意图不证明外部已执行。取消、超额、过期和结算后的额度不准入。
5. 从实际根来源取得 workspace/root handle/binding revision/期限，精确匹配保存的根版本；从根租约服务取得当前 holder/session、版本和 fence，不信收到的 fence 声明。
6. 两次收集当前来源，关键 await 后再次核对；源版本、政策、配置、预算、根、设备或 lease 改变则拒绝。实际时钟在 await 后复查。
7. SQL 事务只保存本 owner 记录；不在 Runner 平台锁内嵌套调用 Run/Budget/Lease 或外部 Reader。登记后再复查，复查失败的记录不能作为发送授权。跨 owner 的这些复核不保证原子执行；真实执行器必须在实际发送/执行前消费当前 fence/撤销。
8. 重放同一请求取得真实原记录，但仍做当前准入检查；撤销/接管/过期后的旧响应不能再批准。恢复读取则不调用新执行 gate 或恢复预算 dispatch；它读取原命令元数据，不授予其涉及文件的内容访问。完整 Principal 包含 session，跨登录重认证/迁移由后续产品协议定义。

## 4. 必要验证与退出条件

真实 PostgreSQL 覆盖设备绑定/跨主体/当前 session/终态与CAS；请求及命令不可变、重复/响应丢失、实例重建、参数伪造；当前政策/预算/取消/配置/根/lease/通道变化；等待期间到期与并发撤销。签名测试使用真实 Ed25519，Reader/gate/通道属于明确受控来源，不冒充产品连接。

静态、格式、类型、全量 SQL 与契约/计划检查通过后发布本子包。B/C/D 开发中的固定基线继续 ms-i2e；本包不要求他们中途消费新 port。没有真实通道/根/密钥后端时，完整 MS-I2f/MS-I2 仍未验收。

## 5. D 当前包的 Ref 类型勘误

MS-I2e 的 D 范围里写了 `runner_receipt`，但当前 RefKind 没有登记这个值。D 的 MS-R2c 在原基线使用 **`Ref.kind=content`**，`runner_receipt` 仅指 owning-domain 的命名空间；精确来源由 journal/Reader 校验。不要在私有 DTO 添加枚举值，也不需要为此切换开发中的基线。后续若增加专用 wire kind，由 A 单独发布版本。其他 MS-R2c 策略不变。
