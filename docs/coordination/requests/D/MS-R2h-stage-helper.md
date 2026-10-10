# MS-R2h M2 隐藏只读 helper 装配

ms-i2k-start / b7b79b150470a80f37b28fd52a2177f6de5b3124，dev/runner。M1源码97da1f39dac82b95c2c9e9b09d05b557209950ea，测试夹具修正41ab8da894d9d2983008133a4b822e49d00d20bb；22不同节点完整通过/32.09秒，首两轮21+1失败保留。

## 固定构造

```python
ReadOnlyHelper(*, bootstrap: BootstrapConsumer, protocol: RunnerProtocol,
    commands: ReceiptCommandReaderPort | None, journal: ReceiptJournal,
    executions: ReadExecutionJournal | None, roots: NativeRootSource,
    registry: ConnectionRegistry, currency: str)
await helper.start()                  # HelperAddress(name, actual OsIdentity)
await helper.accept()                 # 新固定 content channel_ref
authorization = await helper.authorization()  # 原 NativeReadAuthorization
await helper.serve_once()             # 实际原 receipt_ref
await helper.disconnect()            # 释放 listener/session/registry，允许新连接
await helper.close()                 # 永久关闭该实例，幂等
```

同一个 directory / ProtectedSigner / device key / mapping / RootBindings / protocol / owning command Reader / journal；缺源先503，不创 OS listener。accept使用实际DACL/current角色密钥/nonce/OS创建时间；源await后复查。authorization SQLite构造在线程；root代码/proof仅可信本机调用传入，不从IPC网页body传path/approved。IPC依旧仅原command_ref的command/recover，没有新native wire。unknown recover无原签名journal明确不可用。

## 实际进程入口

```python
owned = await HelperProcess.prepare(python=installed_python,
    assembly_module=trusted_installed_factory, environment=trusted_environment)
# A独立当前账号/挑战源绑定实际 OS 子进程 identity；identity本身不是UAW账号。
ready = await owned.start()
# A控制端连接 ready['name']，沿原注册双方当前key握手。
await owned.close()
```

固定 `python -m uaw_runner.helper_host`，仅安装时可信factory模块，无shell/命令请求程序/用户path参数；CREATE_NO_WINDOW，只有本人native窗口可见。stdin只有start/stop进程管理，不授权。stdout有界公共生命周期identity/ready/connected/receipt/failure/closed，不输出code/proof/owner/凭据/文件正文/根绝对路径。A factory实现HelperAssemblyPort.create(actual_identity)->HelperApplication(helper,on_connected?)。on_connected是可信本机适配而非approved回调；调用原native select/bind，原窗口本人决定。缺factory/首次来源拒绝，不挂生产入口。

标准库Popen由后台线程管理，适配当前Windows selector测试事件循环；无asyncio.run桥接现有循环。helper_host的asyncio.run仅新独立进程main。prepare/start/close有界，close优先stdinstop，5秒无退出仅kill自有子进程；listener取消排空并释放晚完成句柄，disconnect取消owned IO。

## 阶段验证

真实Windows helper8不同节点通过/15.64秒：隐藏真实device子进程+控制端、一次原Ticket选择绑定（typed UI double）、UTF-8/原换行实际读/实际设备签名content journal，删除文件＋取消后新进程新channel恢复原Ref；实际native timeout无bind；缺factory、owner/key/OS创建时间/revocation拒绝；pending accept关闭、管道不可再连。A首次登记/owner/challenge/Run authority明确受控fixture，肯定UI不计真人确认。m2.xml8失败（selector无subprocess transport）；m2-2.xml4失败（模块dataclass双身份、撤销Ticket应revoked）；m2-3.xml1失败（临时根夹具旧方法名），诊断/修复最终m2-4.xml8通过。失败均保留，无安全断言删除。

生产A源码/首次账号设备挑战仍缺，输入提案MS-R2h-bootstrap-inputs.md。真人未点击pending。不改schema/锁/flags/其他worktree，不开放写入安装exec，不代选D03。阶段提交后继续M3/M4。
