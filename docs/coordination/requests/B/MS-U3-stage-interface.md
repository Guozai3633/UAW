# MS-U3 M1 当前会话恢复阶段接口

2026-10-10，E:/UAW/.worktrees/context / dev/context。

基线 ms-i2l-start / 8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0：已 fetch、git show origin/integration:docs/coordination/DISPATCH.md 与远端标签准确核对；只快进固定标签，HEAD一致，uv sync --frozen成功。旧准备状态不用于停工。原MS-U1/U2及3次修复/handoff完整保留。

M1源码 8dcaeecca269c1e2a1fe434d3506745cf3eb8762。接口 WorkspaceController.start(initialId?:string)/open(id)/reconnect 保持；DraftStore 新增 select(id)，仅保存 activeConversationId 标识，不保存权限或Run/设备状态。顺序：显式URL → 同身份服务端可见的保存选择 → 服务端列表首项；原Recovery独立保留，不抢当前选择。显式不可见URL不fallback，当前principal/服务端列表/实际Conversation.id与owner必须一致；读取denied/missing清旧正文。Browser popstate重读当前URL，侧栏打开更新URL；刷新均GET。

只改 apps/web/src/lib/cache/drafts.ts、features/workspace/controller.ts、Workspace.tsx、tests/unit/u3-selection.test.ts。M1最终57单元通过（原54+3），类型检查通过。自身 ignored apps/web/.test-results/u3-m1-unit.log/.xml、u3-m1-typecheck.log；冻结pnpm第一次store入口失配无TTY退出，使用原store --store-dir apps/web/.store后锁安装成功，u3-install-store-failure.log/u3-install.log保留。原导航检查迟延但实际最终57通过；之后调整为popstate入口并重跑57，不将延迟称原测试失败。

M2计划消费本固定标签的4个登记HTTP，精确payload candidate_id/空confirmation/空revocation+CAS；新增内存 EnrollmentPort，可注入不可用来源。没有root HTTP或可信candidate launch来源时明确unavailable，不猜路径，不由网页生成native证据。A后续发布DTO/固定阶段后才接新来源。完整成果/文件Ref只来自实际RunDeliveryView，未知恢复沿原ID，不扩多Run调度。

构造：现有WorkspaceController(client,host,drafts?,pollMs?)；关闭stop()/logout()保留。URL成功例start('conv-visible')；拒绝例start('conv-hidden')不打开首项；重复刷新start()/reconnect()不POST；原Recovery仍显示返回原请求入口。当前阶段不是实际本人配对/目录/成果接受或P1产品接受。M1交付后继续M2-M4，不等待A合并。
