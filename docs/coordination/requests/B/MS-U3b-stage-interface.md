# MS-U3b M1 固定生命周期接口

2026-10-11。E:/UAW/.worktrees/context / dev/context。

干净原HEAD 8a590123c1aa166688e7ed830e8c9c5d2d76e89b；fetch后只读远端正式续包DISPATCH，快进 ms-i2l-a8 / 06ff3ef56b68d391387bc7b154fa58ecb00571f9，HEAD完全相等。源码输入 ms-i2l-a8-source / 16e0efaf6daff2fbbd0281473a8c6cc1f652d0e6。文档tag ms-i2l-a8-followup / 610a920d9cc83900f056b0eb2ccfaf13cb122ff8 已与ls-remote相同，git show只读续包规则；不合浮动integration或followup源码，共同start不移动，旧提交保留。

uv sync --frozen、原store pnpm冻结离线安装成功。读取A7 browser-installed-v1和A8 installed-file-sources；缺来源仍503，ready不授文件执行权限。本M1源码 **8271fd9e7467870e6e147eb7e00ff3d583f23e8b**。

客户端 localStart(meta,signal?) / localGet(id,signal?) / localStop(id,meta,signal?) 精确映射 POST /v1/runner/local、GET /v1/runner/local/{launch_id}、POST /v1/runner/local/{launch_id}/stop；POST payload={}，stop保留observed CAS。生成器锁 ms-i2l-a8，25实际paths/28methods/188完整定义；HttpRunnerLocalBegin/Get/StopResult严格验证，ready必有enrollment_id/device_ref/expires_at，未知字段拒绝。没有路径、proof、approved、模块、模型或flags入参。

```ts
interface InstalledLaunchPort {
  lookup(): LaunchLookup | undefined;
  start(signal: AbortSignal, recoverOriginal?: boolean): Promise<InstalledView>;
  get(id: string, signal: AbortSignal): Promise<InstalledView>;
  stop(old: InstalledView, signal: AbortSignal): Promise<InstalledView>;
  clear(): void;
}
const port = new HttpInstalledLaunchPort(client, localStorage); // 现有内存Web session/cookie/CSRF
// 本人点击才调用start。没有id丢回复：本人点击start(signal,true)，复用原request_id。
// 有id刷新只get(id,signal)，stop失回只get。clear是本地查找清理；服务端退出负责drain。
```

InstalledView为生成的InstalledLaunchView；LaunchLookup只含requestId/launchId/revision及可选原stop.requestId/revision。只按完整浏览器identityKey恢复；当前Principal必须user。同账号新session不接管。双击只有一个POST；迟到身份/Abort/clear拒绝返回，原id/request/revision/workspace复查。新启动前先GET旧实例，非终态不能新开；stop先GET当前版本，unknown不换ID重发。没有id时不会刷新POST，只能明确人工恢复。lookup副本，不保存状态/授权。

M1 72单元通过（原66+新6）、类型通过，generator字段逐定义等于实际tag源，冻结安装通过；自身ignored u3b-m1-unit.log/.xml、u3b-m1-typecheck.log、u3b-m1-generate.log、u3b-install.log。第一批契约fixture全是受控DTO，不是OS/native/SQL许可。

M2页面入口将置于原“本机设备与目录状态”对话框，InstalledConnection组件接受port/identity/connected；本人点击“连接本机只读目录”，系统账号确认→目录选择→只读确认三步提示，实际状态/原版本/停止。默认装配真实HTTP port，可选host注入。GET有界轮询、退出Abort/clear，202/ready不当文件Tool权限。M1交付后继续M2–M4，不等待A合入；A可按此签名接线，末包交独立dist/hash及handoff。

认证实连需A受保护限时同源launch和实际原launch ID；当前未提供，真实验收pending。不会读取A私有配置或代点native/成果接受，不扩Context/多Run/flags。


## M2 页面已交付，继续M3/M4

源码 **81e128cf505fb7d62a1980d975b2302e6f60bd11**。默认window host可注入installedLaunch:InstalledLaunchPort；省注入使用HttpInstalledLaunchPort(client)。原本机对话框内InstalledConnection接受port/identity/connected，原设备查询保留。本人点击才start，明确系统账号确认/目录选择/只读确认三步，实际状态/原期限/失败码/原ID；ready和202不当file Tool许可。停止先GET再CAS，丢回复只读对账。

默认串行2秒GET、最多120次本次读取，终态停止；达到上限显示手动读取入口，不更新原期限。错误隐藏旧ready，保留原ID；关闭/pagehide/注销/身份变化Abort、清旧状态，不自动再启动。无IDunknown只提供显式恢复原request_id按钮。组件没有赋权/模型/目录path或新API。

类型/build通过，3个新UI节点通过（单独运行，不将原72重复累计）；M1契约与原回归保留。自身u3b-m2-build.log、u3b-m2-ui.log/.xml。准确独立阶段dist位于apps/web/.test-results/u3b-m2-dist/，每文件hash在u3b-m2-build.json；A只读复制该构建，不执行B环境。原chunk>500KB警告保留。

继续M3竞争/恢复与M4受控Chromium、真实缺源回执；认证只读需A限时launch及原launch ID，真人操作未代理。
