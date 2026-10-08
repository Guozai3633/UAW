# MS-R2d：控制签名阶段版与授权根装配契约

日期：2026-10-08；分支 dev/runner；固定基线 ms-i2g-start / `0bd8e2b8387a46e16435dc033956c2b69bb1a859`。
前两里程碑可审阅接口，下半包继续当前基线，不等待最终集成。未选择 D01/D03/D06，不开放 IPC/配对V2/文件动作/安装写入exec。

## 阶段版接口（里程碑1/2）

```python
ControlKeyBinding(device_id: str, key_id: str, credential_handle: str)
ControlCommandSigner(
    bindings: tuple[ControlKeyBinding, ...], *,
    directory: CurrentKeyDirectory, signer: ProtectedSigner | None,
    clock: Callable[[], datetime] | None = None,
)
await adapter.sign(draft: JsonObject, *, device_id: str) -> JsonObject  # RunnerCommand
await adapter.verify(command: JsonObject, *, device_id: str) -> None
```

实现已有 `RunnerCommandSigningPort`。绑定只由可信构造源固定，每设备唯一 key/handle，immutable mapping；不在 draft 添加选择 key/handle/owner 的字段。严格 schema 校验 RunnerCommandDraft，完整深拷贝，只增加 signature；不改 command正文/用户模型/期限/fence。
当前目录与 ProtectedSigner 必须同源，key_id/device/角色control/撤销均复核，control与device分离。sign 检查 expires_at/ctx.deadline，在 key/OS await 后及返回前重取时钟；取消直接传播，不把已在OS线程完成的读取视为执行授权。verify 不读取私钥，重新查询当前control key，真实验签并复核key；为了已接受恢复链，不以历史command期限拒绝 verify，它不是准入。
ProtectedSigner 改为 off-loop 当前key查询并提前复制 document，保持现有域/角色/私钥公钥匹配与当前key再查；没有OS/credential port无明文回退。签名 adapter本身不证明用户归属，只有可信服务装配才调用；A的 RunnerCommands 仍须独立登记/设备/Run/政策/闸门/lease/fence 全链检查。

```python
# 这些值来自独立可信控制服务登记，绝不来自模型/命令请求体。
store = WindowsCredentialStore(private_service_namespace)
protected = ProtectedSigner(current_key_directory, store)
adapter = ControlCommandSigner(
    (ControlKeyBinding(actual_device_id, registered_control_key_id, protected_handle),),
    directory=current_key_directory,
    signer=protected,
)
command = await adapter.sign(actual_registered_draft, device_id=actual_device_id)
await adapter.verify(command, device_id=actual_device_id)
# container.runner_commands.signer = adapter 由A在真实服务构造点注入。
```

缺device绑定/ProtectedSigner/credential backend为unavailable；当前key错误/撤销/签名或绑定错误拒绝；过期为deadline_exceeded。control绑定替换需要由A在可信构造/版本发布点更新，不能从任意签名选目录里的另一个control key。
OS随机命名空间仅测试；生产现有credential port无create-only CAS，provision_private仍须可信单owner随机handle，不能对既有用户handle执行覆盖/删除。

## 阶段实际回执

`uv sync --frozen`成功（按指令未选agent-engine extra，移除本工作区27个可选包，不修改锁）。
阶段命令：

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_control_signing.py tests/unit/runner/test_real_keys.py tests/integration/runner/test_windows_control_keys.py --basetemp tests/.artifacts/D/MS-R2d/tmp-stage -q --junitxml tests/.artifacts/D/MS-R2d/stage-junit.xml
```

实际 **27 passed，0 failure/error/skip，1.85s**。其中1项真实 `keyring.backends.Windows.WinVaultKeyring`，随机 namespace/handle证明原来不存在→ProtectedSigner生成→OS保存/读取→真实sign/verify→重建store/目录→再签→撤销→finally删除并证明不存在。`tests/.artifacts/D/MS-R2d/windows-control-receipt.json`只含backend/status/随机namespace和handle/cleaned，无私钥/凭据/签名内容；真实OS成功且cleaned=true。其他26项为实际密码学配合明确memory vault fixture，不替代OS回执。不访问已有用户凭据，没有用户项目文件动作。

阶段源码SHA与单独交接SHA在D handoff/Git记录，随后继续里程碑3/4。生产trusted channel、native确认和正式key登记生命周期仍待A。


## 最终授权根接口（里程碑3/4）

```python
PersistentRootGrants(path: Path)  # 显式本机开发SQLite；构造/IO在调用端off-loop
# implements RootRepository + internal RootGrantLookup.find
NativeRootSource(
    bindings: RootBindings, *, grants: RootGrantLookup | None,
    selections: LocalState | None, native_roots: LocalRoots | None,
    mapping: RunnerPrincipalMappingPort | None,
    directory: CurrentKeyDirectory | None = None,
    clock: Callable[[], datetime] | None = None,
)
await roots.current(device_id: str, workspace_ref: Ref,
    ctx: TrustedExecutionContext) -> JsonObject  # 严格 RunnerRootSnapshot
await roots.bind(selection: RootSelection, workspace_ref: Ref, *,
    device_id: str, authenticated_principal: Principal) -> None  # 可信native控制入口
RegisteredPrincipalMapping(devices: DeviceOwnerReader | None)
await mapping.owner(*, authenticated_principal: Principal, device_id: str) -> Principal
```

`RegisteredPrincipalMapping`适配已发布 `RunnerDevices.owner(actor,device_id)`，不读取command。NativeRootSource先/后分别调用独立映射并与完整ctx principal/session比较；ctx只作为可信请求范围和待比较声明，绝不生成owner。缺mapping/device/channel/选择记录/当前key目录无fallback。
RootSource以owner/device/完整固定workspace查找唯一持久grant；不接受模型root_handle/native_path/approved；grant含完整owner、目录dev/inode、read能力、原选择ticket/key/signature和真实确认期限。仅通过实际PersistentRootSelection.consume才能生成该组证据，旧无owner/proof/期限的记录被拒绝，永不填无限deadline。
PersistentRootSelection在消费CAS前同时检查独立当前device key；assembly显式传入同一directory，当前全局撤销拒绝时不消费本机approved票据。兼容旧构造仅以显式LocalState的当前目录验签，不把旧记录当作新的生产授权。
实际已消费root票据必须为consumed/revision2，确认hash与原挑战domain文档一致、有限expiry匹配；独立当前device key必须匹配public bytes/角色/撤销，原root-selection签名真实验签，NativeRoots路径及目录身份与grant一致，RootBindings复查真实路径/read/完整workspace与revision。映射/目录外部查询后重复源/key/grant/时钟检查。scope仅约束请求不能扩大原native read授权。
RootSnapshot只返回发布字段：owner/device/workspace/root_handle/binding_revision/allowed_actions/expires_at，不返回路径或private key。allowed_actions由真实read grant映射为file.read/file.list；这是根元数据，不是已执行文件动作或新准入。expires_at取ticket与真实确认期限最小值，终点闭合拒绝。
到期首次被根来源观察后，持久CAS撤销grant，clock rollback和重启不能恢复原授权。revocation CAS单调推进revision；重放不能覆盖根身份，缺/多个workspace binding拒绝，不自动挑一个或替换revoked root。重新授权/生命周期迁移需要A规定独立可信版本流程。

## 与已接受接口的装配例子

```python
# 当前目录、原选择库/native目录/grant库均来自本机可信后端，文件彼此独立。
# 启动加载IO off-loop；此处不批准新选择、不生成确认，不读取模型路径。
grants = await asyncio.to_thread(PersistentRootGrants, private_native_dir / "grants.sqlite")
selections = await asyncio.to_thread(LocalState, private_control_dir / "selections.sqlite")
native_roots = await asyncio.to_thread(LocalRoots, private_native_dir / "selected-roots.sqlite")
mapping = RegisteredPrincipalMapping(container.runner_devices)
parts = assemble_runner_adapters(
    device_id=actual_device_id,
    control_bindings=(ControlKeyBinding(actual_device_id, control_key_id, control_handle),),
    directory=current_key_directory,
    credentials=WindowsCredentialStore(private_service_namespace),
    grants=grants,
    admissions=actual_admission_repository,
    selections=selections,
    native_roots=native_roots,
    mapping=mapping,
    authority=container.runner_authority,
    receipt_commands=container.runner_receipt_commands,
    journal_path=private_native_dir / "terminal-receipts.sqlite",
)
# A在真实构造点注入，仍须gate/channel/Run/policy/model/lease/fence等全部来源。
container.runner_commands.signer = parts.control_signing
container.runner_commands.roots = parts.roots
root = await parts.roots.current(actual_device_id, actual_workspace_ref, trusted_ctx)
command = await parts.control_signing.sign(actual_registered_draft, device_id=actual_device_id)
# 仅真实通道已验证主体才能调用；admission不是执行。
admission = await parts.protocol.admit_async(
    json.dumps(command), authenticated_principal=verified_channel.principal,
)
# 真正收到签名终态后才可发布，不能由admission/expected result构造。
receipt_ref = await parts.journal.publish(
    actual_command_ref, received_receipt_json,
    authenticated_principal=verified_channel.principal,
)
receipt = await parts.journal.read(receipt_ref, authenticated_principal=verified_channel.principal)
assert receipt_ref.kind == "content"  # 保留ms-i2f2裁决，没有artifact透明别名
```

`assemble_runner_adapters`返回frozen `RunnerAdapters(control_signing,roots,bindings,protocol,journal)`，只做显式构造，不挂载HTTP/IPC/公共Tool/Runtime，不生成用户确认，不自动创建grant/journal文件或启用flags。没有authority、恢复Reader、OSstore或mapping时，各消费入口明确unavailable。
准备新的root绑定只允许可信native适配器将已批准、有真实possession proof/确认期限的RootSelection交给 `await parts.roots.bind(actual_selection, actual_workspace_ref, device_id=..., authenticated_principal=...)`。workspace pin必须来自实际工作区登记源。这里不实现chooser或将旧pair.complete/内部Ticket.document重解释为公开配对V2。

## 持久化、取消与边界

本机grant持久化是D的明确SQLite组件后端；只存具体RootGrant字段，没有公开Object扩展/迁移或D01决策。原选择control库、本机native目录、grants、journal分别配置，未向平台snapshot暴露路径。
SQLite begin immediate约束一次root_handle保存和revoke CAS；目录/映射/key/grant库并非共同事务，多次复查不等于跨服务原子执行。RootBindings同步旧入口兼容；protocol同步和异步admission都把当前时钟传入有限grant检查，async末次CAS前仍复查真实root/time。低级旧check_scope调用不传now的兼容行为不视为可生产的root source。
构造后root source的实际SQLite/stat/key IO在worker线程；取消及时传播，线程不能撤销已完成的选择consume/grant commit。consume后崩溃可能产生未写grant的孤儿消费，保持fail-closed、不重放票据；bind完成后调用者取消/源撤销可能保留实际grant事实，但下一次current仍须当前独立权限/证据。未声称OS句柄TOCTOU隔离、断电每指令边界或跨服务原子撤销。
OS证明限本机当前Windows账户的真实WinVault后端；没有认证native确认/IPC或生产channel。测试受控native确认/owner记录明确标注fixture，即使crypto/持久/路径是真的，也不称为真实用户配对完成。

A接线仍需：真实control/device key登记与可信绑定生命周期、真正channel/owner映射、native用户选择/possession/确认回执与期限、实际固定workspace来源、当前role/resource/consent gate、正式目录ACL/保留/备份/数据库策略和可信IPC。RootSource完成读授权元数据，D03执行模式仍未选；没有文件executor、安装/写入/exec、配对V2或Runner→Tool applied推断。


## 最终实际回执

阶段源码 `92ddf118cf3005bfe32eea630ce950c6325bd76d`，阶段handoff `1287a053da9e3963703091ccbfc9ff0f032c8dc1`，保留为独立交付点。后半包源码/最终handoff SHA见D最终交接与Git历史。
最终命令为D全部单元/本机集成＋公共DTO/真实签名原回归，basetemp限定 `tests/.artifacts/D/MS-R2d/tmp-final2`：**326 passed，0 failure/error/skip，45.05s**。本包新增76项：22项control signing、1项真实Windows OS key、52项native root来源/装配/新进程，以及1项真实签名异步admission期间根期限失效。原250项保留。
真实WinVault用例passed/cleaned=true，无跳过或明文fallback；52项根来源用真实SQLite/临时目录/dev-inode/Ed25519消费，native确认与owner/channel来源仍是明确fixture。8线程revoke CAS只一胜者；新的Python进程读同一真实grant/选择库恢复opaque snapshot；Windows临时junction跨界拒绝并finally移除link，不触碰target。
Ruff全D目录通过、格式31文件通过、Mypy15源码文件通过、git diff --check通过；schema/shared/锁/composition与ms-i2g-start字节一致。本包不需要平台SQL，因此未启动Session D PG，也不把本机SQLite验证称为真实PostgreSQL/真实平台channel链验收。
完整构造例子与后续缺口如上；回执在本session忽略目录，不改公共环境/JUnit生成文件。
