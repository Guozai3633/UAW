# UAW Web / MS-U2

正式开工固定 `ms-i2k-start / b7b79b150470a80f37b28fd52a2177f6de5b3124`。B worktree `E:/UAW/.worktrees/context`，分支dev/context；保留全部MS-U1提交/handoff。本组件默认消费实际A2服务器会话分页、原request_id RecoveryPort、RunDeliveryView全文/逐项核验/合同接受，不需要测试host。生成物固定读取该标签公共契约：18路径/21方法/169定义，完整运行时校验；不改共享schema或Python锁。

从仓库根运行，依赖/锁/构建/浏览器/回执均在本目录：

```powershell
pnpm --dir apps/web install --frozen-lockfile --store-dir apps/web/.store
pnpm --dir apps/web exec node --version
pnpm --dir apps/web generate
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web test:e2e
# A已发布loopback入口，显式opt-in；不设置时无代理
$env:UAW_WEB_API_TARGET='http://127.0.0.1:8000'
pnpm --dir apps/web dev
```

本地锁Node24.21.0，pnpm10.17.0，全局Node22.13未更改（pnpm宿主engine警告保留）。脚本使用私有Node24。浏览器安装`pnpm --dir apps/web exec playwright install chromium`仅下载本目录.playwright。Playwright受控project运行build＋preview5177；开发实际入口固定5173，代理只接受127.0.0.1:8000，changeOrigin修API Host、保留Origin、禁xfwd。A负责配置用户级HttpOnly/SameSite会话、精确Origin/当前CSRF、后台固定Model/Agent及管理员已登记工具；本组件不读A私有配置/model key/admin token，不开放flags或授予目录。

登录使用A提供限时一次fragment启动URL，交换前移除fragment，丢回应先GET session、不重放code；CSRF和cookie会话仅内存/HttpOnly。当前身份10秒复查、退出DELETE撤销；身份换源清理投影和草稿分区。原文为基准，TaskFrame摘要仅提示；未发送无真实理解时明确说明，不改写原文或解析模型文字猜completed。

默认列表来自服务器，固定cursor水位、过期重读、循环拒绝、同ID最高版本；新登录可读本人历史，接受权限由当前服务器复查。分页每操作最多64×100项，3秒只读轮询，Item/revision及Event seq/eventID去重，Run/task独立版本边界。无SSE。读取/修改15秒超时，POST/DELETE不自动重试；未知turn保存原查找ID，刷新先查原request_id/Run，不正文匹配或新发turn。missing lookup仍不确定，不能因为404猜未执行。

ReviewPort默认真实HTTP：读取完整RunDeliveryView，校验Run/Ref/version/可选hash/位置/scope、正文UTF-8长度/SHA256、合同/核验/提案关联；404表示尚无结果。接受前再读当前完整快照，stale/已有receipt/取消或其他当前操作均禁发。POST仅准确固定bundle_ref/artifact_ref/accept及RequestMeta，无expected_revision/If-Match。服务端回执后只查实际acceptance和Run，不设completed。

接受发送前仅持久run/request/bundle/artifact查找ID，最多32条，同身份刷新后仍对账；不保存accepted状态/权限/正文/审批/hash/预算/token。未知回应无actual acceptance时阻止换ID重发。只有匹配实际receipt清查找；新Bundle不自动替代未知旧决定。换身份/退出清理查找分区，当前服务器再次核验原auth_session_id。存储不可用时合同决定明确不可用。安全Markdown禁HTML/危险URL/远程图片，未来Item只读降级，执行和审批schema不放宽。

可选`window.uawWebHost`仅为可信正式adapter：session/subscribe/logout，可选recovery/review；不注入时全部默认A2适配。受控测试用响应截获，不能生产挂fixture，不能证明SQL/真实模型或真人授权。

验证分开：

- `test`：必要单元；`test:e2e`：受控Chromium，真实格式fixture。
- `test:backend`：当前真实TCP后端的匿名401/页面拒绝/刷新零POST，只读，不作为登录后任务通过。
- `test:live`：A提供localhost页面、短期UAW_LIVE_LAUNCH_URL和真实审批/拒绝/取消/接受会话ID后，才运行真实登录任务5场景。缺环境exit2/pending，不记pass或skip；无response mock/identity注入，cookie只在内存，不落trace/secret日志。模型费用和真人文件授权另归A/用户留回执。

ignored回执`.test-results/u2-*`，最终来源/计数/失败历史和接线见`docs/coordination/requests/B/MS-U2-final-wiring.md`；MS-U1历史见该目录MS-U1-final-wiring.md。主chunk>500KB构建警告保留，不宣称生产性能验收。本包只改apps/web及B文档，A审阅合入并执行整链回归；本包交付后停止。
