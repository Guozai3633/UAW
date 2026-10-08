# D-R2b-001：异步 Runner 组装与后续执行协调

日期：2026-10-08；D / MS-R2b；基线 `ms-i2c` = `1411f6aa477b0d000bee871c0f324fbfd67b4ff5`。组件提案/接线说明，待 A 审阅；不修改公共 schema、锁或 routes，不发布配对 V2。

## 已消费的公共接口

`AsyncRunnerAuthorityPort.current(command:JsonObject, *, authenticated_principal:Principal) -> JsonObject`，结果通过 D 的严格 `RunnerAuthoritySnapshot(ContractModel)` 消费权威 0.1 schema。15字段全部必填，无默认能力、期限或状态；context/Ref完整验证。每次传新wire副本，adapter不能改留存的签字命令。新 `RunnerProtocol.admit_async(data, *, authenticated_principal)` 不退回旧同步 authority；旧 `admit(data,now)` 保留兼容。

## A 需要提供或分配的适配器

1. **可信通道**：只有认证过的 IPC/受控传输adapter能传 authenticated_principal，不能从 command.trusted_context.principal 构造。IPC缺失本轮不挂载任何网络/API入口；组件测试只直接调用内部方法。user和runner通道可消费，admin/service不默认具有项目读权。
2. **当前 device ownership**：D新增内部 `RunnerPrincipalMappingPort.owner(*, authenticated_principal,device_id)->Principal`，每次从登记设备/用户/通道会话真实关系得到当前user owner；不能读command/用ID字符串相等自证。runner principal必须验证设备与当前认证session实际归属；user principal也须真实拥有该设备。D只比对返回的完整Principal与command/authority，缺port或登记关系不可用。production实现归A的身份/设备owner；如需要公共导出，A调整shared port并发新固定版本，D不私改共享文件。
3. **AsyncRunnerAuthorityPort真实实现**：根据原已登记请求、固定context（包括原文引用/用户模型/预算/Run/agent/node/scope）、当前policy父链交集、配置flags、设备/key/root撤销、workspace绑定版本、request内容/版本、lease/fence/取消独立查询。每次await后拿实际clock，不缓存许可。本包 ComponentAuthority 只有明确组件records，不宣称连接SQL/真实权限服务。
4. **当前本机检查**：注入真实SignaturePort/current key目录和已获准RootBindings。已有Ed25519SignatureAdapter每次真实验签并查当前key role/revoked；根检查是本机元数据/realpath与撤销，不打开用户文件，不提供OS隔离。
5. **admission仓储**：新内部 `CheckedAdmissionRepository.reserve_checked(principal,device,Admission,*,check)->Admission` 在CAS/锁内调用期限与协作取消guard，重放也检查；缺guard能力不静默退回旧reserve。Memory支持，PersistentAdmissions是显式临时SQLite适配器。部署仓储、持久DTO和SQLowner仍待A/D01；控制面不能把这些内部字段当未发布wire。

公共修改仅需组装/身份映射/authority/仓储adapter；RunnerAuthoritySnapshot 0.1字段无需修改。composition/application/routes/设备目录ACL/真实authority与持久迁移由A处理；D在发布后消费。不得把测试适配器注入Container作为真实服务。

## 流程和比较规则

- 严格解析命令/通道Principal → 当前设备owner → 第一份authority → worker线程真实key验签/根路径检查 → 第二次owner → 第二份authority → 所有snapshot字段与第一次精确比较 → worker再次查本机key/root并按最新snapshot检查 → 锁内期限/取消guard → admission CAS → await返回后再次clock检查。
- context与固定command声明完整比较（包括attempt/trace/deadline及所有Ref），request_ref/parameters/policy/fence逐项等价；device与本机固定设备相等。workspace_ref必须是固定workspace版本且在有效scope中，当前required_capability/allowed_actions/flags/connected/取消都检查；根句柄/绑定revision通过实际本机RootBindings核对。
- snapshot内无command声明的当前字段也不凭默认接受：lease到点拒绝，flags/连接/取消有明确语义，root/revision有真实本机记录，所有字段跨两次权威变化拒绝。原command与snapshot都只有 read/list 准入，安装/write/exec保持不可用。
- 回调和数据比较没有`asyncio.run`桥接。阻塞key/path/SQLite操作只通过`asyncio.to_thread`，SQL锁等待不会堵事件循环；clock为可信组装注入（默认UTC实际时钟），模型/HTTP body不能传now延期期限。
- cooperative cancellation直接传播CancelledError；没有用宽泛异常转换它。已排队CAS worker通过取消Event在锁内检查，取消先到则不插入。若CAS在取消/期限变化前已真实提交，保留原admission，不能伪装没发生；记录不是执行receipt/权限。

## 持久身份与错误例子

PersistentAdmissions开发表：`(principal_id,device_id,command_id)` PK、`attempt_id,fingerprint,state,revision`；不含private/path/rawcode。原fingerprint包含参数/可信context政策模型预算和root/revision/fence，重试可换attempt/trace/短期signature与expiry但仍每次查当前authority并完整匹配本次command；重放返回原attempt/state，不重置cancelled tombstone；不同逻辑参数同ID conflict。cancel(expected_revision)为可信内部owner调用。

- success：真实Ed25519＋明确组件映射/authority＋获准临时根 → Admission(admitted)；不读取文件、不执行任务。
- denial：错误通道session/user或当前owner变化 → permission_denied/binding_mismatch；schema缺字段/非严格类型 → validation；缺authority/mapping/guardedCAS → capability_unavailable；取消 → cancelled；到点 → deadline_exceeded。
- repeat/conflict：16并发调用同cmd只有同一持久record，重新打开SQLite后仍原attempt；当前authority/原模型/参数/版本/lease/fence等变化拒绝，取消state不恢复。过期的锁等待guard回滚插入。

## 尚未解决的真实执行边界

两次查询+本机复核+本地CAS不构成跨服务原子授权。最终authority响应后flags/owner/key/root等仍可能改变；取消可能在CAS提交后到达。真实发送/打开/执行前仍需A设计server lease/fence/当前撤销检查与动作消费协调，本轮admission结果**不能缓存当执行许可**。本机路径检查与文件打开存在TOCTOU，未开放文件IO/executor，也不宣称该问题消除。

若需要真实异步key/root仓储，A须发相应port，不能以短期缓存或同步SQL堵事件循环接线。PersistentAdmissions的同步构造仅为受控初始化，运行时reserve在线程执行；生产构造/生命周期同样由组装根安排。临时SQLite不决定D01；D03/D06保持未决。

本轮不改MS-R2a的Ticket.document或RootSelection签字profile，不发布/重解释成公开配对协议。旧pair.complete、真实可信IPC、OS凭据实连及用户配对仍不可用。完整MS-R2继续等待。

## 验证与回退

真实Ed25519、新wrapper缺字段/extra/null/bool/时间验证、异步过期与撤销/上下文/版本变化、独立user/runner通道与组件登记关系、cancelled传播、blocking线程检查、真实SQLite锁等待、并发/重启/CAS/取消tombstone均有D用例。此前100项范围中的真实签字/跨进程单次ticket消费和本机路径回归保留；生产authority/mapping/IPC尚未实连。

A在集成SHA审阅和实跑组合回归后发布新版本；回退先禁用接线/保持flags关闭，revert本包，不以Git撤销真实凭据/外部效果。A决定与接线SHA/真实authority/IPC回执仍待填，不假定已批准。
