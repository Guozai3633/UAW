# A10：原根 owner 修复与有界 current/watch 接口

2026-10-11。继续本轮 MS-I2l，不建立新共同包。准确源码由 DISPATCH 的 A10 项发布。
B 394d785、C 223c9a9 已在 A 历史内；D 最新 28850ff 已合入，原完整读取仍未接受。

## 交付审阅

B 原拥有者 Page 复用与准确构建已合入；没有新 launch/新会话接管。
真实认证 Page/当前本机实例仍缺，B78单元/36受控Chromium不算认证联调通过。
C 原 AgentToolAccess 缺口由 A 的 bind_agent_tool_facade 注入同一实际 access，
保留原 approvals/budget/executor/results/prepare/lookup；严格 runtime route 已消费。
C121单元/48 SQL是worker组件回执，不证明生产 native/模型链。
D 原工厂纯构造和私钥await后重复pass精简保留准入及其后的复查；A实际复验10项通过。
三个worker已交付部分接受为组件来源，生产第一读与模型/本人页面继续 pending。

## 原用户映射

Runner 要求 roots.mapping、bootstrap.mapping、protocol.principal_mapping 是同一对象。
第一次尝试单独接 RegisteredRunnerPrincipalMapping 被该构造约束拒绝；原11.86秒失败保留。
最终在同一 EnrolledPeerRegistry.owner 增加原 user 查询分支：

- 必须完整 Principal 等于部署固定原 Web owner（包含 auth_session_id），并等于原登记 owner。
- 当前 active enrollment、原 device、原候选双方进程/keys、原 owning native journal、双签名和期限复查。
- 关键等待后再次观察双方 OS 实例和当前角色 key；最终登记与期限核对。
- 通道 actor 分支仍匹配准确登记 actor；原 bootstrap 和原 native 共享映射不变。
- 返回重新验证的原 Principal；不复制 ctx、同名 user.id 或 caller body 作为许可。

16个实际SQL/签名组件通过（10新节点+6旧节点）；OS/native为受控输入。
原成功期望重跑77.52秒：command1/open0，已通过旧 enrolled_actor_denied 位置，
第一个 current 耗时6.673秒，后续准入 authority 仍被原响应期限取消。
尚不能证明完整修复或一次实际读取。4随机凭据、2key、child/proof pipe均清理。

## 内部 current/watch 固定契约

实现位置 src/uaw/run/runner_recheck.py，内部 Protocol RegisteredRunnerRecheckPort，
实际实现 RegisteredRunnerRechecks(commands)。不新增 HTTP/schema/RefKind/flags。

```
recheck(command_ref: Ref, *, authenticated_principal: Principal,
        channel_ref: Ref) -> RunnerAuthoritySnapshot
wait_changed(command_ref: Ref, *, authenticated_principal: Principal,
             channel_ref: Ref, deadline: float) -> None
```

command_ref 必须 content/1/实际hash、无location/access_scope；channel为现有
content/1/hash 或 connection/1，必须逐字匹配实际 device.source.channel_ref。
authenticated_principal 完整身份由原可信调用方传入，不接受 body 的 owner/approved。
10秒外层上限叠加原 command 和所有 owning 来源较早期限；不续租。

recheck 从实际 command 注册读取，要求 active、完整 pin/签名/参数/context；
RunnerCommands.collect 保留两次独立完整来源检查。查询范围包括：
原 Tool call/spec/attempt/context/dispatch；Run/task/conversation/model-policy；
当前权限链/取消、配置pointer/local_files、当前provider/角色和完整审批决定/参数/resources；
原 budget reservation/attempt/ledger 的派发/cancel/overdrawn/期限；原lease/holder/ref/fence；
当前device/channel、原Web owner/登记/双OS/key及原root/native选择证据。
最后重读 command 并检查原期限，严格输出既有 snapshot。
同一短 READ COMMITTED 连接中的每个 SELECT 仍是当前查询，不共享给子任务。

wait_changed 的输入是原绝对 monotonic response deadline，有限且不超过当前时点10秒。
首次 recheck 后每隔最多50ms开始下一次完整读取；实际查询耗时另计，
不是50ms内保证发现的实时通知。当前snapshot发生变化返回 None；任何 owning 来源
拒绝/丢失/撤销以原 DomainError 失败；外层到期 runner_watch_timeout。
返回仅表示检测变化，绝不授执行权。初版完整查询仍有成本，不能宣称解决原10秒读取预算。

14个实际SQL/签名节点通过（10新+4兼容），涵盖原ref/actor/channel/签名/审批/command/lease，
实际下一轮 Run 取消、deadline取消SQL和scope释放。此前wire optional-null、严格tuple解析、
connection Ref兼容与一次性测试hook错误均保留失败回执，修复后原断言通过。
另49个原控制SQL节点通过；D私钥await后10节点在A合入版通过。

## 接线状态与下一门槛

此接口尚未装配 D endpoint/watch，原完整 watch 继续运行；不能仅替换名字即宣称性能解决。
A仍需提供避免递归展开的逐来源批检查策略和生产适配；任何新实现须保留这里列出的
完整绑定、当前前后版本/撤销、OS/root/key检查及取消、原期限。
D不自动消费浮动A源码；只在收到准确后续修复任务时改自己endpoint/runner。

210源码严格类型与改动Ruff/格式通过。无新模型调用或用户目录读取；受控native不代真人。
未知结果保留对账，不重发 command；真实固定模型文件成果、本人页面及汇合全量仍 pending。
