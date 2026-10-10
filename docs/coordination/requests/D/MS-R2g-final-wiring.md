# MS-R2g：Windows本机确认与只读授权最终交接

日期2026-10-10。工作区E:/UAW/.worktrees/runner，dev/runner；开工干净，fetch origin --tags / merge --ff-only ms-i2j-start 成功，HEAD与tag commit精确等值 **abb4590f2bfe53c601e0f6a4a3b65447ba4ec502**；uv sync --frozen检查64包。失败未reset/rebase，原提交/已接受包完整保留。

源码 M1 **42ad508d3d98e703a51bff3d522bf2bbecdf169c**、M2 **88bb0f33a86560a5bce89421e84f1f75cb7d3a09**；阶段handoff **af19a01c49c22d274f10cfd969dca09491b605a9**；最终源码 **d0ea31b7a05885806e9a72b9afff283ddc703122**。最终handoff与源码分开提交。

## 交付文件与固定接口

- 新增 apps/local_runner/uaw_runner/{native_dialog,native_confirmation,native_authorization}.py。
- 修改 apps/local_runner/uaw_runner/{pairing,state}.py：真实选择identity/当前key/Ticket复核、IO异步worker和checked批准CAS，旧调用兼容。
- 新增 tests/unit/runner/test_native_confirmation.py、tests/integration/runner/{test_native_dialog_windows,test_native_authorization,native_manual}.py。
- 修改 tests/integration/runner/{test_native_root_source,test_read_executor}.py：支持延后确认/真实已provision OS keys与实际clock测试组装，原fixture默认兼容，原断言保持。
- 文档 D stage-native/final-wiring/human-native-guide/bootstrap-inputs及D handoff。workspace原四文件无需修改。公共契约/schema/锁/HTTP/认证/composition/其他session路径未改，无新依赖。

M1/M2固定签名见 [阶段接口](MS-R2g-stage-native.md)。最终构造如下，root操作local_roots必须显式注入，否则不可用：

```python
RegisteredNativeChallenges(*, state: LocalState, registry: ConnectionRegistry,
    channel_ref: Ref, device_id: str, mapping: RunnerPrincipalMappingPort | None,
    clock: Callable[[], datetime])
WindowsNativeConfirmation(*, source: NativeChallengeSourcePort | None,
    directory: CurrentKeyDirectory, clock: Callable[[], datetime],
    timeout_seconds=60, local_roots: LocalRoots | None = None)
async confirm(*, ticket_id, principal_id, device_id, document_hash) -> NativeConfirmation
NativeReadAuthorization(*, native: WindowsNativeConfirmation,
    challenges: RegisteredNativeChallenges, verifier: PairingVerifier,
    signer: ProtectedSigner, device_key: DeviceSigningBinding, roots: NativeRootSource)
async select(ticket_id, *, expected_revision, code, proof_signature) -> RootSelection
async bind(selection: RootSelection, workspace_ref: Ref) -> None
async revoke(root_handle, *, expected_revision) -> None
```

NativeDecisionJournal是与LocalRoots同本机数据库的原确认来源证据（完整owner/actor/session、原Ticket文档、origin channel Ref），每次bind仍读当前关系/Ticket/签名/期限/Root与key。重启查原证据，same user_id不同auth session不能复用。不同确认内容冲突，不覆盖；不缓存执行许可。原RootSelectionPort使用PersistentRootSelection，输出仅opaque根handle/准确期限/旧内部selection signature/display_name，固定workspace Ref由可信入口提供。绝对路径、目录identity与grant仅本机LocalRoots/持久grants；控制/IPC命令帧与publicDTO不新增path/approved/owner字段。

## A 真实装配例子

```python
# A必须先有受保护的真实账号/设备/key/challenge登记和真实当前sources。
# 并非任意HTTP path/模型请求或Windows SID就能产生此关系。
channel_ref = await live_registry.add(actual_authenticated_pipe_session)
challenges = RegisteredNativeChallenges(state=local_ticket_state,
    registry=live_registry, channel_ref=channel_ref, device_id=registered_device_id,
    mapping=actual_mapping, clock=actual_clock)
native = WindowsNativeConfirmation(source=challenges, directory=current_keys,
    clock=actual_clock, timeout_seconds=60, local_roots=local_roots)
verifier = PairingVerifier(local_ticket_state, native=native,
    clock=actual_clock, roots=local_roots)
# actual_root_source使用同一local_ticket_state/local_roots/current_keys/mapping，
# RootBindings使用原PersistentRootSelection及持久grant repository。
lifecycle = NativeReadAuthorization(native=native, challenges=challenges,
    verifier=verifier, signer=ProtectedSigner(current_keys, os_credentials),
    device_key=registered_device_key_binding, roots=actual_root_source)
selection = await lifecycle.select(registered_ticket_id,
    expected_revision=registered_ticket_revision,
    code=original_one_time_code, proof_signature=actual_original_challenge_proof)
await lifecycle.bind(selection, exact_registered_workspace_ref)
# 后续已有ReadOnlyPipeEndpoint/ReadOnlyRunner：same registry和新连接Ref、
# actual_root_source、current authority/mapping、签名/admission/once read journal、
# 原登记command Reader和ReceiptJournal/device signer，构造见MS-R2f-final-wiring。
# 撤销必须由可信native/control入口调用，按当前完整owner与grant version复核：
await lifecycle.revoke(selection.root_handle, expected_revision=actual_grant_revision)
```

成功：本人真实选目录+最终确认→原proof/code/document_hash/current角色key/期限复核→持久approved→原签名RootSelection→一次bind consumed→当前root/read链。
拒绝：无桌面/无source/当前映射或key缺失、错误code/proof/owner/device/doc_hash、UI取消/超时、源变化、根/祖先reparse或目录替换；无批准/新读取。重复：同Ticket再次select或同selection再次bind拒绝，复用签名结果恢复必须有当前数据权限，unknown不重发。

A需提供生产身份/当前设备关系/受保护挑战注册及首次配对bootstrap；缺口与最小消费方影响见 [输入提案](MS-R2g-bootstrap-inputs.md)。旧pair.complete不含内联proof，继续不可用；没有把内部Ticket.document变成公开配对协议。Public新DTO/HTTP/认证/控制端/注册/锁仅A发布；D没有自行新增。

## 原生窗口与授权边界

Windows原生SHBrowseForFolder旧式tree（无路径输入/新建目录/拖放UI）由本人选择本机目录，然后独立MessageBox完整显示账号、设备、只读范围、有效期、挑战摘要与选定目录；最终本人再明确“确定”，默认按钮“取消”。取消、关闭、超时、锁屏/无交互Default桌面明确返回失败/不可用。API依据：[微软目录选择](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shbrowseforfolderw)。不自动模拟批准；只有此交互窗口可见，IPC helper隐藏。

专用worker线程初始化STA COM；event loop不阻塞。桌面每20ms检查，超时/取消仅WM_CLOSE本线程窗口；释放PIDL/COM/desktop和monitor。Native await最长60秒可0..120内配置，且受独立Ticket/当前connection期限取最小值；明确显示真实该期限，不延长原challenge。完整source每100ms复查且UI结束后复查，再固定本机identity并复查源；成功时让监视器的在途检查结束，避免cancel错误关闭正常IPC。取消原CancelledError传播；native_cancelled/category=cancelled、native_timeout、依赖缺失capability_unavailable。

目录选择捕获st_dev/st_ino，在最终本人点击后再核同一identity，本机LocalRoots.record按expected_identity写不可覆盖记录；根/祖先reparse/link拒绝，UI与record之间替换也拒绝。PairingVerifier交互后重新读Ticket和current device key，LocalRoots记录不得漂移；批准事务前/锁内/提交前重新时钟与取消检查，等待后的过期/取消回滚。根授权仅read，没有安装/写/exec批准；旧原文件句柄读路径仍复查actual Windows identity/范围/期限。

确认来源证据与实际Run权威独立；持续执行仍完整复核签名、当前owner/key/root/channel、request/parameters/policy/workspace版本、flags、Run取消、lease/fence及一次使用。撤销即阻止新的根读取；重连新channel Ref，不沿用旧连接或重发unknown。恢复原真实已签名receipt走当前数据权限，而不伪造new admission或零费用。

## 验证与真实来源分界

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py -q --basetemp tests/.artifacts/D/MS-R2g/tmp-full --junitxml tests/.artifacts/D/MS-R2g/full.xml
.venv/Scripts/python.exe -m ruff check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
git diff --check
.venv/Scripts/python.exe -m tests.integration.runner.native_manual
# 默认只输出pending；没有执行 --run-human 或自动批准。
```

**550 passed /201.94秒，0 failure/error/skip**，JUnit201.606秒；基线505完整重跑＋45不同新增（unit native22、integration lifecycle20、actual native UI3），不累加重试。Ruff通过、格式58文件、Mypy29源码、diff通过。回执ignored tests/.artifacts/D/MS-R2g/full.xml/full.log、checks.json/public-hashes.json、ruff/format/mypy.log；真人human-pending.json明确pending。

实际：Windows Default桌面/真实原生选择和确认窗口自动关闭（仅取消/超时，不点击批准）；真实两进程本机命名管道、实际OS token/PID/nonce/current key签名和random WindowsCredentialStore私钥；原challenge/once code/proof、实际SQLite approved/consumed/decision/revoke与重开；临时根identity/junction、实际UTF-8只读/签名journal及新连接恢复。64份windows-ipc清理记录全部cleaned=true，原OS read/control签名回归保留；finally清理自有随机凭据/管道/子进程/OS句柄。未使用PG，不改55432..55435数据库或用户项目。

受控依赖：UAW账号/owner/pairing注册、当前Run authority/feature/lease、fixture挑战发出、currency及肯定UI选择由独立测试源明确提供；它们不从command/body生成，也不登记为产品提供方。Native自动测试不称“真人确认”。原生自动取消实际运行，肯定双进程只读链使用typed UI double；**本人亲自选择/确认的完整链 pending**。可复现手动入口见 [真人临时根指南](MS-R2g-human-native-guide.md)，其 --run-human尚未运行。

专项：M1修复后21 passed /3.02秒；M2首轮82 passed /23.07秒，checked CAS后30 passed /13.58秒；M3/M4首轮39 passed /36.17秒，decision持久绑定后38 passed /37.84秒；source monitor修复22 passed /7.59秒，unit身份fixture修复21 passed /1.21秒；最后全550覆盖新增监视竞争回归。用通过不同节点计数，不把这些批次叠加。

失败历史完整保留：m1.xml 3失败/18通过（BrowseInfo wchar buffer指针类型、Principal fixture缺auth_session_id）；native-final.xml 7失败/34通过（6项新local_roots依赖未注入unit fixture；1项真实成功确认竞争——取消监视source check使IPC关闭，已改为在途检查正常结束）；native-unit-final.xml 1通过/20setup errors（LocalRoots导入此前被unused清理，fixture接线后未恢复）。均已修正，native-unit-fixed.xml、monitor.xml及最终全550通过；新逻辑没有删签名/取消/授权断言。Ruff的格式/导入/同步子进程提示已修复。当前自动检查无未通过项，人工及生产输入门槛仍pending。

## 剩余门槛

A真实认证/OIDC及受保护账号/挑战注册、首次配对bootstrap、控制端/HTTP/composition与C文件Tool业务核验仍需实际接线；D当前缺真实这些来源时拒绝。开发原生Default桌面不是安全桌面或抗同登录恶意进程注入的正式部署保证；未决定D01/D03/D06，不扩配对V2/schema，不开放flags/写入安装exec。组件journal与外部authority没有跨服务原子事务；晚取消/断线可能留下真实已确认/签名记录，仅按当前数据权限恢复，不能宣布产品任务完成。

四个连续里程碑在组件范围交付完成，真人验收单独pending。最终源码与handoff分开提交、干净交付，本包后停止；完整MS-R2/产品授权和下一包等待A实际接受/派发。
