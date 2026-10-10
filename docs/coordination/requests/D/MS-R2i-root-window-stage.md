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

## 同包修复最终定向验证

147不同节点通过/139.44s，0失败/错误/跳过：新增25构造边界＋6实际Windows节点，原116受影响native/root/helper read/recover兼容，不与前包644或阶段重复累加。

真实隐藏进程、IPC/当前OS role keys/原签名/临时根：default60与120分别实际进入session/native；120 session有效期限大于90秒且不超过120；短原登记限制channel/native并阻止过期读取；短原Ticket限制prompt/grant，即使channel仍120也阻止读取，attempt为0；实际native自动取消/close幂等、自有process退出0且Ticket未消费；新process/reconnect恢复原签名content Ref，删除文件后不重新打开，原grant expiry和confirmation expiry完全相等，attempt仍1。肯定UI/账号/authority是明确fixture，不称本人通过；没有A新真人重验。

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_helper_root_windows.py tests/integration/runner/test_helper_root_windows.py tests/integration/runner/test_helper_runtime.py tests/integration/runner/test_native_authorization.py tests/integration/runner/test_native_dialog_windows.py tests/unit/runner/test_native_confirmation.py tests/integration/runner/test_native_root_source.py -q --basetemp tests/.artifacts/D/MS-R2i-root-window/temp-final-2 --junitxml tests/.artifacts/D/MS-R2i-root-window/final-2.xml
.venv/Scripts/python.exe -m ruff check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
git diff --check
```

Ruff、73文件格式、Mypy34源码、diff通过。回执ignored tests/.artifacts/D/MS-R2i-root-window/final-2.xml/log、ruff/format/mypy.log和checks.json/nodes.json。原windows-first.xml/log为5通过/1测试观察抢在grant CAS前读取失败；修正等待原持久绑定而不删断言。selection-error.log保存误写不存在测试文件、0测试执行，不计通过；stage.xml25与最终147不重复计数。测试fixture只增加可信窗口配置/观察元数据、新Ticket创建时可显式短期限；没有修改旧Ticket/grant，生产只有runtime兼容参数。

A按阶段源码e5d27593e9639fbca2a3964f055d73466093192c消费即可，新的明确root实例两端120、普通默认60；原当前登记/原Ticket依旧取更早值。A负责installed/父端消费与本人重验，原两个真人ipc_timeout回执保留，尚无成功本人root/文件/模型通过声明。不改首次账号native60、普通15/first90、flags或D03。最终源码与独立handoff另记精确SHA，本同包修复后停止。

## 后续真人失败与只读审查（2026-10-11）

上文“没有A新真人重验”是147项运行时的阶段状态；其后 A 已消费阶段并进行了第三次本人尝试，仍未看到目录窗口，root_selected=false，无文件/模型成功。最新审查与所需原子端失败码见 MS-R2i-native-root-review.md。不能把本次120参数修复或147通过声明为真人根选择完成。最终测试源码0c7aec747623f42b479c922808c8e018760453e5；原fixture LF恢复提交cd747489a52a902d188997952df972c1a58bc203保留历史；最终handoff另提交。
