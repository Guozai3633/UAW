# A13 D M1：统一来源消费接口与效果检查点

2026-10-12。dev/runner / E:/UAW/.worktrees/runner。准确来源
ms-i2l-a13-source / 69fae72742a8a64b55a240cb735066aeef78240f；
远端正式DISPATCH元数据6ec7d0f5ea30d718efcdab29309f8c19c3436366。
干净检查/fetch/远端tag核对/ff/HEAD精确tag/uv sync --frozen已完成，旧失败/清理/提交保留。

## 显式可信构造/调用（非IPC wire）

```
helper = ReadOnlyHelper(
    bootstrap=bootstrap, protocol=protocol, commands=reader,
    journal=journal, executions=executions, roots=roots, registry=registry,
    currency=currency, current_source=original_current_source,
)
runner = ReadOnlyRunner(
    protocol=protocol, command_ref=registered_ref, journal=journal,
    executions=executions, roots=roots, channel=registry,
    channel_ref=original_channel_ref, signer=signer, device_key=device_key,
    currency=currency, current_source=original_current_source,
)
receipt = await runner.execute(
    registered_command, authenticated_principal=trusted_channel_actor,
    response_deadline=original_reply_deadline,
)
```

ReadOnlyPipeEndpoint新增current_source=None；HelperReadAssembly从helper原同对象传入。
Factory.create(command_ref, *, channel_ref)签名不变，未注入旧调用兼容。
A13 InstalledReadOnlyHelper在super后已保存current_source，本阶段D在connect时显式传给endpoint/factory。
A可改自己的factory为super(current_source=current_source)，D不改A文件或公开schema。
endpoint强制runner.current_source与自身为同对象；A现有工厂已检查commands/store/authority/roots/registry同对象。
构造元数据不授权，body不得提交port对象、owner/approved/path。

## 检查点表

| 边界 | 原等待与效果 | composite消费/独立复核 |
| --- | --- | --- |
| helper idle→bootstrap→receive | 首字节前只等原session；首字节后bootstrap.connected、frame验证 | helper固定until=min(first_byte+原timeout,session.expiry)，timeout_at覆盖bootstrap；同一until传serve_once/dispatch/execute/current/send，不新now+10 |
| endpoint主体与登记 | registry实际当前actor、Reader.resolve、session.check | 仍从独立可信通道读取actor，fixedRef/hash/device；Reader用于判断原attempt/recovery，不走active composite代替旧回执权限 |
| Factory await | 固定依赖构造、原channel与对象一致性 | snapshot只复制元数据；endpoint后session检查和runner效果前复查保留 |
| runner第一次current | 当前原source/owner/context/request/parameters/channel/root/authority | 一次composite替代Reader→mapping→channel→root→两次authority递归；严格类型、脱离副本、固定actor/owner/device/key/root/命令与原runtime交叉比对 |
| current关键本机await | 实际consumed native selection/Ticket/signature/key/root目录身份与命令签名/root scope | NativeRootSource._read不再次展开mapping；admission.external真实control signature与本机root；随后同until fresh composite，对全投影比较，不跨等待allowed缓存 |
| 私钥await→admission CAS | ProtectedSigner实际当前设备私钥；准入一次CAS | composite callback替换旧AsyncAdmission.authority展开；原commit真实key/root/取消/command与lease期限、reply期限CAS内仍检查；之后runner fresh current与首次固定绑定比较 |
| execution claim→OS open | 独立执行一次claim、真实WindowsReadHandle打开 | 原stopped/最早期限/key/root/一次CAS保留；不从composite直接生成receipt或绕过OS |
| OS open后→read | 打开后最终路径/根与文件身份、替换竞争；read在线程中有界 | 关键await后fresh current；handle.check/read前后同一根/句柄，1MiB/64KiB/UTF-8不变 |
| read后→sign | 实际结果/Usage；签名前源复查 | fresh current，原device receipt域签名不改 |
| sign→verify→signed CAS | sign await、actual signature verify await、持久一次签名写入 | 每个关键等待后fresh current，native/key/OS句柄/期限与停止仍在CAS guard；保留原content固定Ref |
| publish→response | owningReader数据权限、原publish/read与实际签名、channel | 执行后fresh current保留；旧数据Reader恢复复查；send沿用until，不额外预算 |
| original attempt/recover | 旧已签名/已发布或未知原journal | 不调用active composite；当前Reader/owner/root/key/channel/数据权限与原receipt签名，取消Run不推拒绝旧数据，unknown不重发 |
| watch | 每50ms后完整双方当前登记/key/OS/期限，断连取消dispatch | 暂保留原session.check；A13.wait_changed仍完整current，未旁挂为廉价通知，不删关键检查/加睡眠 |

当前每个runner.current用两次composite把本机external await夹在中间；这是两个不同效果检查点。
不再独立调用旧AsyncRunnerAuthorityPort.current，测试将其设为fail确保无旧图旁挂。
既有Reader数据权限路径不缓存或合并成执行许可。

## A监控输入提案（未装配，pending）

同签名wait_changed若A改为初次完整owning校验＋本次SQL current/history/absence/tombstone最终fresh单条比较：
需明确所有原Run/task/model/config/provider/flags/角色/审批/action/budget/attempt/lease/fence/device/owner会话登记输入覆盖；
不返回allowed，不跨调用保存payload，不晚于原until或command期限，初次失败立即拒绝，cancel释放SQL观察/连接。
其初次校验不能被dispatch当作效果许可；effect current仍完整且等待后复查。

该SQL watcher不能覆盖SQLite native ticket/root grant、控制/设备key目录、OS实例、live pipe。
D现有session.check查询双方registration，仍递归SQL且保留。要降低重复图，A需提供明确的
双方原peer绑定当前失效检查port，覆盖实际owner/session/enrollment/candidate/native journal/key角色/OS identity；
或将其全部SQL谓词纳入wait_changed并说明与D本机原registered metadata对应关系，D才能独立监控
原peer role/key_ref/public digest/角色撤销、原pipe/进程PID+creation+SID/logonSID和native grant/Ticket/key/期限。
只查OS或只查key不代表当前账号授权；无必要owning来源就保持当前watch与pending，不能用测试Event。
A发布准确源后再消费，不假定新wait_changed已发布或便宜。

## M1回执

stage.xml/log：180passed/72.31s，旧read_executor/AsyncAdmission/真实WindowsIPC及deadline scheduling兼容。
composite-stage-final.xml/log：25passed/6.71s；显式组件authority/root/channel，实际Ed25519/临时OS/SQLite；
严格错type/schema/ref/context/actor/owner/device/key/root/action、等待取消/fence/lease/flags/request/policy/channel/owner/root/双方key/期限拒绝及旧cancelledjournal恢复。
没有宣称SQL witness、真人native或生产IPC通过。Mypy35源码通过，stage-mypy初始17类型错误/测试fixture与模型构造失败保留。
本阶段源码与本接口独立提交；M1后继续M2真实SQL/Windows临时完整链、journal与原回归。

实际M1源码：bb24f69761429a110e5906063ed4333220f35f53。
