# MS-U3 M1 当前会话恢复阶段接口

2026-10-10，E:/UAW/.worktrees/context / dev/context。

基线 ms-i2l-start / 8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0：已 fetch、git show origin/integration:docs/coordination/DISPATCH.md 与远端标签准确核对；只快进固定标签，HEAD一致，uv sync --frozen成功。旧准备状态不用于停工。原MS-U1/U2及3次修复/handoff完整保留。

M1源码 8dcaeecca269c1e2a1fe434d3506745cf3eb8762。接口 WorkspaceController.start(initialId?:string)/open(id)/reconnect 保持；DraftStore 新增 select(id)，仅保存 activeConversationId 标识，不保存权限或Run/设备状态。顺序：显式URL → 同身份服务端可见的保存选择 → 服务端列表首项；原Recovery独立保留，不抢当前选择。显式不可见URL不fallback，当前principal/服务端列表/实际Conversation.id与owner必须一致；读取denied/missing清旧正文。Browser popstate重读当前URL，侧栏打开更新URL；刷新均GET。

只改 apps/web/src/lib/cache/drafts.ts、features/workspace/controller.ts、Workspace.tsx、tests/unit/u3-selection.test.ts。M1最终57单元通过（原54+3），类型检查通过。自身 ignored apps/web/.test-results/u3-m1-unit.log/.xml、u3-m1-typecheck.log；冻结pnpm第一次store入口失配无TTY退出，使用原store --store-dir apps/web/.store后锁安装成功，u3-install-store-failure.log/u3-install.log保留。原导航检查迟延但实际最终57通过；之后调整为popstate入口并重跑57，不将延迟称原测试失败。

M2计划消费本固定标签的4个登记HTTP，精确payload candidate_id/空confirmation/空revocation+CAS；新增内存 EnrollmentPort，可注入不可用来源。没有root HTTP或可信candidate launch来源时明确unavailable，不猜路径，不由网页生成native证据。A后续发布DTO/固定阶段后才接新来源。完整成果/文件Ref只来自实际RunDeliveryView，未知恢复沿原ID，不扩多Run调度。

构造：现有WorkspaceController(client,host,drafts?,pollMs?)；关闭stop()/logout()保留。URL成功例start('conv-visible')；拒绝例start('conv-hidden')不打开首项；重复刷新start()/reconnect()不POST；原Recovery仍显示返回原请求入口。当前阶段不是实际本人配对/目录/成果接受或P1产品接受。M1交付后继续M2-M4，不等待A合并。


## M2 已交付（继续 M3/M4）

源码 d35725b0899c17b8df67581a18ac8e9b3dead0a0；固定 ms-i2l-start 22paths/25methods/181defs。新增 client.enrollment/beginEnrollment/confirmEnrollment/revokeEnrollment 精确原四HTTP，正文请求仍{meta,payload}，空确认/撤销payload及expected_revision，无browser approved/proof/native或新root路径。

内存端口 HttpEnrollmentPort(client,source?:EnrollmentSourcePort,storage?:Storage) 实现 locate/read/begin/decide/uncertain；可信主机可注入 window.uawWebHost.enrollmentSource 或完整 enrollments port，默认缺source首次登记明确unavailable。source.current(signal)只返回原candidateId/enrollmentId（非权限）。read('原登记ID')返回经公开schema和原owner验证的实际状态；decide(old,'confirmation'|'revocation',signal)先读原ID、精确proof/revision和原deadline，再空body+CAS派发。未知只保存原lookup IDs和基准revision，不保存nonce/proof/keys/status/permission；重新查询同ID无新POST。pending不是授权，active也不授予目录。Devices组件初次读取/关闭/身份变化均Abort；复用现有cookie/CSRF，仅内存身份。

完整成果原严格链保留；来源及核验Ref显示精确版本/摘要/定位，不由路径文字创造根权限。没有root HTTP、没有新launch/current locator DTO；公共缺源不猜API，A新固定阶段到达再接。

63单元通过（原57+6），类型/build通过；回执 apps/web/.test-results/u3-m2-unit.log/.xml、u3-m2-typecheck.log、u3-m2-generate.log、u3-m2-build.log。独立阶段构建已保存 apps/web/.test-results/u3-m2-dist/，每文件SHA256在 u3-m2-build-manifest.json；A只读复制该阶段构建，不执行B环境。阶段不是真人配对/目录/接受或整轮accepted，继续本包M3/M4。
