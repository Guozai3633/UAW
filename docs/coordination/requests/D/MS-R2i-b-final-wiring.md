# D MS-R2i-b：阶段与最终接线回执

2026-10-11。D自身可验证项交付，**完整A8 FileTool→installed helper原读链仍未通过，等待A来源/接线**。不发布生产权限或整包accepted，不自动下一包。

## 固定版本与改动

工作区E:/UAW/.worktrees/runner；dev/runner。原HEAD484e0c1b1e680c73f739313bdd134ece18830716干净，fetch origin --tags，git show origin/integration:docs/coordination/DISPATCH.md核对正式续包；执行快照ms-i2l-a8 /06ff3ef56b68d391387bc7b154fa58ecb00571f9，源码ms-i2l-a8-source /16e0efaf6daff2fbbd0281473a8c6cc1f652d0e6，固定任务文档ms-i2l-a8-followup /610a920d9cc83900f056b0eb2ccfaf13cb122ff8均与远端一致。只快进准确A8标签，HEAD精确等于标签后uv sync --frozen通过64包；原start不移动，未reset/rebase/stash/浮动合并。

M1源码3f660f69fc2d8aaa7885aed51e76e03e0ff1ceef/阶段cfac57bf7535c426650a383d82057ecc92c7561f；M2源码c1c081fb5d159b72d0e34277dd3f9f0b3656ddf0/阶段dea2c08c5054c5b87b3343f33f85b260d9ed396e；**最终源码acd7bd9d10387566c634b87d99fe3c01c165f618**。最终文档/独立handoff另提交。

运行代码只改D helper_host.py、runtime.py、ipc/windows_pipe.py。D测试：installed_file_fixture/child、test_installed_file_sources/chain/boundaries、test_helper_idle、counted_recovery_child/test_original_journal_recovery、unit/test_pipe_idle。D requests阶段/本页与独立handoff。workspace四文件不需变更。无新公共DTO/RefKind/依赖；shared/HTTP/锁/A composition/factory/control端/Tool源码未编辑，7个公共基线文件hash逐一相同。

## D内部行为与构造

`PipeConnection.wait_readable(*, deadline:float)->float`仅在原session monotonic expiry前PeekNamedPipe等首字节；不读文件、不缓存权限，不把普通用户审批空闲当断帧。ReadOnlyHelper.serve_once仍原构造与签名：首字节后总bootstrap/完整frame/endpoint响应受min(首字节+原10秒, 原会话expiry)约束，超时统一ipc_timeout。不能续租或绕过cancel/roots/role/key/lease/fence。Windows OS操作off-thread，取消drain原句柄，256KiB与10秒/15秒/首次90秒/root120秒及所有较早source期限保留。

回执已发送后helper_host等待对端明确关闭/退出、own stop或原session expiry，期间不读取/执行新帧，不授许可；解决控制端尚在verify/current source时server过早disconnect竞态。没有新增ACK wire或透明重发。新连接仍新Ref，unknown不能再command。

实际A8测试构造仍 `async with installed_file_case(web,tmp_path,monkeypatch) as p`，原空payload HTTP→真实browser owner/SQL session→原InstalledHelperAssembly/protected proof/双keys→原callback/ticket/native journal/root→assemble_installed_file。`p.approve()`调用原FileTool facade等待并对原SQL ApprovalService作**受控fixture用户决定**，`p.bindings.tool.facade.invoke(p.raw,p.ctx)`保留完整approval/budget/dispatch/command/attempt/model/provider。该成功期望节点在固定A8真实失败，不能当已执行。真实receipt应由 `p.bindings.tool.receipts.read_observation` 独立查原登记source并验证当前data权限；D不手工签发假回执或用admission生成receipt。

只有新fixture Run之前建立测试provider active元数据、local_files测试版本及implemented availability；所有其他flags关闭，固定旧Run/config/model不改。没有注册生产fixture、网络模型调用或用户目录。

## 实际验证与耗时

最终不同节点并集 **42通过，0失败/错误/跳过**（只指三份定向最终XML，不包括未通过的A8完整链）：

| 回执 | 不同节点 | 实际CLI/ XML秒 | 范围 |
| --- | --- | --- | --- |
| final-regression.xml |34|97.43 /97.392|受影响IPC/原签名/取消/并发/重启恢复；含7调度单位节点与真实双进程|
| boundaries.xml |7|533.39 /533.375|真实A8 Web/SQL/Windows双keys/helper等待后的根/key/角色撤销、stop、Run cancel、policy版本、较早期限|
| m1-final.xml |1|70.33 /70.319|最终实际A8来源/原选择签名，factory source query测量|

Ruff通过、37文件format、Mypy34源码通过、diff检查通过。没有重跑旧695/1691全量。节点按classname/name去重，阶段13/4/6回执与重试不累加。SQL8个原instance每个4随机protected handles缺失/2role keys撤销/own process退出/proof pipe关闭，zero command/open；54不同保留IPC namespace回执cleaned=true。无本包自有helper进程剩余，D数据库55435保留供明确后续测试，不删库/其他session库。

M1初次来源节点48.86秒，callback ready44.821秒/child callback35.428秒/assembly1.084秒；最终含factory指标：new Run fixture setup1.086秒、ready65.008秒、assembly1.591秒、清理0.649秒；parent查询2346次/7.181秒，child查询14339次/29.024秒。7边界ready62.497–67.245秒，assembly1.360–1.544秒；等待释放后拒绝0.010–6.032秒。边界parent查询3400–4851次，child13904或14339次；按namespace与每phase原始值在source-costs.json。部分测试与D组件回归并发，不把这些时间当独占生产性能；源查询秒是各调用累计，不能与wall time相加为总elapsed。

测量从parent新Run fixture setup计时及后续get，从child factory.create首query开始；SQL put/transaction不是这些get成本计数。budget reserve/dispatch、lease acquire、command register/collect、bridge source、signed exchange、child authority/signature/journal均有逐方法计数/耗时钩子；没有到达的阶段标未到达，**不能说0费用/成功**。phase/namespace/error只记录有界metadata，不记录绝对目录/proof/key/正文；private-cleanup locator仅ignored自有临时状态。

## 原失败与A待接线

完整读链原m2-4.xml/log仍 **1失败+1teardown错误/130.24秒**，facade返回ipc_timeout/Connection expired during source await；未收到原真实FileContent、未验证Tool业务结果或预算结算。此前53.24秒D遗漏implemented availability已修；59.00秒空闲误断管已修。stage-interface记Record字段/LocalState.get调用的D错误与修复；m2-3中断无XML不记通过，4遗留own credentials已准确SQL-key匹配删除，2keys撤销，最后仅其两个随机SQL主体rows清理。m2-4恢复审计确认随机RootGrant.owner namespace凭据0残留/2keys revoked，原CancelledError不改成正常清理通过。审计初次win32cred import不可用按已有pywin32-ctypes修正，无新依赖。原Mypy单文件调用缺MYPYPATH import-untyped失败，最终正确source path34通过；所有修复前失败仍保留。

原组件受影响第一次regression1失败/28通过/74.42秒：server发receipt立即disconnect与client最后current check竞争；D已修，reply-fix4通过31.10秒、最终含同一失败节点的34通过。13个最后边界47.86秒包含实际断帧10秒/超长、回复关闭、重启恢复，不能与34重复累计。

A具名需求见MS-R2i-b-stage-read-chain.md：降低原完整来源/审批重复查询的耗时但保持固定指纹和当前前后复查；InstalledLifecycle.finally清理不要再次cancel own task、done/异常可靠drain；固定A8 child RunnerCommands缺真实gate/control verify（当前构造None），需注入原审批/当前签名来源；A生命周期需消费真实receipt事件，原control关闭后允许可信的新连接/原根证据与原journal恢复，而非再次用户确认/再次command。

D **受控注册/native/authority的组件链**实跑actual hidden Windows read/真实签名journal：故障在消费适配器丢已到签名回复，随后本session文件改变并新进程/新connection Ref恢复；回执内容/hash/usage/Ref逐字保持原值，actual WindowsReadHandle仅构造1次，发送kind仅command一次/recover一次，取消source下也无新admission/read。原双进程并发/once/replay/timeout源与签名撤销回归通过。该组件真实journal不冒充A8 installed原FileTool全链或真人配对；真实A8预算/lease/Tool成功与丢回复恢复继续pending。

## 验证入口和后续门槛

`. ./ops/start-dev-db.ps1 -Session D`；准确URL仅127.0.0.1:55435/uaw_dev，alembic upgrade head。`pytest -q --require-postgres tests/integration/runner/test_installed_file_sources.py tests/integration/runner/test_installed_file_boundaries.py` 实际分两份XML执行。`pytest -q tests/unit/runner/test_pipe_idle.py tests/integration/runner/test_helper_idle.py tests/integration/runner/test_original_journal_recovery.py tests/integration/runner/test_windows_read_ipc.py`加4个原helper/runtime与6个原post-signature节点，见final-nodes.json准确名单。各自basetemp位于ignored本session artifacts，原日志/XML都保留。

A接源码后仅受影响消费者回归；先交准确允许消费的固定源码标签与真实审批/签名/重连输入，D再恢复原成功期望节点，不合浮动integration。没有native本人弹窗或代点批准；真人根/页面/FileTool实际链/固定模型成果验收均由本人及A另实跑，标pending。写入安装exec/生产flags关闭，不决定D01/D03/D06。
