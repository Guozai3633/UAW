# MS-R2i 本人确认后超时：只读调用链与测量/去重提案

2026-10-11；E:/UAW/.worktrees/runner / dev/runner，D source ef609407b0875fb51c53121a31a5a56d37dab93a，handoff a448be8c5afc5f5c0f492eda074f38cf467fccbe。A第四次准确运行 e05b15801c0ef8104de740e5ef61ad03ffe92ce6；对 A 安装与登记组件用该固定 commit 的 git show 核对，不合并浮动integration、不改A。本次仅源码/公开安全回执只读审查，无生产改动、无新测试、无真人重复操作；原152/644测试不冒充本次性能测量。

## 实际结果与能定位的边界

只读 A docs/implementation/evidence/ms-i2l-native-root-visible-failure.json：本人“已经选目录并确认只读范围”，实际native_roots=1/native_decisions=1/root_grants=0；父端 native.root_selection/deadline_exceeded，child native_select/CancelledError，自有资源cleanup=true、两key已撤销、原Ticket已revoked。文件/模型调用均0，human_root_authorization_passed=false。

因此显示修复有效、本人选择/确认已有原本机证据，但没有绑定授权。native_decisions记录落盘证明写入发生，不证明 await to_thread(record) 已返回，也不能区分 root_selection 签名、final current 或 caller后续步骤。原child仅native_select不足以归咎于任一具体D方法；不要从decision自动生成/恢复grant或延长原Ticket。

## record 后实际路径

NativeReadAuthorization.select（native_authorization.py）：await decisions.record -> PairingVerifier.root_selection -> final challenges.current -> 比较完整owner/actor -> return selection。caller固定A InstalledRootSelection随后 bootstrap.connected -> auth.bind -> bootstrap.connected。

PairingVerifier.root_selection（pairing.py:207）是本机 state.get / roots.current / ProtectedSigner.sign_document(domain=root-selection) / state.get再次按新clock检查Ticket未变化 / roots.current再次检查OS目录。签名（keys.py:106）固定document快照，当前key前后lookup、OS私钥resolve与实际Ed25519；不读SQL登记源，不缓存签名权限。上述等待后Ticket/根/key复核均有必要，不能去掉或改成旧native_decision批准。

final BootstrapNativeChallenges.current（bootstrap.py:181）才再次展开D和A完整当前登记链；它既检查原本机Ticket与真实channel，也检查独立A挑战和owner，最终比较fingerprint。bind还有当前actor/owner、原持久decision/签名一次消费、当前owner再次复核和本机根校验。不能删掉最后current或bind，只因本人已经点击。

## 静态成功路径开销（不是实测SQL次数或耗时）

固定 e05b 安装 EnrolledNativeChallenges 内调用 RegisteredNativeChallenges，并且登记与mapping都为 EnrolledPeerRegistry。没有异常/取消的完整一次 BootstrapNativeChallenges.current 展开：

| 调用 | session.check | registration.current直接调用 | mapping.owner |
|---|---:|---:|---:|
| D super.current 前后两次 | 10 | 0 | 2 |
| verify_challenge 的registry.session | 1 | 0 | 0 |
| verify_challenge 的connected前后两次 | 4 | 4 | 4 |
| A独立EnrolledNativeChallenges.current | 5 | 2 | 1 |
| 合计 | 20 | 6 | 7 |

RegisteredNativeChallenges.current 自身5次check来自 registry.session、authenticated_principal、read内部session、read末尾check、自身末尾session.check。每check复核双方各1 registration.current，故20*2+6=46直接登记调用。固定A mapping.owner又调用一次current，共53次EnrolledPeerRegistry.current；该版本每current两次RunnerEnrollments.get，owner另一次get，静态约106+7=113个get方法调用。该数字不等于113条SQL、更不是第四次已完成113次；超时可能中途取消，真实读耗时/池等待必须量测。A source优化后此调用图与get实现成本应重新测量，不套用旧数。

## 建议先交的非敏感分段测量

在受控临时账号/根的 installed fixture 测量，不要求本人重复点窗：记录 monotonic 起止/总量/异常类型与原failure.code，仅固定标签，不记录Ticket/code/proof、私钥、路径或文件正文。区分 decisions.record等待、root_selection、其中credentials.resolve/state.get/roots.current、final challenges.current、caller connected、bind。A给 EnrolledPeerRegistry.current/owner、RunnerEnrollments.get 的次数/总耗时/单次最大耗时及池等待；D保留原等待后状态检查，observer不作为授权且不能延长期限。coarse native_select 和原父端deadline原样保留。

## D可审阅优化提案（尚未实现）

首选A优化实际current源的SQL/重复反序列化/往返成本，每次仍取真实当前full session/登记/owner/key/expiry，不做TTL许可cache、不跨关键await复用旧批准；A source只由A改。

若测量确认D包装重复是主要开销，D可在 ConnectionRegistry 内加入纯本机、私有的session角色快照构造；RegisteredNativeChallenges.current只获取一次注册session并保留其前check，在mapping.owner和OS identity await后执行同session后check，再从该session固定handshake的owner/actor/pairing/key/channel元数据形成原严格snapshot并比较。避免再调另两个会各自重新检查的公共registry访问器。公共read/authenticated_principal/session保持原自足校验，外部消费者不获unchecked接口。

目标单次RegisteredNativeChallenges.current从5次完整check降为2次前后check，而不是降为0或拿cache。本机ticket/channelRef/device/full主体/OS identity及原时间交集都保留；后check必须重新取当前双方角色key/撤销/进程活性和时钟，并确保session仍是原registry连接。A独立source和D fingerprint前后交集仍保留。固定图三次RegisteredNative.current可少9次session.check；预期方法调用降幅需实际新回执，不能声称等价已经成立。

落地前必须新增/复跑实际await期间owner/actor/channel替换、key/root撤销、session/原Ticket过期、进程退出/取消、错误device/schema、OS实例变化与原选择一次消费/重启journal；前后current来源变化均拒绝。不能只按调用次数写镜像测试，也不能用冻结permission快照替代真实source。具体D代码优化待分段证据，当前无已确认D业务错误，不以猜测删检查。

普通15/first90/新root最多120保持；不延长旧Ticket/grant、不开flags、不从SID/PID/body approved推权限、不代本人确认，不把真人已选择等同bind/Tool成功。第四次失败和清理保留；A先完成受控量测与自己的source优化，再决定下一次本人验收。
