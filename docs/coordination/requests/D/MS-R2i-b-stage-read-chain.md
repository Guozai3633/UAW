# D MS-R2i-b M2阶段与 A 原来源缺口

2026-10-11；dev/runner，准确A8基线06ff3ef56b68d391387bc7b154fa58ecb00571f9。M1源码3f660f69fc2d8aaa7885aed51e76e03e0ff1ceef/阶段cfac57bf7535c426650a383d82057ecc92c7561f；本阶段源码 **c1c081fb5d159b72d0e34277dd3f9f0b3656ddf0**。

D修复：PipeConnection.wait_readable(*, deadline:float)->float，以原会话monotonic_expiry等待首字节，只有PeekNamedPipe，不读文件、不检查后缓存许可；ReadOnlyHelper.serve_once()随后在min(首字节+原10秒, 原会话期限)内做原bootstrap、完整frame/权限/执行检查。没有改变15/90/120、256KiB、lease或添加timeout。原空闲等待误将审批无帧当断帧，在等待用户决定时关闭连接；idle不属于partial frame。取消即时传播并drain句柄；断帧/超长仍走原收包检查。

6个不同定向节点通过16.30秒，包含真实隐藏双进程空闲10.2秒后一次签名读、stop零journal，4调度/期限单位节点；Ruff34文件/28源码Mypy通过。初次idle2节点15.23秒已保留；直接单文件Mypy没有MYPYPATH的import检查失败保留含义为调用环境错误，最终显式MYPYPATH=src;apps/local_runner通过。

原A8读链未通过：初轮53.24秒D遗漏implemented_flags fixture导致feature_disabled，已在新Run之前补齐（生产默认仍空）；第二轮59.00秒原helper空闲收包超时导致file.current_browser_owned_root，D已修复。m2-3用户消息/工具会话中断，无XML、不记passed；准确SQL角色keys匹配其随机namespace，4遗留handle删除/2keys撤销，自有子进程已无残留。修复后m2-4在130.24秒失败+teardown错误：原facade返回ipc_timeout/Connection expired during source await，且A InstalledLifecycle.run清理await launch.close收到CancelledError，stop_entry的entry.done尚未set，container.close又返回cleanup_incomplete。本轮没有读回执，原fail/error XML不更改。实际原临时RootGrant.owner确定其随机namespace，凭据0残留、2keys revoked；没有触碰用户凭据。

A需处理的具名输入（仅提案，D没有修改A文件）：

1. `installed_files/installed_lifecycle`原审批/来源成本：callback已需35–40秒，后续Original ToolApprovalAuthority多轮bridge.resolve→owned_ready/current_root→双角色SQL查询，原较早expiry被耗尽。保持固定source指纹和前后current checks，不加时/删检查/缓存执行许可；需给成本可控的原来源组合。D parent/child按namespace记录calls/seconds，phase与budget/lease/register/send/read/sign/journal分别观测；执行期缺项表示未到阶段而非0成本。M1实测child callback35.428秒、整启动44.821秒、assembly1.084秒。
2. `InstalledLifecycle.run/stop_entry`自有task在进入finally cleanup时不应再被stop_entry.cancel打断，finally需可靠done/异常drain；保留原错误。D夹具已在finally再次drain准确own launch并原样重抛A清理失败，不伪造关闭成功。
3. 固定A8 `PairedInstalledFactory.create`的child RunnerCommands构造仅roots，gate/signing为None。RegisteredRunnerAuthority.current调用collect时会要求真实root_action_signing_sources。需A注入原完整Tool审批与当前control verify，不能用allow gate或模型/body声明；D不把它当已可执行。
4. 实际回执/恢复接线：D helper_host原一次serve_once后disconnect/relisten，A lifecycle.child_failure只接受failure frame；后续真实receipt事件与原实例当前状态的关系、原RunnerPipeClient丢回复后关闭、InstalledControlConnection.used拒绝重连、原root marker精确channelRef在新连接下的复核，均需A给原实例受控重连/原签名journal消费接口。恢复必须新connection Ref、当前root/owner/key，绝不再command dispatch/open，unknown不重发。

消费例：新fixture Run之前固定available flags和provider metadata，`p=installed_file_case(...)`→`await p.approve()`（SQL受控用户决定明确标fixture）→`p.bindings.tool.facade.invoke(p.raw,p.ctx)`，后者目前真实期望ok节点在固定A8失败。阶段测试源码保留成功断言，不能xfail/跳过或称Tool/Runner成功。

继续M3/M4独立D边界和实际组件journal重启恢复；A源待发布后接，不合浮动integration、不回退已交接口，不重跑旧695全量。真人与新模型验收pending，不弹本人窗口、不读用户目录。
