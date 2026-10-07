# D-R2a-001：异步 authority、可信 IPC/挑战证明和持久 DTO 接线

日期：2026-10-07；D / MS-R2a；实际基线 `ms-i2a` = `ac9bf621e3caebf060300b3a628b77dee36f7ab0`。状态：提案待 A 决定、发布，D 未私改公共 schema/依赖/迁移，不默认进入完整 MS-R2。

## 当前交付与边界

- SignaturePort 已消费 `uaw.shared.runner_signatures`，每次从可信注入 CurrentKeyDirectory 读取公钥与角色/撤销。公钥不从命令自报字段获取，command 用 control，receipt/pairing-proof/root-selection 用 device。
- `LocalState` 是显式选择临时路径的开发 SQLite 适配器：真实事务/CAS、重启、跨进程竞争得到验证。内部 SQL 字段/Ticket 是组件记录，**不是公共 wire DTO，不登记成控制面 RecordTransaction schema，不决定 D01**。
- `PairingVerifier` 仅内部可信适配器调用，要求真实设备挑战签名 + 独立 NativeConfirmationPort；缺本机端口返回不可用。测试 NativeFixture 只模拟确认端口；它不证明 OS 用户或 IPC 已认证。没有对外配对 route、设备注册、会话凭据发行或 executor。
- Ticket.document() 是本包内部签字测试 profile。将它用于网络或产品 RootSelection token 前，A 必须发布下面的公共签字文档/DTO；不能把私有字段塞入旧 pair.complete。根选择 token 仍占已有 RootSelection.selection_token 字段，其被签状态含准确 display_name/expires_at/root_handle、主体/设备/key/nonce/challenge/read；私钥与明文路径均不在签字文档。

## 1. 异步 authority（A 的 MS-I2 汇合依赖）

建议 A 公布供 D 消费的 port，签名如下（不是本包已接线能力）：

```python
class AsyncRunnerAuthorityPort(Protocol):
    async def current(self, command: RunnerCommand) -> CommandAuthority: ...
```

参数沿用已验证完整命令，但认证来源必须是受控传输与已登记命令，不是模型 body；返回的 CommandAuthority 从 Run/身份/版本仓储独立重建。最小结果仍使用现有 D 的内部类型：`context, device_id, root_handle, workspace_ref, binding_revision, fencing_token, lease_expires_at, request_ref, request_parameters, policy_ref, required_scope_capability, allowed_actions, feature_enabled, connected, cancelled`，均必填，无宽松默认。

- 每次调用/重试/实际发送前 await 当前认证 principal/session、原 context 的模型/预算/agent/node/Run/scope、固定参数与 request_ref/version、父政策交集和固定/当前 flags、当前租约/fence、设备/key/root 撤销及绑定版本。scope 是选择器，不能自证授权。
- 若已发生 dispatch 再失联，原账本保留原 attempt/unknown；不能将重新准入当成重发写动作。取消所有者仍是 Run，审批不会扩大真实权限。
- 同步 LocalState/key 目录仅用于本机临时组件；不得在 async SQL 里 `asyncio.run`、阻塞事件循环或拿快照替代当前状态。实际 control-plane directory 应另提供 async lookup，D 在 A 发布后接异步协议入口；现有同步 RunnerProtocol 不假装完成这项接线。
- A 修改/分配：`shared/ports.py`（若需要统一导出）、Run/Workspace authority adapter、composition/application/routes；D 下一次在允许 Runner 目录消费正式 port。旧同步调用者保留组件接口，不默默改变为 coroutine。
- 错误：缺 reader/current owner → dependency_unavailable；取消 → cancelled；租约到期 → deadline_exceeded；fence/request/policy/root修订变化 → revision_conflict；权限/flag/撤销 → permission_denied/feature_disabled。没有默认 allow。

## 2. 可信 IPC 与挑战证明

已有 D 的 NativeConfirmationPort 是独立可信入口，返回结构化确认（ticket_id、principal_id、device_id、document_hash、expires_at；root 才带本机 path），并非 approved=True。真实 adapter 必须做：OS/account 用户/会话认证、local peer 来源验证、防重放、展示完整设备公钥摘要/请求/能力、明确确认、hash 与事务绑定、短期有效期、当前撤销复核。RootSelection 的 native_path 只由实际本机选择返回，网页/模型不能提供。

候选设备持钥证明取自固定 pending ticket 的 candidate 公钥，不作为已登记身份；仅 proof 验签成功仍不能批准。签字 domain=pairing-proof，覆盖 nonce、challenge、ticket/principal/device/key、公钥摘要、期限及种类/根能力。一次码是独立 256-bit 随机秘密，普通记录只保存 salted digest；没有默认 TTL，注入明确截止时间。持有一次码和公钥本身均不等于用户确认。

旧 `RunnerPairCompleteRequest{pairing_id,verification_code,device_public_key}` 缺 proof，D 的 legacy completion 明确返回 `capability_unavailable: runner.versioned_pairing_proof_DTO`。不推断之前已通过挑战；没有可信 IPC 返回 `runner.trusted_native_confirmation` 不可用。

建议 A 发布新的命名 DTO/操作版本（候选 pairing v0.2，RunnerCommand 0.1 不因此变动）：

- `RunnerPairChallengeV2`：`pairing_id:ID, revision:Revision, device_nonce:NonEmptyText, challenge:NonEmptyText, device_id:ID, key_id:ID(需 KEY_ID 限制), candidate_public_key:NonEmptyText(32-byte无填充base64url), public_key_hash:Hash, expires_at:Timestamp` 必填；已认证 principal 从可信端口注入，签字文档必须包含该 principal。
- `RunnerPairProofDocumentV2`：`pairing_id, principal_id, device_id, key_id, public_key_hash, device_nonce, challenge, expires_at, kind=pair` 全必填，额外字段拒绝；device签名以 pairing-proof 域对这些准确字段签字。
- `RunnerPairCompleteV2`：`pairing_id:ID, expected_revision:Revision, verification_code:NonEmptyText, proof_signature:NonEmptyText` 必填；key 从原 challenge 解析，不能新传公钥替换；native confirmation 通过可信 port 取得，HTTP body 不接受 approved/native_path/Principal。
- `RunnerRootProofDocumentV2`：相同身份/nonce/challenge字段 + `root_handle:ID, display_name:NonEmptyText, capabilities:[read], expires_at:Timestamp` 必填；pairing-proof 验证持钥，root-selection 签字发行一次 token。签字 document 包含所有公开 RootSelection 字段（不含 token 自身），准确字符串不归一化；根路径只保存在本机目录。

成功示例（占位签名不表示真实证明）：`RunnerPairCompleteV2{pairing_id:'pair-1',expected_revision:0,verification_code:'<secret via trusted UI>',proof_signature:'uaw-ed25519-v1:device-1:<signature>'}` + 已认证本机确认 → 持久 approved revision=1。缺 IPC/签名、错主体/nonce/期限拒绝；消费后同 revision 再消费 → conflict。当前本包只验证内部 profile，A 发新版本前不启用这个网络 DTO。

消费方：可信本机 UI/IPC、control pairing服务、Runner签字者、Workspace bind。旧 v0.1 客户端继续明确不可用或走已验证的独立可信 port，不接受新增字段或自动降级。A 修改 contracts源/生成物/对象文档与路由版本，并提供例子、错误与兼容回执；D 不运行共享生成器。

## 3. 持久 DTO / SQL 接线

当前内部 tickets 字段：`ticket_id, kind, principal_id, device_id, key_id, public_bytes, nonce, challenge, expires_at, state, revision, salt, code_hash, root_handle, display_name, confirmation_hash, confirmation_expires_at`；目录 key 字段为 `key_id, device_id, public_bytes, role, revoked, revision`。没有 raw一次码、私钥、credential handle或native_path进入控制记录。native目录单独保存 ticket/root句柄、path和文件身份。

建议 A 发布 `RunnerPairingStateV2` / `RunnerRootSelectionStateV2`（内部持久 DTO，禁止模型/API直接写），对应上面字段但公钥采用严格编码；pending 可以省略confirmation字段，approved/consumed必须携真实确认摘要与期限；state枚举 pending/approved/consumed/expired/revoked，revision非负整数；expires与确认expires任一到点就终态失效，无 TTL 默认。根状态的 capabilities 仅 read；安装/write/exec等待 D03及独立真实授权。需要 A 确认聚合/命名空间、public schema、迁移、CAS/请求 receipts映射，再由D写真实SQL适配器。

- issuance 幂等 key `(principal,device,request_id)`；同输入返回原 ticket/nonce/challenge，不再回传 raw一次码、不换挑战、不延长期限；不同参数/公钥/种类/根/期限 conflict。
- 原子事务按 state+expected_revision 消费，跨连接/进程只有一个获准消费；失败重试保持原态，终态不能恢复。Pair consume 在本包仅消费状态，**不注册设备、不签发会话凭据**。最终注册与消费必须同一所有者持久原子步骤或可恢复的幂等 journal，不能先消费后伪装配对完成。
- Root native记录先写后CAS，败者只可能留下无授权孤儿；consume后崩溃失去可用性也不允许再次消费。A需设计原子绑定/journal恢复，不能宣称跨目录事务已解决。
- key_id 永不复用；role/device/public key 不原地改，轮换新key_id后撤旧；当前撤销还原子撤销未消费tickets。可信目录写者必须绑定认证所有者和本机目录ACL，不能由模型/HTTP自报key建立信任。开发SQLite路径不是部署ACL保证。

## 4. 私钥与凭据

ProtectedSigner 从 CredentialStorePort 获取 SecretStr，验私钥与当前公钥一致、检查角色/撤销，async取凭据后再次查当前key。生产只能由 A 明确注入现有 WindowsCredentialStore/批准的保护后端，缺失无明文 fallback。测试 CredentialFixture 为内存替身，仅用于验证调用边界/不落普通记录；**未运行OS keyring实连**，遵守只用临时测试目录。

provision_private 拒绝已有 handle，不返回private，只返回public；但现有 CredentialStorePort 没有跨进程 create-only CAS，真实 provision 必须受单一可信所有者约束。A如需并发发行应发布 `create_once(handle,SecretStr)`/登记事务port；不能把本包预读检查称为跨进程凭据原子性。privates不落SQLite、日志、普通DTO、上下文、Git；密钥材料只在加密原语与保护后端的必要内存中出现，Python内存不宣称已安全擦除。

## 验证和回退

真实 Ed25519 adapter、role/domain/错误device/篡改、当前key撤销重启、一次码digest不泄露、持久批准/消费/CAS/期限/撤销、RootSelection真实签字、16并发连接和6实际Python进程一人消费，均在 D 独立临时根测试。确认/凭据port为显式TEST adapter，不声称真实IPC/用户配对。

A需要在集成SHA补实际可信来源、公钥持有、OS保护后端、持久DTO/真实SQL、重启配对注册/根绑定journal、异步当前authority、使用时文件句柄路径与撤销验证；仍保持flags关闭，无executor就不可用。回退先移除新增接线并保持禁用，再revert相应提交；真实凭据与外部效果由其状态所有者撤销。D01/D03/D06保持待定。

## A 决定/发布

待填写：采用/调整/暂缓，公共实际提交SHA、schema生成/迁移/锁回执、需要同步的session与新固定基线。D不假定本提案被批准。
