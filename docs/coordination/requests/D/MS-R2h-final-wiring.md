# MS-R2h 最终组件接线与实际回执

2026-10-10，E:/UAW/.worktrees/runner，dev/runner。正式 DISPATCH/远程tag/开工HEAD精确 ms-i2k-start / b7b79b150470a80f37b28fd52a2177f6de5b3124；干净fetch/ff-only/原MS-R2g祖先核对/uv sync --frozen 64包成功。未reset/rebase，原已接受提交和失败/清理记录保留。

M1源码97da1f39dac82b95c2c9e9b09d05b557209950ea，撤销CAS夹具修正41ab8da894d9d2983008133a4b822e49d00d20bb；M2源码105dcbf1ca3828cd49988d6a60aabf6daab6f9c1；阶段handoff d0d45dc13a5029b87bb448686bc32b33a8465abd；最终源码ba798ad70b1e62f21fe9f33b4d1252bdac2a653a。本最终接线与handoff独立提交。

组件交付既有ports的当前交集消费、隐藏helper生命周期、一次根选择/绑定/撤销、实际只读/新连接/原journal恢复。**A生产首次认证/设备/挑战实现尚未发布，本人实际点击pending**。基线及最终只读fetch均只提供MS-I2k-input-contracts.md原ports；不消费其他session未交接源码，不自建生产enrollment或pair.complete v2。

## 文件和固定内部接口

新增Runner bootstrap.py、runtime.py、helper_process.py、helper_host.py；新增D integration test_bootstrap.py、helper_fixture.py、test_helper_runtime.py、helper_manual.py。文档为D bootstrap输入提案、两阶段签名、本人指南、本接线与handoff。原workspace四文件无需改，原native/pairing/root/read/admission/journal源码保持基线。没有schema/shared/锁/composition/API/其他worktree修改、新依赖或PG操作。

```python
BootstrapConsumer(*, registration: PeerRegistrationPort | None,
    challenges: NativeChallengeSourcePort | None,
    mapping: RunnerPrincipalMappingPort | None, directory: CurrentKeyDirectory,
    signer: ProtectedSigner, device_key: DeviceSigningBinding)
await bootstrap.local(actual_identity)  # 原 RegisteredPeer
await bootstrap.connected(actual_session)
BootstrapNativeChallenges(*, bootstrap, state, registry, channel_ref,
    device_id, mapping, clock).current(original_ticket_id)  # 原 NativeChallenge

ReadOnlyHelper(*, bootstrap, protocol: RunnerProtocol,
    commands: ReceiptCommandReaderPort | None, journal: ReceiptJournal,
    executions: ReadExecutionJournal | None, roots: NativeRootSource,
    registry: ConnectionRegistry, currency: str)
await helper.start()          # HelperAddress(name, actual OsIdentity)
await helper.accept()         # 新content固定channel Ref，互验nonce/current角色签名
lifecycle = await helper.authorization()  # 原 NativeReadAuthorization
await helper.serve_once()     # 实际签名receipt固定Ref，原command/recover wire
await helper.disconnect()     # 释放session/listener/registry，可start新连接
await helper.close()          # 永久关闭该实例，幂等

HelperApplication(helper, on_connected=None)
HelperAssemblyPort.create(actual_identity) -> HelperApplication  # async
owned = await HelperProcess.prepare(python=installed_python,
    assembly_module=trusted_installed_factory, environment=trusted_environment)
ready = await owned.start()
await owned.event()           # identity/ready/connected/receipt/failure/closed
await owned.close()           # 并发调用共同等待实际同一清理
```

固定启动 `python -m uaw_runner.helper_host`；assembly_module是安装时可信代码配置，不可取自命令/网页/模型body。没有shell/per-command任意程序参数。CREATE_NO_WINDOW，实际OS API再核对子进程PID/创建时间/SID/登录实例与stdout一致；只有native授权UI可见。stdin仅start/stop管理，不授予账号/path/approved。stdout≤4096字节公共生命周期metadata，不输出账号、code/proof、私钥、根路径或文件正文。

当前Windows selector环境由Popen后台线程管理，无asyncio.run桥接现有loop，独立helper main初始化自身loop。OS创建/IO/close在线程；取消监听创建排空并释放晚完成句柄。close优先stop，5秒未退出仅kill自有子进程；并发close共同等待清理，重复start拒绝。一个连接最多服务一个有界read/recover响应，然后断开并重新listen，新连接新Ref。没有新增IPC native/root wire；本人流程在可信本机callback执行。

## A固定装配与真实来源

以下actual变量必须由A真实受保护服务提供；缺源保持不可用，不能把tests工厂挂产品入口：

```python
protected = ProtectedSigner(current_keys, os_credential_store)
bootstrap = BootstrapConsumer(registration=actual_A_registration,
    challenges=actual_A_challenges, mapping=actual_A_owner_mapping,
    directory=current_keys, signer=protected, device_key=actual_device_binding)
protocol = RunnerProtocol(device_id=actual_device_binding.device_id,
    bindings=native_root_source.bindings, admissions=persistent_admissions,
    signatures=Ed25519SignatureAdapter(current_keys),
    async_authority=actual_current_run_authority,
    principal_mapping=actual_A_owner_mapping)
journal = ReceiptJournal(receipt_path, protocol=protocol, reader=registered_command_reader)
helper = ReadOnlyHelper(bootstrap=bootstrap, protocol=protocol,
    commands=registered_command_reader, journal=journal,
    executions=ReadExecutionJournal(read_attempt_path), roots=native_root_source,
    registry=ConnectionRegistry(), currency=actual_billing_currency)
```

native_root_source使用同bindings/mapping/directory；原一次Ticket已经在本机。currency不猜零费用，持久paths由安装方显式选择。A owning Reader可接既有Container.runner_receipt_commands，当前命令/owner/data权限每次复查。same-object检查绑定CurrentKeyDirectory/ProtectedSigner/owner mapping/RootBindings/protocol/Reader/journal；assembly创建Runner再次绑定当前registry/channel_ref。A负责控制端/注册权威/HTTP/composition，D不改这些文件。

A首次来源责任：当前完整Web会话/独立账号设备关系，实际OS实例，双方当前role key Ref/摘要/撤销、原pairing Ref/短期期限，双方真实持有证明，以及原Ticket/code/proof受保护本机交付。D不从SID/PID/public_key/网页Principal/path/approved登记账号，不自行issue/mirror生产Ticket。最小字段、状态同步与消费方影响见 [bootstrap输入提案](MS-R2h-bootstrap-inputs.md)。若HTTP需新DTO，由A统一版本/生成/发布后D消费；内部Ticket.document不重解释为公开配对协议。

## 成功、拒绝、重复和恢复

A本机adapter已绑定当前connection时可调用：

```python
lifecycle = await helper.authorization()
selection = await lifecycle.select(original_ticket_id, expected_revision=original_revision,
    code=original_one_time_code, proof_signature=original_device_possession_proof)
# Windows真实目录树和完整只读账号/设备/期限/挑战/目录确认，本人决定；默认取消。
await lifecycle.bind(selection, exact_workspace_ref)
# A控制端沿原IPC提交已登记command_ref，不传授权path/approved。
await lifecycle.revoke(selection.root_handle, expected_revision=actual_grant_revision)
```

无path/owner/approved构造参数，绝对目录仅本机。D取本机原Ticket与实际活ConnectionRegistry，和A NativeChallenge完整fingerprint交集：document/revision/state、完整owner/actor/session、OS创建时间、current channel/device/key/期限。角色key、私钥持有和账号映射在关键await后再查；原native签名域/document_hash/current key/取消/时钟复查，持久Ticket/RootSelection CAS一次消费保持。

- 成功：可信源＋本人确定→原selection/once bind→已登记签名file.read→actual Windows文件/根句柄身份/范围→当前authority/owner/channel/key/root/request/parameters/policy/workspace/flags/Run cancel/lease/fence/期限重查→一次admission/read claim→实际终态Ed25519签名content journal。
- 拒绝：registration/challenges/mapping/credentials/authority/Reader/原根/read journal缺失unavailable，启动前不创建listener；错账号/session/OS创建时间/key/角色/hash/Ticket/challenge/通道拒绝；取消原CancelledError传播，await后再查期限。固定workspace/command digest或坏签名拒绝；撤销阻止新读。
- 重复与恢复：原Ticket重select或selection重bind拒绝，revoke按revision CAS。断连旧Ref无许可，重连新Ref；已有签名终态可恢复同content Ref/原Usage。unknown recover明确不可用，不重发command/新准入/新打开。删除文件、取消后新进程恢复仍复查当前数据权限，不缓存执行许可。

A须让本人确认完成后再提交read，并持有准确原command pin。HelperAddress/生命周期metadata不是授权回执。错误不推导not_applied/零费用；Runner ok不自动Tool applied。

## 实际验证和受控依赖

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py -q --basetemp tests/.artifacts/D/MS-R2h/tmp-full --junitxml tests/.artifacts/D/MS-R2h/full.xml
.venv/Scripts/python.exe -m ruff check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
git diff --check
.venv/Scripts/python.exe -m tests.integration.runner.helper_manual
# 仅默认pending，--run-human未执行。
```

**591 passed /280.39秒，0 failure/error/skip**，JUnit280.015秒。原550完整重跑＋新增41不同节点：bootstrap22、helper19，不累加专项/重试。Ruff通过、格式66文件、Mypy33源码、diff通过。ignored tests/.artifacts/D/MS-R2h/full.xml/full.log、checks.json、public-hashes.json、ruff/format/mypy.log、manual-default.log/human-pending.json；7个公共基线文件字节一致。

真实Windows随机CredentialStore/current device/control签名；隐藏device进程＋控制端OS/创建时间/DACL/nonce/角色互签，native自动timeout拒绝；实际SQLite一次root bind/replay/revoke、新连接新进程/双helper并发journal/固定Ref恢复及UTF-8原换行。当前logout/owner/key/OS instance/workspace版本/坏签名拒绝，取消/并发close/pending accept清理。**105份随机IPC OS凭据清理回执全cleaned=true**，自有helper/管道/句柄/凭据finally回收。原admission/journal/范围/原生自动取消与OS签名回归保留；没有访问用户项目或其他session/PG资源。

A enrollment/Ticket发出/code-proof交付、owner/pairing/Run authority/feature/lease均是独立明确tests ports，肯定UI是typed double，只在临时根使用。它们不算A生产服务或真人确认，通信成功不冒充配对。真实原生自动取消可以自动验证，真人确定只能本人点击。[手动指南](MS-R2h-human-helper-guide.md) 与默认pending入口已备，--run-human没有运行。

阶段：M1最终22/32.09秒；M2最终8/17.16秒；M3 helper14/39.97秒；M4 helper19/47.41秒；最终全591采用最新不同节点。失败保留：m1.xml和m1-fixed.xml各21通过/1 revoke_key参数错误(device_id/expected_revision)，修正41ab8da；早期mypy单文件缺源码路径及沙箱base Python路径错误，完整原类型命令通过，未放松strict。m2.xml8失败(selector不支持asyncio subprocess transport)；m2-2.xml4失败/4通过(python -m dataclass双模块身份、撤销Ticket应revoked)；m2-3.xml1失败/7通过(LocalRoots夹具旧方法，diagnostic/read-diagnostic保留)，改原current和正规模块main后m2-4/m2-final全部通过。manual默认首次缺Runner导入路径及Ruff导入/有界poll提示修正后通过。没有删除安全断言、隐藏失败或累加失败重试。

最终文档首轮写入/提交未执行：自动审批服务额度耗尽，非安全判定；用户要求继续后正常审批重试，没有绕过检查。该服务错误不计测试失败或源码完成回执。

## 剩余门槛和停止边界

A真实认证full session→device/role keys/双方证明→OS实例→原挑战/Ticket-code-proof/活channel生产登记与退出撤销仍待交付。本人确认、A/C/Tool业务核验/页面及完整汇合验收pending；不挂生产factory/HTTP入口。OS credential handle仅受保护安装配置输入，不把私钥放账本或模型。

Default桌面/同登录开发IPC不是安全桌面或抗同账户恶意进程的正式部署保证，SQLite是组件journal，当前源与多个journal没有跨服务原子事务。晚取消/断线按已有真实记录和当前数据权限恢复，不推断许可/费用。D01/D03/D06不代选，写入安装exec与flags关闭。组件M1-M4装配/验证交付，生产bootstrap/真人门槛未完成；本包后停止，等待A审阅/派发。
