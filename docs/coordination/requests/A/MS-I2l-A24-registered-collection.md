# A24：登记读取检查点的封闭来源比较

2026-10-13；准确源码与最终验收以随后DISPATCH及A24证据为准，当前实现与验证记录。
本轮只改A RunnerCommands/RegisteredRunnerRechecks/BudgetService及A测试，不改D读取执行器或worker分支。

## 问题与边界

D每个效果检查点需要前后fresh current；A原current内部又调用collect的两遍完整审批图。
这产生多层完整Run/模型/配置/角色/审批来源重复展开，原10秒reply多次超时。
本轮不删除D效果前后checkpoint/OS handle guard，不扩大reply、lease、root或更早期限。
仅优化实际封闭installed file.read装配内A的一次登记来源收集。

## 支持检测

`RunnerCommands.supports_registered_collection() -> bool` 是内部能力检查，没有公开开关。
要求实际PostgresRecordStore且checked_metadata为False；同一store上的实际RunnerDevices、
ConfigurationService、ExecutionPolicyResolver、BudgetService、ExecutionLeaseService。
根必须为原NativeRootSource，控制签名必须为原ControlCommandSigner或child InstalledControlVerifier，
签名目录和根目录同一个对象。Gate必须为A原file Gate，消费同一个root/store/config/policy。
原控制Gate的实际资源Reader必须是InstalledFileResources指向原根。
不支持的custom/替身装配仍执行原collect两遍完整图，不能借新入口跳过外部审批来源。
存在完整装配但检查期间失败不fallback；装配对象被换掉也拒绝。

## 新内部入口

`RunnerCommands.collect_registered(record, actor) -> Payload`

1. 保留原caller/command较早deadline；原记录和actor脱离引用固定，验证原已登记command记录一致。
2. 在owning current_reads/current_witness内执行一次原_collect完整审批/Run/模型/配置/权限/预算/root/lease/signature。
3. 再实际RunnerDevices.current（原通道/actor/owner/SQL）、NativeRootSource.current（原owner/read前后）;
   BudgetService.execution_state和ExecutionLeaseService.current完整复查，当前configuration再读取。
4. 原签名/current control key验证→实际native根SQLite/selection/device key/OS identity重新_read
   →原签名/current control key再验证。最终compare全部前后完整device/root/budget/lease/config，
   原record、actor及装配身份，最后再次检查所有较早源deadline。
5. 一条fresh SQL witness重新读取所有实际依赖，包括当前/历史版本、缺失/tombstone，完整schema/revision/payload
   与首次观察比较；nested同任务scope由外层统一结束，在返回authority之前关闭。结束/cleanup后再检查deadline。

没有allowed缓存、跨检查点数据复用、重复输入cache或预取locator计划。原approval request/grant/binding、Run、
模型政策与用户输入、配置、角色/provider、账号/enrollment/native journal及命令记录仍实际读取并最终比较。
不宣称SQL与OS/native跨域原子：D继续关键操作后current和本机key/handle独立guards。

`RegisteredRunnerRechecks.current` 仅对该实际装配调用此入口，原command/channel/actor完整Ref校验、
projection绑定、原命令后读取、外层full witness、10秒绝对deadline和watch语义保留。
原collect、控制端注册、通用authority与custom sources没有改为单遍，也不改变数据恢复授权。

## 独立预算/租约来源

预算组合查询与lease事务不是普通get；不能直接删第二遍检查。
本轮仍调用两次完整预算和lease current，并将BudgetService._read_state里每个joined当前row
（含不存在）接Database.observe_record。最终witness能发现最后签名等待期间会计记录删除等变化。
lease的原锁/CAS/fence、失效durable tombstone，以及budget实际dispatched/reserved/cancel/overdrawn判据保持。
不会用Record观察器替代SQL counter/预算计算或写事务。

## 验证策略与真实进度

用同一个真实Windows/Web/SQL/双key/IPC/原native证明实例，消费原审批和原Tool已dispatch的已登记命令。
只在bridge.evidence前测试metadata，然后明确抛测试停止信号，不发送command或打开文件。
比较旧collect与新collect_registered的完整结果；Root/OS/key及owning graph实际次数记录。
对抗场景在完整审批结束后的签名await内改变：原approval、Web账号、政策、lease、预算取消、
登记command、native根撤销和当前control key；RegisteredRunnerRechecks.current必须拒绝。
原current/watch/witness及custom sources继续回归；独立预算会计删除必须在final witness拒绝。

初次测量及8个变更测试的测试停止信号预期写错，修正的是测试断言；所有原失败和清理记录保留。
首次Mypy未窄化signer.directory失败保留，修正后214源码类型通过。自动权限审阅一次超时重试成功，
不将审阅超时当不安全，也没有绕过审批。测量和变更实例native/用户approve_once及模型配置为受控fixture，
当前SQL/Web/native journal/签名/OS/key/pipe是真实。不能冒充真人确认或模型质量验收。

## 最终实际回执

38不同定向节点通过：28 current/watch/witness/同图测量＋8真实变更＋2旧入口/预算会计。
578历史并集未全部重跑，481源码摘要；214源码Mypy、4文件静态/格式通过，原1691全量保持。
最初1测量失败/1通过及8变更测试失败保留，修正停止信号断言后最终通过；不多计重复节点。
原budget joined会计记录删除实际在最终witness拒绝；所有8场景均完成两次签名边界及实际来源拒绝。

| 同一原已登记命令／完整结果一致 | 旧两遍collect | 封闭collect_registered |
| --- | --- | --- |
| owning Task SQL SELECT | 360 | 231 |
| 原完整Gate审批次数 | 2 | 1 |
| native root _read | 4 | 5 |
| owning enrollment图／角色OS | 6／48 | 6／48 |
| 当前key读取 | 82 | 89 |

多出的root/key是最后签名await后的fresh本机复查，不是删权限获得的收益；预算和lease仍两遍完整检查。
样本1.211→0.936秒不能当通用生产提速，不与跨轮负载不同的完整首次链秒数做百分比。

原完整成功断言只跑一次：48.33秒，1 failed，command1/open调用1/占位1，signed_data0/ref0。
child signer总调用3，含2次native启动，较此前多一次符合执行receipt签名路径；
**没有持久签名数据，不能据此宣称receipt成功或正文可交付**。
最后current/endpoint被原reply窗口取消，原journal恢复断言未到，unknown未重发。
两次current之间不复用allowance，D效果前后fresh与handle guard保持。
19独立installed实例（原失败测量1、最终测量1、原变更失败8、最终变更8、首次链1）
4随机凭据不存在/2role keys撤销/child退出/proof关闭全部核对；按物理路径去重current别名。
只有临时测试材料，无真实用户文件、模型调用或真人操作；所有旧失败/费用/标签保留。
详细[通过及失败证据](../../../implementation/evidence/ms-i2l-a24.json)。

准确源码SHA发布后补入DISPATCH；完整首次读取、签名journal、原恢复和模型文件交付仍pending。
未获得签名journal之前，unknown保持不可用且不重发，不推not_applied/零费用或假造恢复。
BCD原交付保持无新包，A继续原来源收尾；flags/子Agent/DAG/写入安装exec保持关闭。
