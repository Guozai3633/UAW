# A26：原审批决定在同源 Run 括号内校验

2026-10-13，继续 A25 发布 HEAD；仅 A 保留源码和测试，不操作 B/C/D 分支。

## 原因

签名后的 current 仍重新展开完整审批图。ApprovalService.recheck 的两段事务读取各自
解析 Run/政策/配置；中间 Tool authority 再解析同一套来源。每次效果检查点又在本机操作
前后各调用一次。大量递归检查让原 10 秒回复期限耗尽，尚未产生持久回执。

本轮保留原 request、decide、get 及到期封存；仅实际只读 file Gate 使用独立的
InstalledFileDecision.recheck，不改通用审批协议，不缓存授权，不放宽任何期限。

## 内部接口与装配

`InstalledFileApprovalAuthority.checked_action(action_id, ctx, *, check=None) -> JsonObject`

current 仍返回相同 ApprovalCreateRequest；新可选回调在已有角色/Run 前后校验之间接收
脱离引用的原 action request 和 RunSourceSnapshot。必须返回 None，错误和取消直接传播。
原 ledger、registry、resources、config/policy/access 对象关闭等待后必须未被替换。
回调仅元数据，不能执行工具、读正文、注册授权或等待用户确认。

`InstalledFileDecision.recheck(approval_ref, request, ctx) -> ApprovalGrant`

实际同源 PostgresRecordStore / ConfigurationService / ExecutionPolicyResolver / RunToolAccessSources，
原 InstalledFileApprovalAuthority 及有观察根的 InstalledFileResources 才可使用；缺来源直接拒绝。
原 OriginalFileApprovalGate 和 child InstalledToolApprovalGate 在原 native root bracket 内装配；
无根观察的入口继续原 ApprovalService 和 ToolApprovalAuthority，不自动 fallback。

```text
原 get：当前到期/取消检查及必要的持久封存
 → 原 request/binding/ctx/version/status 比较
 → fresh 同句 SQL：approval/binding/grant/Run/budget/admission/conversation
 → 当前 approval policy
 → 角色/Run 前后来源括号
    → 原固定 action/spec/Resource Reader
    → 原决定和来源全部谓词校验
    → fresh 同句 SQL 再查全部决定记录 + policy 再查，完整结果比较
 → Run/固定模型/权限、角色/provider 收尾复查
 → 最外层 fresh 完整 SQL witness（当前/历史/absence/tombstone）
 → 原对象/认证/ctx/较早期限再查 → 返回原存储 grant
```

保留原作用域、原动作/参数/资源、已批准版本、Run 活跃状态、预算取消、原较早期限、
固定与当前配置的审批政策、manual 模式、政策 rules 不可用、完整 permission scope。
审批创建/用户决定写事务、事件、锁和 CAS 保持。只读收集不持 conversation lock 等待 Resource Reader，
真实取消能在等待期间提交。完整记录组读每次 fresh SELECT，不是快照授权缓存。

SQL witness 提供一个比较点，不是跨 SQL/native 的原子执行授权；比较点之后的 SQL 改动
由下一个独立 current 检查点拒绝。测试明确展示此边界。关闭等待期间内存 authority、
认证、ledger 或 registry 替换在返回前拒绝。D 原效果前后 current/key/native/handle guards 不变。

## 实际测量与验证

原审批 SQL 元数据图结果完全相同，SELECT 83→51。
同一 installed 根内原两类 Gate（control、child 类在 parent 测量）结果相同：
已合并角色图 SQL 128→96；root2/owner2/owning2/OS16/key28 不减。
同一个原已登记命令完整结果相同：SQL221→189；Gate1/root5/owning6/OS48/key89 不减。
这些是受控 metadata 试验，不发送命令，不证明子进程效果链或通用耗时比例。

首次 45 SQL 用例通过；补齐 ledger/registry 关闭期间替换边界后 47 SQL 复跑通过。
拒绝场景覆盖 cancel、decision、binding、grant、mode、expiry、policy、role，
原 Reader 拒绝/取消、较短 caller deadline、关闭期间 authority/authentication/ledger/registry 替换。
原 generic 审批锁/等待/决定、资源以及同源 action 请求测试继续通过。
最终 installed 和原首次读取回执在证据中独立记录；不把组件通过当首次链成功。

最初 no-any-return 类型失败与格式/静态准备失败修复，原实际运行回执保持。
仅受控临时材料、native/SQL 决定及模型配置；真实 SQL/OS/key/签名/IPC 保留。
没有新 LLM、用户文件或真人确认/接受；flags/checked_metadata/子Agent/DAG/写入安装exec关闭。
BCD 原交付保留，本轮无新 worker 包。详细最终回执见
[A26 证据](../../../implementation/evidence/ms-i2l-a26.json)，准确 source 随 DISPATCH 发布。

## 最终结果与未完成边界

53 个不同定向节点通过：47 SQL＋2 metadata installed 对照＋4 原审批/账号/native/key 实际撤销。
215 源码类型、7 文件静态与格式通过；603 历史并集未全部重跑，486 源码摘要固定。
最终源码对照结果如上，SQL 减少不代表通用生产耗时收益或完整首次链通过。

原成功断言初次 46.80 秒失败，单独最终复跑 53.83 秒仍失败，所有失败保持。
初次原 command 只发送一次，打开/读取和 receipt domain 签名各完成一次，第五检查点完成，
第六检查点（签名验证后、signed CAS 前）被取消。该实例运行时另有独立 metadata 试验，
不能用总耗时和最终实例做因果提速比较。

最终复跑发生在其他试验结束后。仍只有 command1，打开/读取/receipt 签名各完成一次；
第五检查点开始时 child 原回复窗口剩约 2.013 秒，第二次 fresh current 以 ipc_closed 结束。
这次不是在 trace 中直接看到 child deadline 到零，不能将 IPC 关闭一律解释成 child 自身超时。
父控制端返回 invocation_interrupted；下步需要核对父/child 原回复窗口和关闭传播的衔接。
两实例一次使用占位各 1，持久 receipt_data/ref 均 0；原字节及 journal 恢复断言未到达。
内存签名不等于持久可恢复交付。unknown 未重发，不推 not_applied 或零费用。

8 个独立 installed 临时实例（2 metadata 对照、4 撤销、2 首次链）随机凭据移除、双方 key 撤销、
子进程退出和 proof pipe 关闭全部核对。原 10 秒/15秒/90秒/30秒/120秒及较早期限不延长，
无真实用户材料、外部模型或本人操作。完整首次链与 MS-I2l 产品验收继续 pending。
A 自己继续父控制端截止/原来源复查至持久恢复链；BCD 本轮没有新接口或新包，不自动同步。
