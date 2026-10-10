# MS-R2i 根选择窗口：第三次真人失败后的只读审查

2026-10-11；E:/UAW/.worktrees/runner / dev/runner。同包消费者修复，不派新包、不增加等待上限。原 MS-R2i 和本次窗口修复源码、失败、清理记录全部保留。

A 第三次尝试（2026-10-10 UTC 13:58:06–14:00:22）本人反馈没有看到目录选择窗口。只读核对 E:/UAW/tests/.artifacts/A/MS-I2l/m2-native-root-attempt-3.log 的允许诊断字段：failed_phase=native.root_selection，父端 failure_code=deadline_exceeded，native_human_confirmed=true，root_selected=false，model_calls=0。首次账号确认不证明根确认；A报告无文件读取且自有资源已清理。父端超时不能定位子端 UI 前失败，也不能继续归因于本人选择太慢。

## D 显示窗口前的实际调用链

1. helper_host.py:75 执行可信 application.on_connected；固定 A3 InstalledRootSelection 先复核 bootstrap/当前登记，再签发独立原 root Ticket、使用当前设备受保护私钥签原 pairing-proof，调用 helper.authorization()/auth.select。D 不发行生产 Ticket，不从网页 body/path/approved 取权限。
2. runtime.py:206 构造 BootstrapNativeChallenges、WindowsNativeConfirmation、PairingVerifier 和 NativeReadAuthorization。LocalRoots/签名目录/owner mapping/state 实例必须一致；缺失或不一致拒绝。
3. native_authorization.py:104 select 首次 current 校验，root/device/key 与固定 helper 一致，ProtectedSigner.check_private 后进入 PairingVerifier.approve。
4. pairing.py:101 approve 复核 pending/revision/principal、当前原 root key，并验证原 Ticket.document 的真实 pairing-proof；不合法的证据在 UI 前失败。
5. native_confirmation.py:168 confirm 先执行 checked（同文件127）：独立当前 source、原 document_hash、完整 owner/actor/current channel、key 角色与撤销、原 Ticket/当前期限、实际 OS instance。BootstrapNativeChallenges.current（bootstrap.py:181）还与 A challenge/source 交叉复查。这些 await 完成前没有创建 UI worker。
6. 通过后才启动 to_thread(WindowsNativeDialog.show)。native_dialog.py:108 先 guard 当前桌面/取消/期限，CoInitializeEx STA 成功后，root 使用 SHBrowseForFolderW（170），选择后才 MessageBoxW（196）再次确认只读授权。桌面/COM失败、来源变化、过期与取消均拒绝；不通过模拟 Yes 修复。

目前只读审查未定位到可由证据确认的 D 业务错误；没有修改上述权限、UI或签名代码，没有再延长时间。现有实际 native 自动取消/超时测试证明退出和资源排空，不能证明用户看到窗口。147 项测试中的肯定 UI 仍是明示 fixture，不能替代本人根确认。

## A 下一次诊断输入与停止条件

A 已在自己的 InstalledRootSelection 增加私有 phase/error_type/failure_code 诊断，并在父端 connected 后消费现有 helper failure/closed 事件。请交准确消费者 SHA、对应 phase/error_type/failure_code 与自有资源清理回执；保留当前 deadline_exceeded，禁止打印原 verification_code/proof、凭据或目录。

D helper_host.py:79 在 on_connected 的 DomainError 路径已返回原 failure.code，finally disconnect；非 DomainError 由 host 顶层返回 dependency_protocol_invalid 并关闭。父端只轮询 grant 会掩盖这一路原失败；应先收取现有事件，而不是新增批准输入或重发未知命令。若诊断停在 checked/source/private proof，交实际源停止码；若停在桌面/COM，交原 unavailable；只有证明实际进入窗口却不可见后，才有据审查显示行为。

缺具体子端失败证据的根授权仍 unavailable/pending。A 负责本人操作与生产源消费；D 不访问用户目录、不自动点击，不将首次账号确认、SID/PID、通信成功或 UI double 当根授权。原签名 journal/重连恢复规则、15/90 启动上限、默认60/可信新root最多120、旧 Ticket/grant 更早期限、flags和D03均保持。

## A 新定位回执（同日后续）

A tests/integration/agent/test_installed_pre_ui.py 使用独立web-platform测试账号与实际InstalledHelperAssembly/SQL/OS/IPC，受控根对话仅返回 diagnostic_reached_native 拒绝，不读文件。m2-root-pre-ui-trace-fixed.xml 1通过/49.821s（pytest49.91s），原120秒session内110秒诊断预算确实到达目录对话；首20秒诊断失败不能作为D UI前业务错误证据，中间fixture冻结字段失败也由A保留。真人仍未看到窗口。

当前 native_dialog.py 的 BFFM_INITIALIZED 回调只处理取消/期限，没有请求前台/显示提醒，MessageBox亦未带前台显示选项。后续限定补自有原生窗口显示与提醒，不替本人选择/确认、不增加期限，不改变来源校验；具体源提交/实际native可见与取消回执另交。Windows前台请求可能被系统拒绝，不能据此保证本人已见/已确认；需实际本人重验。
