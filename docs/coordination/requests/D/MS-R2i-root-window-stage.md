# MS-R2i 同包修复：可信 helper 根确认窗口

D E:/UAW/.worktrees/runner /dev/runner；保留最终源码1eac90b7c942b0bd9eec6f779f4403cc072a1274/handoff0a386383d04f1158c55c3436bb4a516ae7cf77b7。A请求MS-I2l-D-native-root-window-repair.md已交接，远端精确核对ms-i2l-a3-source /5fbfa752f6d83a3e663b98b6b002eb8a481e8b3e，仅只读其消费者，没有合并浮动integration或复刻A代码。

阶段源码 **e5d27593e9639fbca2a3964f055d73466093192c**；仅runtime.py和D unit test_helper_root_windows.py。

```python
helper = ReadOnlyHelper(
    bootstrap=bootstrap, protocol=protocol, commands=commands, journal=journal,
    executions=executions, roots=roots, registry=registry, currency=currency,
    session_lifetime_seconds=120, native_timeout_seconds=120)
```

两个新增参数keyword-only，均默认60兼容。仅可信安装组装在新的明确root实例提供；严格int/float、拒bool/NaN/Infinity/其他类型，0<native<=session<=120，不读command/body/path/approved。accept向原AuthenticatedPipeSession传lifetime_seconds；authorization向原WindowsNativeConfirmation传timeout_seconds。不改普通15秒/首次90秒/首次账号native60秒。

120只是等待上限。原session min(当前注册双方expiry,本次lifetime)、native min(原Ticket/current channel expiry,本次timeout)继续有效，不修改旧ticket/grant/registration，不延长原已确认根；重连新Ref仍受原期限和current owner/key/root/Run/lease/fence制约。超过/错误参数ValueError，在创建任何OS资源前拒绝；运行中原取消/DomainError和close规则保持。

25不同构造参数单元节点通过/0.12s；Ruff/Mypy34/diff通过。回执tests/.artifacts/D/MS-R2i-root-window/stage.xml/log。构造源是明示double，只证明参数，不冒充IPC/native/授权。继续实际Windows参数注入、短登记/Ticket、取消/read/recover兼容验证；真人重验A与本人完成，A原两次ipc_timeout失败保留且未产生根授权/读取/模型调用。
