# MS-I2l A1：固定安装模块和每次启动的实际来源

本阶段不移动ms-i2l-start；具体源码SHA及阶段标签见DISPATCH后续A1回执。A/D v1对象与D的start/进度签名保持；没有新的HTTP root授权或公开配对V2。

## 父端入口（A）

```python
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch

launch = await PreparedEnrollmentLaunch.prepare(
    container, owner=actual_authenticated_web_principal,
    python=installed_python, state_directory=installed_runner_data_directory,
    currency=actual_configured_currency, environment=trusted_install_environment,
)
try:
    # candidate_id、enrollment_id、policy 来自真实捕获和原持久登记，不从body声明。
    ready = await launch.start(on_progress=observer)
finally:
    await launch.close()
```

调用仅供可信本机composition/operator；没有model tool或HTTP可选python/module/environment/path字段。owner必须原完整当前Web Principal，先实际会话检查；同一个Container一次准备一个活launch，多次初始化串行。python及数据目录是已安装开发部署配置，不是用户项目路径；MODULE固定`uaw.infrastructure.installed_helper`。本阶段不选择D03正式部署方案，也不执行命令/安装/写用户文件。

prepare生成本次独立device id/双方actor与真实Ed25519角色key，私钥存原Windows凭据库；LocalState仅保存原公钥。隐藏prepare→独立实际PID/创建时间/SID/logon→OwnedEnrollmentCandidates.capture→原begin→受保护EnrollmentProofServer。期限与hash直接来自原challenge，角色key与Web身份在受保护交付后重查。准备完成仍pending，没有pairing_ref/根权限/native确认。

## 子端交付（A固定模块，D host消费）

父端环境只新增`UAW_INSTALLED_HELPER_NAMESPACE`和`UAW_INSTALLED_HELPER_LAUNCH`两个selector；无proof/code/private key或文件正文。部署环境本身由operator提供，不接受HTTP/model输入。原每次启动descriptor和最小服务端设置放Windows凭据库两个随机handle，UTF8≤4096、UTF16LE≤4800 bytes。DB与Web用户/cursor/会话签名配置只能从受保护设置解析；不传管理员或第三方模型credential，也不启动子端Agent worker。凭据库是同Windows用户开发信任边界，不宣称其他同用户任意程序不能读取，OS实例授权仍靠真实独立来源复核。

descriptor内含原owner/enrollment/hash/expiry/device/role credential handle、原实际device OsIdentity、已安装内部state目录、原受保护proof管道name、配置handle、明确账务currency。字段严格，拒绝approved/任意模块/用户目录/额外字段。selector不是授权；子端实际WindowsApi.current必须等于descriptor，随后读取实际原SQL Web会话、OwnedCandidate、双方当前key及原challenge比较hash/identity/expiry，再用FirstEnrollmentDeviceFactory进入真实native。

installed_factory要求D的HelperBootstrapProgress和first_start start。没有阶段适配就明确unavailable，不回退普通15秒、受控registry或native Yes。子端PostgreSQL要求既有`control_plane_loop`；[D精确修复请求](MS-I2l-D-selector-loop-repair.md)。

## 已提供具体paired factory / 尚缺消费

`PairedInstalledFactory`使用EnrolledPeerRegistry的实际active/natively confirmed记录、当前key、同一映射，装配ConnectionRegistry、BootstrapConsumer、NativeRootSource/RootBindings/LocalRoots/PersistentRootGrants、真实RegisteredRunnerAuthority/ReceiptCommandReader、PersistentAdmissions、签名ReceiptJournal/ReadExecutionJournal、ReadonlyHelper。其子端Container与客户端在helper.close时关闭；没有fake owner/command或任意Executor。

EnrolledNativeChallenges以实际已连接session、原LocalState Ticket、当前active owner/device/key检查根挑战。根Ticket的实际签发/受保护交付、on_connected本人选择/绑定、父端current RunnerDevices/Root/FileRoute/Tool权限组装仍是M2/M3任务；本阶段空根始终拒绝文件读取，helper可构造不表示已授权。账务currency必须管理员实际配置，不靠模型猜。

## 清理与恢复

close幂等且排空自身关闭任务；先关闭自有helper/proof，再撤销本次新key并删除四个原随机protected handle，迟到OS credential put/register必须排空再清理。子端启动失败/cancel同路径；cleanup异常明确报告，不冒充清理完成。保留原SQL/LocalState/journal历史；不删除用户资料或覆盖已有key。

新PID/实例必须新candidate/enrollment，不能借旧active重复授权。丢命令回复只能沿原journal恢复，此入口不发送任何文件命令。原活同实例factory内部兼容规则保持；本protected安装模块一次create，不能用一个locator重开第二个helper。

## 当前验证边界

新的实际准备/拒绝/清理测试使用A自有SQL、真实Web会话、固定production module隐藏子端、真实Windows凭据及公钥；没有本人native Yes、目录选择、模型或file.read。两个子端SQL拒绝首轮发现D默认Proactor事件循环不兼容，D修复到达即复跑，失败回执保留。单元严格字段/缺selector覆盖另记。

原办公completed与学术pending保持旧真实调用来源；本阶段不能标MS-I2k/MS-I2l整轮通过或新全量，不开默认flags。D阶段SHA先合入、C多资料读取签名到即可独立做A origin router，不等待所有包结束。
