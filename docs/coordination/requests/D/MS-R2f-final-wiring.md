# MS-R2f 最终接线与实际回执

2026-10-09；原工作区 E:/UAW/.worktrees/runner，dev/runner。工作区开工干净，fetch origin --tags、merge --ff-only ms-i2i-start 成功，HEAD/tag 等值 **d8023eb07e1460961782f297697da7428f6ad247**，uv sync --frozen 按独立环境检查64包。没有 reset/rebase、公共文件或其他 worktree 修改。

源码提交：M1 **81bc7cabf997447dd550e27de502e7462a1cb5ce**；M2 **ea16682101cc4c9a3e4d02398c5ccebbda6254a0**；最终 M3/M4 **d3f60771accca99832673820c8a43c4ec32f4cbd**。阶段接口/handoff 已单独提交36cb329；最终 handoff 另提交。原 MS-R2a..e 历史保留，不重做已接受包。

## 文件和固定接口

新增：apps/local_runner/uaw_runner/ipc/{__init__,windows_pipe,frames,sessions,channel_source,read_endpoint}.py；tests/unit/runner/test_ipc_frames.py；tests/integration/runner/{ipc_fixture,ipc_child,test_windows_ipc,test_windows_read_ipc}.py。
修改 tests/integration/runner/test_native_root_source.py，仅可选复用已独立 provision 的真实 OS key 测试组装，原 fixture 默认兼容。
文档：本文件、MS-R2f-stage-ipc.md、handoffs/D.md。workspace四文件无需改变；shared/schema/锁/composition/API/flags均未修改，无新依赖/公共 RefKind。

M1/M2详细构造及关闭语义见 [阶段接口](MS-R2f-stage-ipc.md)。最终增加：

```python
class ReadOnlyRunnerFactoryPort(Protocol):
    async def create(self, command_ref: Ref, *, channel_ref: Ref) -> ReadOnlyRunner: ...

ReadOnlyPipeEndpoint(*, session: AuthenticatedPipeSession,
    registry: ConnectionRegistry,
    commands: ReceiptCommandReaderPort | None = None,
    runners: ReadOnlyRunnerFactoryPort | None = None)
async serve_once() -> Ref  # 已验证、实际签名持久终态的 content Ref；发回成功后返回
```

dispatch/watch 是组件内部处理；外部可信入口调用 serve_once，先 session.receive 验证实际连接/当前key/nonce/序号。缺 Reader/factory/已注册连接及原 Runner 来源即不可用。endpoint只支持已登记 file.read，工厂必须构造匹配完整 command_ref/channel_ref/device 的原 ReadOnlyRunner，使用同一 registry 和独立 Reader 实例；禁止通过工厂新造 owner/grant/authority。

内部帧 version=1。command/recover 的 body **仅** `{"command_ref": <完整固定Ref>}`，收到 Ref 后 Reader 从独立登记读原签名 RunnerCommand/device/owner；不使用输入 command/principal/approved/path 等自证。receipt body **仅** `{"command_ref": <原Ref>, "receipt_ref": <实际content Ref>, "receipt": <原RunnerReceipt>}`。原命令/回执公共DTO及Ed25519域完全沿用；IPC外层证明文档带独立protocol/purpose/role，不能把公共command/receipt/Ticket签名改作通道证明或配对V2。A控制端应再次校验原command/attempt/Usage/action/FileContent、当前device签名和receipt_ref.content_hash，传输成功不等于Tool业务成功。

## A 最小装配例子

```python
# A: actual_peer_registry 每次按真实 OsIdentity(pid, creation, userSID, logonSID)
# 读取受保护注册的完整 owner/actor/device/current role key/pairing/expiry。
# 缺真实用户确认/配对登记，不给出 RegisteredPeer。
listener = WindowsPipeListener(name=random_local_name,
    logon_sid=WindowsApi().current().logon_sid)
registry = ConnectionRegistry(max_connections=16)
try:
    pipe = await listener.accept(deadline=trusted_monotonic_deadline)
    session = AuthenticatedPipeSession(pipe=pipe, registration=actual_peer_registry,
        directory=current_key_directory,
        signer=IpcSigner(binding=registered_device_ipc_binding,
            directory=current_key_directory, credentials=windows_credentials))
    await session.handshake()
    channel_ref = await registry.add(session)
    # factory.create(ref, channel_ref=...)：实际异步 authority + owner mapping、
    # 原签名验证/持久 admission、真实已消费 RootSelection/grant/期限/OS身份根源；
    # ReceiptJournal(path, protocol=protocol, reader=actual_commands)、
    # ReadExecutionJournal(other_path)、实际OS device key和明确currency；
    # ReadOnlyRunner(... command_ref=ref, channel=registry, channel_ref=channel_ref,
    #                roots=actual_root_source, journal=journal, executions=reads, ...)
    endpoint = ReadOnlyPipeEndpoint(session=session, registry=registry,
        commands=actual_commands, runners=registered_read_factory)
    actual_receipt_ref = await endpoint.serve_once()
finally:
    await registry.close()
    await listener.close()
```

actual_commands 可消费 A 已有 Container.runner_receipt_commands，但实际 channel→owner 关系、数据可读权限和版本/摘要仍须独立实读。生产系统需明确提供 PeerRegistrationPort、受保护当前key/私钥handle、native确认与配对来源、当前AsyncRunnerAuthority/Root/PrincipalMapping及持久路径。目录/端口/工厂由可信组装固定，不接受客户端任意 Python 路径、凭据名或SQLite路径；默认没有这些注入，D组件不挂载网络/用户项目入口。

## 生命周期、期限与恢复

显式本登录会话 DACL 的内核实际描述符已测试：仅一个允许ACE、实际logon SID和0x12019b，非默认Everyone/anonymous；FIRST_PIPE_INSTANCE、REJECT_REMOTE_CLIENTS、本机管道路径。实际双进程PID/创建时间/process token +服务端客户端模拟token核对；每次活性再读实际进程身份，持有原process句柄检测退出/PID复用，模拟总恢复，恢复失败进程fail closed。每次独立注册完整关系/key Ref摘要/当前角色撤销复核。连接nonce/序号单次；同session不得重新handshake；重连新nonce/new content Ref，旧Ref不恢复许可。

最大256KiB，长度前缀先验证再分配，真实上限帧通过，超限/0/断帧拒绝。握手/读写/异步注册与签名await默认10秒，可缩短；connection最长600秒且受实际登记期限约束，墙钟与monotonic一起检查。每pipe/session/endpoint最多一项在途，registry最多16（可信构造1..32），无无限队列。endpoint业务响应也受10秒以内限时并每50ms复查连接生命周期；退出/撤销/超时关闭并取消等待中的业务task，原CancelledError传播。OVERLAPPED取消完成后才释放buffer/event/pipe/process句柄；连接打开时取消也回收真实handle；关闭幂等，不flush、不自动重发。成功 serve_once 后连接由外部finally关闭；其返回只证明发送已完成，不证明对端已接受业务结果。

原 ReadOnlyRunner保留签名/Root/owner/channel/authority/request-parameters-policy-workspace版本、flags、lease/fence、deadline、取消及admission/execution CAS；真实OS根/文件句柄与读取上限不变，签实际终态后publish原journal。这里只接获准read，不从admission签发receipt。

回复丢失不自动重发未知command。新可信连接可显式 recover 原command_ref：先 Reader复查当前数据权限和 once journal，只有原已签名结果才恢复；无记录/未完成明确不可用，不新admit或重读。恢复仍核当前设备签名/角色撤销、owner/Root/data access，原取消不抹掉真实历史。测试在实际journal提交后故意断开回复，删掉原临时文件、将Run设cancelled，重建连接与journal实例，收取完全相同原签名/content Ref，authority新准入查询0次。双实际连接并发仅一次实际OS read，其余恢复同结果或unknown拒绝，不伪造新成功。

## 验证命令与结果

回执目录 ignored `tests/.artifacts/D/MS-R2f`，不提交数据库/私钥/临时内容。

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py -q --basetemp tests/.artifacts/D/MS-R2f/tmp-full --junitxml tests/.artifacts/D/MS-R2f/full.xml
.venv/Scripts/python.exe -m ruff check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
git diff --check
```

**505 passed /160.20秒，0 failure/error/skip**；JUnit 159.866秒。原基线432项＋本包73不同节点（frame29、Windows IPC32、Windows read IPC12）；不累加重试。Ruff通过，格式49文件，mypy24源码，diff通过。full.xml/full.log、ruff.log/format.log/mypy.log、checks.json/public-hashes.json保留。

专项 m4-2.xml 70 passed /57.91秒；随后 bounds.xml 4 passed /5.31秒（其中1为既有双进程用例、3新增），最终全部505再验证。真实案例：OS内核DACL、双进程token/PID/创建时间/当前role key、nonce/重放/坏签名/冒名/错误device/key hash/无登记、0/过长/断帧/超时/取消/重复取消、进程退出/重连与registry上限、source await到期、body权限注入拒绝、临时UTF-8实际read/设备签名journal传回、authority等待时撤销/Root撤销/过期/断连/取消/响应超时、双连接一次实际读取和回复丢失恢复。原D真实签名/新进程admission/journal CAS/句柄读取回归保留。

44份 `windows-ipc-*.json` 均 cleaned=true，记录随机namespace OS provision和 finally清理，不把fixture清理状态当单用例通过判据；最终测试通过数由JUnit确认。子进程仅本session拥有的隐藏Python helper，finally等待/终止及关闭流，pipe/process/event句柄关闭；不访问既有用户凭据或项目。原 windows-control/read OS 回执由原D回归重新验证，均清理。未启动PG/未操作任何55432..55435数据库服务。

失败历史保留：M1首次回执父目录缺失和venv launcher PID不等实际解释器；M3首次fixture把device-only private检查用于control key（4失败），修复后helper stdout GBK无法输出emoji（2失败），固定UTF-8后fixture write_text自动CRLF与预期原文不一致、新增测试缺DomainError import（m4.xml 7失败/59通过，伴随未等待测试task消息）。均为测试组装/输出问题，改为真实原bytes、正确role及import；没有放宽业务验权、签名、取消或读取检查。后续专项及最终回归全通过。中途Ruff格式/import问题也已修正。

## 接受边界与缺口

真实：Windows同机命名管道、OS身份/内核ACL/生命周期、随机WindowsCredentialStore私钥、真实Ed25519双向签名、临时文件读取、开发SQLite一次使用和实际终态恢复。
受控独立fixture：UAW account/设备owner/pairing注册、native confirmation、根选择确认、当前Run authority/flags/lease与计费currency。它们不由body生成，也不构成真实用户配对/项目授权。尚缺A生产受保护登记、真实native确认及控制端/组装/Tool业务校验。没有非本登录会话或远程主机实连环境，本包内核ACL/本机身份反例与REJECT_REMOTE_CLIENTS配置实证不冒称跨用户/远程部署验收。

这是Windows开发适配器及组件journal，未决定D01/D03/D06；不发布配对V2、不新增list/写入/安装/exec，不开放flags、不自动Tool applied/not_applied/零费用。当前源复查与多个服务不具跨服务原子事务，晚撤销/断连可能留下真实已签名原记录，只能以当前数据权限恢复。四项完成后停在MS-R2f，完整产品/完整MS-R2及正式部署继续由A另行派发/验收。
