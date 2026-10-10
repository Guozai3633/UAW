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


## M2 阶段交付（继续M3/M4）

实际M1源码42ad508d3d98e703a51bff3d522bf2bbecdf169c；M2源码88bb0f33a86560a5bce89421e84f1f75cb7d3a09，同固定基线/分支。新增NativeReadAuthorization，修改PairingVerifier/LocalRoots和LocalState的私有可选checked CAS，D integration lifecycle与原native fixture增加可选延后确认。

```python
NativeReadAuthorization(*, native: WindowsNativeConfirmation,
    challenges: RegisteredNativeChallenges, verifier: PairingVerifier,
    signer: ProtectedSigner, device_key: DeviceSigningBinding, roots: NativeRootSource)
async select(ticket_id: str, *, expected_revision: int, code: str,
             proof_signature: str) -> RootSelection
async bind(selection: RootSelection, workspace_ref: Ref) -> None
async revoke(root_handle: str, *, expected_revision: int) -> None
```

所有state/roots/source/mapping/confirmation须同一可信组装；select仅针对已有root Ticket，对其角色key/私钥持有/原签名挑战和真实native adapter复核。owner/actor来自registry + mapping，不接受主体/path/能力布尔参数。输出旧RootSelection是opaque handle/有界期限/原内部签名profile，不改公开PairComplete DTO或控制面协议。bind消费既有RootSelectionPort/NativeRootSource，持久CAS一次；重复或版本冲突拒绝。revoke用当前live channel完整owner与登记grant匹配后revision CAS，阻止当前RootSource读取；无owner不撤销其他主体的根。

PairingVerifier的SQLite/根IO移到worker，交互后再读取Ticket/current key、原本机根身份；批准CAS在事务内重新取时钟且检查协作取消，取消完成后回收worker，不使用UI前期限。LocalRoots拒绝根或祖先reparse/link，绝对路径仍仅本机数据库。

阶段82 passed /23.07秒（原native root/persistent pairing＋9个新生命周期节点），补checked CAS后30 passed /13.58秒。m2.xml/m2-2.xml、原m1错误保留；Ruff通过、Mypy29源通过。真实IPC双进程/OS凭据/SQLite/根验证，与肯定UI替身明确分开；pending真人交互、A生产认证/挑战登记/首次配对bootstrap及组装。继续M3/M4，不能以阶段成功开放用户项目或flags。


## 最终接口补充（M3/M4）

`WindowsNativeConfirmation(..., local_roots: LocalRoots | None = None)`：root交互必须显式注入与PairingVerifier/RootSource同一LocalRoots，缺省不可用。其内部WindowsNativeDialog返回本机NativeDirectoryDecision(path, identity)，选择时捕获实际目录st_dev/st_ino、最终明确点击后复核；确认adapter将这一固定identity写入本机LocalRoots并在源await后再检查，不向公共NativeConfirmation新增字段。替身UI也必须显式返回该typed结果，不能给Path/True冒充真实身份。

NativeReadAuthorization增加本机NativeDecisionJournal（与LocalRoots同库），保存原Ticket文档和完整owner/actor/session/origin channel固定Ref，重复不同内容冲突；bind复核持久原确认主体与当前mapping，重启或新channel不能借同user ID换auth session绑定。记录是确认来源证据，不缓存当前权限，原key/root/channel/authority/期限/取消仍逐次查询。source monitor成功结束时等待在途current检查，不以task.cancel误关闭正常IPC；实际取消/超时仍取消监视并拒绝批准。

人工脚本和状态见 MS-R2g-human-native-guide.md；命令缺 --run-human 只输出pending，无native批准。新真实批准对人的验收仍未运行。
