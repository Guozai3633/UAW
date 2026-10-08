# 下一轮可直接转发的任务

日期：2026-10-08。共同标签 **ms-i2e**，实际代码提交和公共摘要见 [DISPATCH](DISPATCH.md)。B/C/D 的上一包已接受；用户已确认以下三个包同时开工，固定基线继续 ms-i2e。A 正在执行 MS-I2f1，详细范围见 requests/A/MS-I2f1-scope.md。

每个 session 在自己的原 worktree 开工。A 没有代为切换分支或向其他聊天发送消息；将对应代码框内容发给原 session 即可。

## 发给 B：MS-C4

```text
开始UAW Session B下一包MS-C4：上下文纯计算有界缓存。
目录E:/UAW/.worktrees/context，分支dev/context。MS-C3已由A接受，原15项真实SQL已通过；两处Ref/Windows测试兼容修复保留在集成分支，请包含它们。
工作区干净后git fetch origin --tags，然后git merge --ff-only ms-i2e；核对HEAD与ms-i2e^{commit}一致，按uv.lock同步本worktree独立环境。失败先报告，不reset/rebase或单独覆盖公共文件。
先读docs/coordination/DISPATCH.md、docs/coordination/requests/A/MS-I2e-next-packages.md第2节、docs/plan/sessions/B.md及PARALLEL_WORKFLOW.md。精确允许路径以B页为准；本包新增src/uaw/context/cache.py归B。
保持GenericModelInputs与TokenCounter现有公开签名，只缓存已完成当前校验的数据的格式化/序列化/token估算；每次当前authority/Reader/scope/epoch/规则/工具/窗口/取消及最终复查保留。键覆盖实际完整内容/元数据、主体/Run、固定模型/权限、预留与算法版本。进程内条目/字节有界，返回不可变或副本，容量零关闭。不能缓存访问许可、旧Reading或模型输出，不跨主体共享，不宣称provider prompt cache或Token收益。
验证相同输入纯计算次数减少、正文/分类/规则/工具/窗口改变、撤销/取消、容量与变异隔离；保留原Context单元/SQL回归。SQL测试模块名与单元测试不同。缺数据库URL如实记录待A实跑，不复制A私有配置/凭据。
只修改B允许目录；不改shared/schema/锁/composition/API/Model或其他worktree。公共缺口提案交B requests。本包是局部组件，不把P1-02或P4-04整轮标accepted。
源码与交接分别提交，工作区干净后报告实际基线、SHA、修改清单、真实回执、可选注入/关闭示例和A接线要求；不自动开始下一包。
```

## 发给 C：MS-T2c

```text
开始UAW Session C下一包MS-T2c：统一工具核对入口与明确outcome读取。
目录E:/UAW/.worktrees/tool，分支dev/tool。MS-T2b已由A合入，97单元＋43真实SQL全部通过。A仅修复同名测试收集冲突，将SQL文件改为test_tool_reconciliation_postgres.py；原handoff保留。
工作区干净后git fetch origin --tags，然后git merge --ff-only ms-i2e；核对HEAD与ms-i2e^{commit}一致，按uv.lock同步独立环境。失败先报告，不reset/rebase或覆盖公共文件。
先读docs/coordination/DISPATCH.md、docs/coordination/requests/A/MS-I2e-next-packages.md第3节、docs/plan/sessions/C.md及PARALLEL_WORKFLOW.md。
在C目录实现可选ActionReceiptLookupPort.find(action_id,ctx)->Ref|None；从独立已登记原attempt来源查找实际固定回执，查找不是权限，生产实现由A接。ToolFacade.reconcile严格消费现有ReconcileRequest，返回既有RuntimeToolruntimeReconcileResult；默认缺Lookup/Reconciler不可用，额外receipt_ref拒绝，绑定仍交ToolReconciler核对。恢复入口不走新执行_access，而是当前恢复数据权限。补read_outcome(action_id,ctx)->实际ToolReconciliationReceipt，重新核对来源/证据/绑定。confirmed和核对ok不等于applied、工具成功或Task完成。
保留效果/费用独立、unknown额度、原attempt与固定费用计划；不新建attempt、不reserve/dispatch/retry，不扩EffectRecord或公共请求。pending增量预算规则和orphan会计协调仍由A处理。
真实SQL覆盖查找/无来源/缺port/跨主体attemptprovider/重复重启/撤销取消恢复/明确未应用与费用独立，保留现有43项SQL。新SQL模块与单元模块不要同名。缺连接如实报待A实跑，不复制凭据。
只改src/uaw/tool及C测试/requests/handoff；不改shared/schema/锁/composition/API/其他worktree。不开flags或目录，不注册受控Reader为产品能力。源码与交接分开提交，报告实际SHA/回执/接线样例；完整MS-T2仍等待，不自动扩大范围。
```

## 发给 D：MS-R2c

```text
开始UAW Session D下一包MS-R2c：签名终态回执持久journal。
目录E:/UAW/.worktrees/runner，分支dev/runner。MS-R2b已由A接受；根ExecutionLease服务已进入基线，但不是实际执行权限。
工作区干净后git fetch origin --tags，然后git merge --ff-only ms-i2e；核对HEAD与ms-i2e^{commit}一致，按uv.lock同步独立环境。失败先报告，不reset/rebase或覆盖公共文件。
先读docs/coordination/DISPATCH.md、docs/coordination/requests/A/MS-I2e-next-packages.md第4节、docs/plan/sessions/D.md及PARALLEL_WORKFLOW.md。
在D目录定义可选ReceiptCommandReaderPort，从独立登记源读取固定RunnerCommand/device/owner，不能从receipt或命令请求体自证权限。实现内部publish(command_ref,receipt_data,authenticated_principal)->实际固定Ref和read(receipt_ref,authenticated_principal)->RunnerReceipt；主体来自可信适配器，默认无Reader不可用。
复用真实Ed25519 receipt域、当前device key角色与撤销、RunnerProtocol现有command/attempt/Usage/action/资源校验。只保存ok/failed/cancelled终态，waiting明确不支持。开发SQLite按owner/device/command/attempt唯一保存，实际版本1，相同已验证内容去重，不同内容冲突，不覆盖历史；当前源/签名/数据权限每次复查，恢复不新准入。
真实签名与本session临时SQLite验证重启、新进程/并发、冲突/越权/撤销/固定Ref摘要及取消后的原回执恢复。SQLite是组件journal，不决定D01。不得从admission生成receipt，Runner ok不直接映射Tool applied，failed/cancelled不推断not_applied或零费用。
只改D允许目录；不改shared/schema/锁/composition/API/其他worktree。不接IPC/配对V2、不签发假执行回执、不开放安装写入exec、不自行决定D03。源码与交接分开提交，报告实际基线/SHA/回执/Reader与持久化接线例子/缺口，完整MS-R2继续等待。
```

## A 的下一包与合并安排

A 执行 MS-I2f：实现实际设备/通道归属与不可变命令登记，发布当前权威和恢复读取契约，再组装 policy、配置、审批/预算、根、lease/fence 及撤销。通用 Context authority、真实回执来源、可信 IPC/OS 凭据和实际执行仍需逐项接线。

A 收到任意一个包即可审阅、合入和回归，不必等待三个同时完成。开发中的 session 保持固定 ms-i2e；新公共契约只在包边界同步。完成后用户转交报告，A统一发布接受结果与下一基线。

## 2026-10-08 开发中补充

工作包定义源是 `planning/parallel_catalog.py` 的 PACKAGES；session 页定义可写路径；`MS-I2e-next-packages.md` 定义 B/C/D 当前输入输出与策略。A 本轮首个子包的详细范围见 [MS-I2f1-scope](requests/A/MS-I2f1-scope.md)。

D 的当前说明勘误：journal 返回已有 `content` Ref；`runner_receipt` 只是命名空间，不能新增私有 RefKind。无需中途换基线。
