# MS-R2i 同包阶段：原生目录窗口显示与提醒

2026-10-11；E:/UAW/.worktrees/runner / dev/runner。阶段源码 **ef609407b0875fb51c53121a31a5a56d37dab93a**，仅 native_dialog.py + D unit/integration visibility 三文件；接在原窗口期限源码及handoff b6554c250f46dfb2996758a9896492d393519fcc 后。A无需新构造/DTO/依赖，保留当前 trusted ReadOnlyHelper 60/120 配置，不合并浮动integration。

原本人120秒失败/未看到目录窗口保留；A受控实际源预UI复现49.91s已进入目录调用并拒绝，不能称本人成功。本修复针对隐藏helper的自有窗口初始化：BFFM_INITIALIZED 仅对回调工作线程拥有的 HWND，在实际 Default 输入桌面复核后 SetWindowPos 显示/置顶（不改位置/大小，不先抢焦点），请求 SetForegroundWindow；系统拒绝焦点时用三次 FlashWindowEx 提醒。无外部窗口、全局桌面、AttachThreadInput、默认路径、选择/OK输入。窗口随原取消/期限销毁；显示失败明确 runner.native_window_display，不把未显示当批准。账号/最终只读 MessageBox 追加 MB_SETFOREGROUND/MB_TOPMOST，原 OK/Cancel、默认Cancel保持。

官方语义：[BFFCALLBACK 初始化消息](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/legacy/bb762598(v=vs.85))；[SetWindowPos 显示/置顶](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos)；[SetForegroundWindow 可能被系统拒绝](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow)；[FlashWindowEx 不改变活动状态](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-flashwindowex)；[MessageBox 显示 flags](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-messagebox)。这是显示/提醒修复，不证明第三次失败确由后台窗口造成，不保证本人已看见或已批准。

8不同定向节点通过/3.83s：新增4单元（自有窗口/焦点拒绝/显示失败/外部线程拒绝）+1真实隐藏Windows子进程；原3 native自动取消/timeout。真实子进程报告 actual HWND visible/topmost/own_thread=true，随后仅 Event CANCEL，原 native_cancelled，窗口已销毁，自有进程退出0，无根选择/用户文件/凭据/读权限。肯定本人确认pending。Ruff、76格式文件、Mypy34源码、diff通过。

```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/runner/test_native_visibility.py tests/integration/runner/test_native_visibility.py tests/integration/runner/test_native_dialog_windows.py --basetemp=tests/.artifacts/D/MS-R2i-visibility/temp-stage-2 --junitxml=tests/.artifacts/D/MS-R2i-visibility/stage-2.xml
```

原首次 HWND 负指针表示断言错误、basetemp父目录未创建导致4setup错误保存 visibility-stage.log/stage.xml；断言改为实际 HWND(-1) 表示，父目录由首次XML建立，完整复跑8通过。原Ruff两import错误留ruff-first.log，修正后ruff.log通过。不删权限/取消断言，不重写源码历史。

阶段可供A审阅；A已发布诊断来源3ff37f4cc8524591648e0a450c246757a5a6fc8a，本D只读参考不合并/不改A。A保持connected后原failure/closed消费、准确phase/error_type/code与清理，待本人重验目录窗口/真实根选择。D继续同包原native/root/IPC/read/journal兼容回归，终态handoff另交，不加时间/flags或代本人批准。
