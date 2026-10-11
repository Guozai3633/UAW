# A9 当前开发接口与接线状态

2026-10-11。A继续自己已发布 A8 后的 integration HEAD。A9组件源码由ms-i2l-a9-source固定，准确SHA见DISPATCH；没有自动派发D修复包。worker 保持原 A8 快照，只有收到明确任务和准确新阶段SHA才同步，不消费浮动 integration。

## 文件管理与准入

- `ConfigurationService._profile` 增加闭合 `tool.installed.readonly/1`：local、无任意 endpoint/credentials、仅 file.read、USD、16384字符/65536返回字节。
- `FileProviderConnectionAcceptance.accept(admin, provider, meta)` 需要管理员和原 revision；默认无 availability 拒绝。实际来源为 `InstalledFileAvailability`，不接 caller 的 connected/approved。登记默认 disconnected，接受只变 provider，不激活配置或开 flags。
- 开启 local_files 的 validate/activate 需一个准确 conversation + 一个 workspace、唯一 active 只读 provider，以及实际当前原生命周期/账号/设备/根/原签名证据。默认其他能力仍不可开启。关闭不依赖仍存活的本机来源。
- `InstalledFileRunSources.admit(tx, actor, run, binding, configuration)` 在原提交事务内固定 `FileRunSourceBinding`；无文件范围保持普通 Run，不添加 capability；有范围但缺实际来源整笔提交失败，不留下伪成功 Run。固定原用户会话、Run/task/conversation、配置与用户显式模型、provider、launch、workspace/device、根证据摘要和原期限，无 native path/正文。
- `current(ctx, workspace)` 重新核对原 Run/模型/配置、管理员当前开关、原实例/root/device。原来源对象只用于一致性比对，不是权限缓存。`assemble_installed_file` 的生产 route 在已装配 `container.file_run_sources` 时调用它；A8 默认组件来源构造保持兼容。

## 原审批所属服务

`RoutedApprovals(registry, ledger, tuple[ToolApprovalRoute(tool_ref, provider_ref, service)])` 需要1–128个明确、唯一、完整工具 hash/provider 的原 ApprovalService。所有服务的实际 store/configuration 与原 ToolApprovalAuthority/registry一致。

request 按实际 ledger action/spec/参数摘要选服务；get/decide/recheck 从持久 ApprovalBinding 的原完整 context/action 选择，不接受 caller provider/service。新会话不能接管旧审批；保留原用户决定、expiry、当前权限检查；缺 route 不 fallback。办公后台已消费该路由，HTTP 通过 ApprovalPort 注入，不再强绑某个办公具体 service。

## 消费 C 阶段

C最终源码223c9a9963414bdc1ae71d3e723224d0958ab63c、D最终源码acd7bd9d10387566c634b87d99fe3c01c165f618、B最终源码394d78579bb6841bd936b11af557bc401d0b2dba已按准确提交合入A。未操作worker分支或工作区。组件合入不等于产品整链通过。

`bind_agent_tool_facade(original, registry, access)` 复制原独立 ToolInvocation，仅绑定实际 AgentToolAccess，保留原 approval/budget/executor/results/prepare/lookup/reconciler。

`assemble_agent_runtime(..., tool_routes=factory)` 的可信 factory 收到该 Agent 的准确 access；须用上述函数给每条原 facade 注入同一个 access，再返回 C 的 ToolRuntimeRoute tuple。C 负责严格路由校验；A observations 以 ToolResultReadPort 消费 routed.read_result。没有改 C 实现或其分支。

每Run混合runtime、原文件fragment进入低信任Context、原观察来源进入成果核验以及审批/用户接受所属服务路由已实现，实际文件与模型产品链验收仍继续，不把签名正确的ToolResult当任务通过。

## 当前回执与限制

初轮新增SQL：6通过、2失败，失败源是测试使用不合法空ScopeSelector，已修输入，旧日志/xml保留。随后23个不同SQL节点通过，涵盖办公提交/审批/拒绝/接受、READ COMMITTED当前来源以及新增管理配置/Run准入/审批路由；原门禁/生命周期12个SQL节点通过。48个单位节点以及25个来源/清理回归节点分别通过。

最新定向回归：a9-current-command-http.xml 的55项SQL通过；a9-bridge-current.xml 的12项SQL/真实双进程IPC通过；a9-file-evidence.xml 的21项SQL通过，包括6个最新当前peer/通道节点、7个原材料引用/低信任读取节点和原审批/开关来源。以上有重叠，按节点去重，不求和冒充新全量。208源码严格Mypy与189文件格式检查通过；运行源码及A新测试Ruff通过。只检查src/uaw的Mypy命令会漏Runner源码类型，错误日志保留；同时传入两个实际源码目录后通过。通用contracts历史文件有466项Ruff格式/风格错误，此轮未整片格式化，契约生成/校验另验。

原Windows双进程文件链失败回执a9-native-chain及source2至source12全部保留。source12运行103.47秒，发送原command 1次、文件打开0次，返回ipc_broken；随机4凭据/2角色key/原子进程/proof pipe均清理。source8的runner_device_changed已定位两端session expiry毫秒差，改为同一原登记期限（不晚于任一session）并通过真实SQL/签名的双方来源比对及撤销测试。source12仍受原30秒lease/10秒响应中的重复来源展开影响。注册后没有等待的重复collect已精简，实际完整读链仍未通过。具体A/D修复边界见MS-I2l-A9-D-original-read-budget.md。不延原期限、不缓存授权、不重发unknown、不把受控native作为本人确认。

A localhost后台8000及B最终构建5173已启动；匿名同源/v1/web/session正确401。构建私有复制与B三文件摘要一致，没有修改B工作区。computer-use当前浏览器清单没有原拥有者页面，因此不能把新ticket/新会话配旧本机launch_id冒充B认证只读通过。尚未建立新本人实例；B真实认证来源继续pending，准备顺序见MS-I2l-A9-B-authenticated-readonly.md。

没有自动开启 flags，没有新用户文件正文或模型调用，没有新 native/接受操作。本页仅组件接线约束，不是新整轮验收或worker开工授权。
