# UAW Web / MS-U1

B 原 worktree `E:/UAW/.worktrees/context` / `dev/context`。开工基线 ms-i2j-start；生成物额外只读消费 A 已公开 `ms-i2j-a1 / 202544f452c485c84eb7fe08675576e31c75cad3` 的公共契约，未改共享文件或同步浮动集成分支。13个已实现路径/15个HTTP方法，含 GET/POST/DELETE `/v1/web/session`。默认使用实际会话协议；配置或后端缺失时不可用。完整 Run 执行、原请求查询及成果/核验/接受 HTTP 仍需 A 接线，不能拿 queued 当完成。

从仓库根目录运行，依赖和锁只在本目录：

```powershell
pnpm --dir apps/web install --frozen-lockfile --store-dir apps/web/.store
pnpm --dir apps/web exec node --version
pnpm --dir apps/web generate
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web test:e2e
# A 已发布的本机代理 opt-in，保留 Origin；不设置时没有代理
$env:UAW_WEB_API_TARGET='http://127.0.0.1:8000'
pnpm --dir apps/web dev
```

Node24.21.0为本工程锁定私有开发依赖，pnpm10.17.0；不改全局Node。pnpm宿主Node22.13会给engine警告，项目脚本使用本地Node24。首次浏览器安装 `pnpm --dir apps/web exec playwright install chromium`，下载在本目录 `.playwright`。Playwright运行build＋preview静态产物，控制测试端口5177；冷Vite/HMR首次导航曾超时，原失败保存。构建当前主JS727.12KB/gzip212.22KB，保留>500KB警告，尚未宣称生产性能验收。

开发入口固定 `http://127.0.0.1:5173`；显式代理只接受 A 公布的127.0.0.1:8000，changeOrigin校正API Host，Origin保留、xfwd关闭。A负责 localhost 同源静态/API、本机用户HttpOnly/SameSite会话、精确Origin、CSRF、退出失效和真实运行调度。通过A的CLI一次启动链接登录（本组件不取得用户/管理员Bearer）；code只在fragment，交换前立即history.replaceState移除，丢回应先GET session、不重放；CSRF只在内存。当前会话10秒复查，期限/撤销/身份变化清理读取投影与本地草稿分区。退出DELETE带实际X-UAW-CSRF和{meta,payload:{}}。

A可选提供可信 `window.uawWebHost`，消费同一WorkspaceHost：session()返回身份分区与实际CSRF，subscribe()通知撤销/退出/换身份，logout()做服务端失效；recovery.find(conversationId,requestId,signal)查询原任务；review.read/accept消费内部ReviewPort。不可生产挂测试fixture。默认实际BrowserSessionHost不包含尚未发布的恢复/成果适配，不猜路由。

审批先GET当前revision/hash/refs/期限再CAS；取消ACK后等待Run终态；接受前再读成果/核验/合同并校验正文UTF-8字节/SHA256，回执后查询实际Run，不直接设置completed。接受派发后未知或已确认时本视图阻止再提交；A还须提供原接受请求对账，刷新没有自动POST。前端不授予目录/执行权限。localStorage只保存草稿及conversation/request/Run查找ID，永不保存令牌、审批、预算、权限或接受状态。

分页轮询3秒，每次最多64页×100项，cursor固定watermark，走完重新取当前快照；seq/event ID、Item ID/revision去重；失效重读，循环明确失败。每次GET/POST/DELETE超时15秒，POST/DELETE无自动重试；已知Run刷新GET，未知发送缺恢复适配就阻止再次发送。未知Item只读降级，Run和审批schema不放宽。安全Markdown无原始HTML、远程图片或危险URL。

真实联调 `pnpm --dir apps/web test:live` 只连A已配置localhost页面。需环境：UAW_LIVE_WEB_URL、A给出的短期UAW_LIVE_LAUNCH_URL、UAW_LIVE_APPROVAL_CONVERSATION、UAW_LIVE_DECLINE_CONVERSATION、UAW_LIVE_CANCEL_CONVERSATION、UAW_LIVE_ACCEPTANCE_CONVERSATION。启动URL不写日志；仅内存保留测试会话cookie、不输出或存盘。缺环境exit2/pending，不计pass或skip；实际后端缺失同样pending。测试无响应截获/身份注入/LLM替身，覆盖实际发送、审批/拒绝、取消、接受及刷新。控制测试另存 `.test-results/` 和日志，不能冒充真实验收。

最终接线、准确SHA和回执在 `docs/coordination/requests/B/MS-U1-final-wiring.md`。本包不改Python、共享schema/锁、Model/Run/flags或其他worktree；整链验收由A执行。
