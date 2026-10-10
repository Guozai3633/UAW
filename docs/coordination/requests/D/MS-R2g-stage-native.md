# MS-R2g M1：Windows真实本机确认接口

日期2026-10-10，工作区E:/UAW/.worktrees/runner，dev/runner；实际 ms-i2j-start/HEAD 等值 abb4590f2bfe53c601e0f6a4a3b65447ba4ec502，干净后fetch/ff-only/uv sync --frozen成功，64包。源码 SHA 在阶段handoff记录。

新增Runner内部 native_dialog.py / native_confirmation.py；新增D unit native_confirmation和integration native_dialog_windows。只用标准库ctypes/已锁签名依赖，不改公共schema/锁/HTTP/flags，不决定D03。

```python
RegisteredNativeChallenges(*, state: LocalState, registry: ConnectionRegistry,
    channel_ref: Ref, device_id: str, mapping: RunnerPrincipalMappingPort | None,
    clock: Callable[[], datetime])
# current(ticket_id) -> NativeChallenge：独立登记Ticket/完整owner、actor、
# 实际当前本机OsIdentity、channel固定Ref和有界期限，不接path/approved。
WindowsNativeConfirmation(*, source: NativeChallengeSourcePort | None,
    directory: CurrentKeyDirectory, clock: Callable[[], datetime], timeout_seconds=60)
async confirm(*, ticket_id, principal_id, device_id, document_hash) -> NativeConfirmation
# 既有NativeConfirmationPort完全兼容，超时0..120秒、最多一个待决定。
```

NativePrompt只在本机窗口展示账号/设备/只读范围/准确期限/挑战摘要；SHBrowseForFolder旧式无路径编辑/新建目录/拖放UI，由本人选择实际本机目录，然后MessageBox明确显示目录并点“确定”，默认按钮“取消”。没有参数路径、HTTP布尔批准或模型批准接口。绝对路径只交回本机NativeConfirmation→LocalRoots，不进控制面帧/日志。配对种类仅显示身份确认，不授root或exec；root才执行目录选择。

真实输入桌面OpenInputDesktop/GetThreadDesktop/UOI_NAME一致且为Default，锁屏/无桌面返回capability_unavailable，绝不默认批准。专属UI worker STA初始化COM，事件循环不阻塞；worker窗口所属线程独立，取消/超时/桌面变化仅向该线程窗口发WM_CLOSE，绝不自动点击确定；回收PIDL、COM、桌面和monitor。客户端CancelledError传播，业务取消/超时分别native_cancelled/category=cancelled、native_timeout。取消拒绝不落批准；source/key/账号/OS/channel/期限每100ms复查及交互后复查，源变化立刻关窗。

独立源来自可信connection registry +当前mapping +Ticket登记；current device role/key/public bytes/挑战签名document_hash检查。缺源不可用。当前RegisteredNativeChallenges适用于已独立登记/配对的只读根选择；首次账号配对bootstrap需A真实认证/挑战来源，缺失不从Windows SID/PID造UAW账号。PairingVerifier/RootSelectionPort仍保持原内部Ticket profile，未改公开pair.complete或发布配对V2。

实测：21 passed /3.02秒；m1-2.xml，Mypy workspace/Runner28源通过。原native窗口实际自动取消/超时3例，独立UI/source double单元18例明确不算真人授权；真人点击pending。m1.xml首次3失败/18通过：BrowseInfo wchar buffer未cast指针、测试Principal缺auth_session_id，均已修复，未放宽安全断言。回执ignored tests/.artifacts/D/MS-R2g。后续M2连接PairingVerifier/LocalRoots/一次消费，M3/M4接基线真实IPC/read/journal。

API依据：[微软目录选择](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shbrowseforfolderw)。这里选择旧式只读tree避免新版“新建/编辑/拖放”UI；路径及根身份仍由本机RootSource独立验证。正式安全桌面/抗其他同登录进程UI注入不作保证；不是D03部署或真人验收。
