# MS-R2f M1：Windows 开发 IPC 固定接口

2026-10-09。固定基线 ms-i2i-start / d8023eb07e1460961782f297697da7428f6ad247，dev/runner。仅 D 路径，无新依赖/public schema/flags；内部 IPC v1 不是配对 V2。

```python
WindowsPipeListener(*, name: str, logon_sid: str, timeout: float = 10)
async accept(*, deadline: float | None = None) -> PipeConnection
async close() -> None
async connect_pipe(*, name: str, logon_sid: str, timeout: float = 10,
                   deadline: float | None = None) -> PipeConnection
PipeConnection.receive(*, deadline=None) -> bytes   # async
PipeConnection.send(data: bytes, *, deadline=None) -> None  # async
PipeConnection.identify() -> OsIdentity             # async
PipeConnection.close() -> None                      # async，幂等

@dataclass(frozen=True)
class OsIdentity:
    pid: int
    created: int
    user_sid: str
    logon_sid: str

class PeerRegistrationPort(Protocol):
    async current(identity: OsIdentity, *, role: str) -> RegisteredPeer: ...
AuthenticatedPipeSession(*, pipe: PipeConnection, registration: PeerRegistrationPort | None,
    directory: CurrentKeyDirectory, signer: IpcSigner, lifetime_seconds: float = 60)
async handshake() -> None
async check() -> None
async send(kind: str, body: dict, *, deadline=None) -> None
async receive(*, deadline=None) -> dict
async close() -> None
```

时间 deadline 为 monotonic 绝对秒，OS IO 默认10秒，可缩短，不超过10秒；frame最大256KiB，4字节 network-order长度前缀先校验再分配。单 pipe/session 一个在途操作，busy 拒绝不无限排队。connection TTL默认60秒（可信构造可1..600秒内配置），注册期限更短取其最小值；按墙钟和monotonic双重检查。关闭不flush、不重发command，取消通知CancelIoEx，等待OVERLAPPED取消完成后释放缓冲/事件/pipe/process句柄，异步 CancelledError 原样传播。错误/超时/坏帧/签名/身份失败关闭通道，关闭幂等；unknown发送不可自动重发。

DACL 明确 `D:P(A;;0x0012019B;;;<实际登录SID>)`，仅该登录会话，非 Everyone/anonymous/默认 ACL；避免GENERIC_WRITE隐含FILE_CREATE_PIPE_INSTANCE，server FIRST_PIPE_INSTANCE、PIPE_REJECT_REMOTE_CLIENTS，客户端仅本机 `\\.\pipe\uaw-*`。独立GetNamedPipeClient/ServerProcessId→持有OpenProcess句柄→GetProcessTimes/TokenUser/TokenGroups logon SID；server在读客户端证明后ImpersonateNamedPipeClient/OpenThreadToken对照实际token，finally RevertToSelf，不在身份模拟范围做业务IO。恢复失败进程退出，不把带模拟身份的线程交回业务池。仅PID/用户SID不证明UAW账号。

RegisteredPeer 固定字段：实际OsIdentity、完整owner、actor、device_id、role(control/device)、key_id/key_ref、pairing_ref、expires_at。由真实受保护登记适配器每次 current 实读，不从 body/user_id/approved/path 生成。缺此源不可用。IpcSigner绑定独立角色key和受保护credential_handle；使用现有真实Ed25519规范和command/control或pairing-proof/device域，但签名文档明确ipc_protocol/purpose/role/frame，不能重解释public command/receipt/Ticket签名。本机独立nonce、peer_nonce、connection ID和严格序号均签名；角色/当前key/撤销检查逐次执行。frame仅hello/proof/ready及command/receipt/recover/error，外层拒绝未知字段、重复key、非JSON数、float/deep/超大集合；应用body严格字段将在业务bridge验证。

```python
# 可信native组装，actual登记和OS credentials由A提供，body不包含主体授权。
listener = WindowsPipeListener(name=random_local_name,
                               logon_sid=WindowsApi().current().logon_sid)
pipe = await listener.accept(deadline=actual_monotonic_deadline)
session = AuthenticatedPipeSession(pipe=pipe, registration=actual_registry,
    directory=current_directory, signer=IpcSigner(binding=registered_device_binding,
    directory=current_directory, credentials=os_credentials))
try:
    await session.handshake()
    frame = await session.receive(deadline=actual_monotonic_deadline)
finally:
    await session.close()
    await listener.close()
# 拒绝：未登记OS进程、错误role/key/签名/nonce、超长/超时关闭，无业务调用。
# 重复：同连接sequence重复拒绝；重连必须新nonce/new Ref，未知command不重发。
```

M1真实实测：test_windows_ipc.py 实际两Python进程、隐藏helper、random Windows vault control/device key、显式DACL、actual进程/token/logon身份、双nonce当前角色签名及frame往返/退出/关闭；m1-3.xml 1 passed /1.31秒，凭据/管道/子进程finally清理。UAW account/pairing/native-confirmation依赖为独立临时fixture，不宣称真实用户配对或可信授权已完成。首次回执目录缺父目录、venv launcher PID与实际解释器不同的失败保留；直接启动同锁环境实际解释器后通过。M2再提交registry adapter和阶段源码，继续M3/M4。A控制端/组装仍归A，D只提供对称可消费内部transport。

API依据：[微软管道ACL](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights)、[身份模拟](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-impersonatenamedpipeclient)。D03部署/exec、native用户确认/生产账号登记仍独立，file_access flags不开放。

## M2 阶段接线（继续同包 M3/M4）

M1 源码 SHA：81bc7cabf997447dd550e27de502e7462a1cb5ce；M2 源码 SHA：ea16682101cc4c9a3e4d02398c5ccebbda6254a0。实际分支 dev/runner；基线仍 d8023eb07e1460961782f297697da7428f6ad247。

```python
registry = ConnectionRegistry(max_connections=16)  # 1..32，无许可持久缓存
await session.handshake()
channel_ref = await registry.add(session)
# RunnerChannelSourcePort 适配：
await registry.read(channel_ref, device_id=registered_device_id)
actor = await registry.authenticated_principal(channel_ref, device_id=registered_device_id)
# ReadOnlyRunner(channel=registry, channel_ref=channel_ref, ...)；actor 传可信入口。
await registry.close()
```

connection content Ref 由双方注册快照和 control/device nonce 的固定排序摘要得到，同连接固定；重连新 nonce/Ref。每次 read/principal/session 重查真实 OS pipe/进程生命周期、独立登记完整主体与期限、当前角色 key/revocation；断连、退出、改 owner/actor、到期或撤销即失效。未知/旧 Ref 拒绝，body 不参与登记。异步登记/密钥 await 也受 10 秒以内限时，协作取消关闭连接，不缓存执行授权。

阶段验证：`python -m pytest tests/unit/runner/test_ipc_frames.py tests/integration/runner/test_windows_ipc.py -q --basetemp tests/.artifacts/D/MS-R2f/tmp-m2 --junitxml tests/.artifacts/D/MS-R2f/m2.xml`，39 passed /13.48秒；Ruff 与 mypy（workspace + local_runner，23源码）通过。回执 ignored tests/.artifacts/D/MS-R2f，随机 OS 凭据逐例清理。M1 两次初始失败保留；M1 修复后30 passed。生产受保护进程/账号/key/pairing登记、native确认、控制端及应用装配仍由 A 提供，fixture 明示来源，不认作真实配对。

M2 改动文件：ipc/sessions.py、ipc/channel_source.py、tests/integration/runner/test_windows_ipc.py。M1 文件详见该提交。无公共文件/新依赖/flags 修改；继续 M3/M4，不自动下一包。
