# B/MS-U2 最终接线与回执（2026-10-10）

## 固定来源、阶段与最终提交

worktree **E:/UAW/.worktrees/context**，分支 **dev/context**。DISPATCH正式发布与远端
ms-i2k-start精确核对，准确基线 **b7b79b150470a80f37b28fd52a2177f6de5b3124**。
clean/fetch origin --tags/merge --ff-only/HEAD==tag/uv sync --frozen成功；MS-U1全部历史、
独立handoff保留。不reset/rebase/stash，不改其他worktree，不跟随浮动integration。
本基线已含A2六个实际HTTP和已合入前轮组件；A当前私有配置及凭据没有读取或复制。

| 阶段 | 源码 SHA | 独立阶段说明 SHA |
|---|---|---|
| M1固定A2客户端/服务器分页/ports | fe68599a46bdb7df8d896a073776c6f64cd5c081 | 2c3ac0e152011c7db557e1c42581c7f869fa7566 |
| M2默认全文/恢复/实际接受读取 | 98976199fbde10cf96816751a43cfd4b7aea9cd4 | 75952a2aec4a47ba94966d673ebf8b46daa3d747 |
| M3/M4最终恢复/竞争/验证 | **ab14fe3063d4a1e781196aeab8a81e452cd5f207** | 本final-wiring及B handoff另行提交；准确SHA由git log/最终消息给出 |

生成器固定读取正式标签公共schema/OpenAPI，核对commit，source.json保存源文件SHA256。
实际18个路径/21个HTTP方法/169个reachable定义，类型形状清理无法表达的条件，运行时
Ajv仍保留原条件/required/additionalProperties，不放宽执行或审批DTO。共享schema/后端/
Python锁/Model/Run/flags和Context源码/测试无改动。

## 默认真实客户端与端口

原A1客户端、cookie/内存CSRF/15秒超时、{meta,payload}保持；新增A2实际方法：

| 客户端 | 实际HTTP与准确输出 |
|---|---|
| conversations(cursor?,signal?) | GET /v1/conversations，limit=100/固定cursor → ConversationPage |
| lookup(conversationId,requestId,signal?) | GET /v1/conversations/{conversation_id}/turn-requests/{request_id} → 原RunRecord |
| delivery(runId,signal?) | GET /v1/runs/{run_id}/delivery → RunDeliveryView |
| artifact(id,version?,signal?) | GET /v1/artifacts/{artifact_id} → ArtifactRecord |
| content(id,version,content_hash,signal?) | GET /v1/artifacts/{artifact_id}/content → ArtifactContentView |
| acceptDelivery(runId,{bundle_ref,artifact_ref,decision},meta,signal?) | POST /v1/runs/{run_id}/delivery/acceptance → CompletionAcceptance |

默认BrowserSessionHost之后直接注入 **HttpRecoveryPort / HttpReviewPort**，不需要测试
window.uawWebHost，不给缺来源造空成果或假登录。可选可信host仍兼容，未给recovery/review
则自动使用上述真实adapter。A已有后台固定Model/工具登记决定是否执行，B不启用flags。

```ts
const client = new UawClient(trustedCurrentWebSession);
const recovery = new HttpRecoveryPort(client);
await recovery.find(conversationId, originalRequestId, signal); // only original lookup
const review = new HttpReviewPort(client);
const snapshot = await review.read(artifactRefOrUndefined, originalRunId, signal);
// snapshot.artifact/content/report/bundleRef/contractRef/requiresAcceptance + exact delivery
// delivery preserves contract/report/proposal, each fixed Ref, stale and actual acceptance.
await review.accept(snapshot, requestMeta(), signal); // guarded by fresh UI read, current session
// immutable bundle_ref/artifact_ref; no expected_revision/If-Match; read receipt and actual Run
```

HttpRecoveryPort missing→undefined，只意味着尚无原回执，不意味着未执行；其他错误保持
实际失败。WorkspaceController刷新先查原request_id/已知Run，然后读历史；unknown不
正文匹配或新发turn，只有实际原Run归属匹配才能恢复。已知Run取消ACK不当终态。

HttpReviewPort read保留完整RunDeliveryView及各源，复核Run归属、artifactRef与请求pin、
合同/报告/提案/目标关联，UTF-8字节/SHA256正文，和源Ref可选parameter_hash摘要。
摘要使用已发布Python sorted UTF-8 JSON域，含Unicode/整数元数据的实际Python黄金
摘要验证；Bundle含执行上下文不在Web返回，不伪造Bundle正文重算hash。位置/scope
若请求pin提供则完整复核。老正文/报告hash、错目标/合同、stale明确拒绝新决定。

accept消费真实view，缺view/过时/已有决定/不要求接受拒绝；UI在点击前重新GET并比较
完整快照，变更/取消/身份/其他当前操作触发Abort，服务端最终锁复查。当前会话Principal
若可得，则回执主体必须与当前会话一致；跨登录可读历史，旧会话接受由A2明确拒绝。
结果回执后只重新查询实际acceptance/Run，**页面不设置completed**。

## 页面与用户状态

侧栏改为实际服务器分页、刷新，跨登录重新从当前服务器读本人历史。分页固定水位，
每操作最多64页×100，同ID最高revision，cursor过期重读第一页、循环明确失败。
每页await后guard当前identity/generation；旧读不能落入新身份。Item/Event/Run/task
原版本去重和3秒分页轮询保留，当前A2无SSE。原文保持，不假造未发送AI理解；实际
TaskFrame摘要仅作提示，不能覆盖用户原文。

成果默认全文显示及逐项要求文本/状态/理由/限制/引用、检查依据、原合同目标和实际
接受决定。404/missing是尚无完整结果，仅可读条目摘要或等待，不当completed/新任务。
“读取当前成果与接受回执”按钮及3秒只读查询用于显式恢复；无结果、旧hash、实际拒绝
保持可见。Markdown禁HTML、远程图片、危险URL，未知Item只读降级。

未知接受在dispatch前仅保存 **runId/requestId/bundleId/artifactId**查找（最多32项），
不保存接受状态、Ref/hash/正文、审批、预算或权限。同identity刷新恢复该查找，实际
GET delivery没有acceptance时仍不确定：**不换request_id重发**，新的bundle也不能自动
替代原未知决定。只有匹配真实receipt清查找；接收到POST回执仍先保留查找到GET确认。
明确ApiFailure拒绝可以清查找，TransportError/Abort/坏回执/等待保留；UI也不自动重试。
存储不可用则决定明确不可用，避免发送后刷新丢对账。换身份/退出清理查找分区。
localStorage其余只保留非敏感草稿及conversation/request/Run查找ID，无model key、admin
Bearer、CSRF/审批/执行权威/接受状态。当前权限、用户会话、cancel/终态仍归服务器。

取消和接受竞争：当前cancel/其他操作或“正在停止”禁用接受，等待期间相关状态变化Abort；
服务器取消赢得竞争时显示实际cancelled及拒绝，不把HTTP成功/模型文字猜completed。

## 本机运行与真实联调要求

```powershell
# 自己的B worktree repo根
pnpm --dir apps/web install --frozen-lockfile --store-dir apps/web/.store
$env:UAW_WEB_API_TARGET='http://127.0.0.1:8000'
pnpm --dir apps/web dev # 127.0.0.1:5173；A的精确Web Origin
# A提供两分钟一次fragment启动URL；不读A配置/keyring/主凭据。
```

Vite只在上述显式变量存在时代理固定127.0.0.1:8000，changeOrigin校正Host，保留真实
Origin、xfwd关闭，不新增服务器路由。backend/read-only project也用实际5173，A后端
由A持有；B没有启动/停止或修改A后端/数据库。子测试自己的preview由Playwright自动收尾。

真实登录任务准备5场景：办公原文→实际TaskFrame→RunDeliveryView全文及逐项核验、
审批、拒绝、取消、合同接受，并逐场刷新不重发。真实suite不route截获、不注入identity，
使用A一次launch，cookie仅内存，trace关闭、不输出/存盘一次码及主凭据。
实际TaskFrame/Delivery响应与页面逐项对比，不用“没有占位符”替代全文或真实理解。
环境：UAW_LIVE_WEB_URL、UAW_LIVE_LAUNCH_URL、UAW_LIVE_APPROVAL_CONVERSATION、
UAW_LIVE_DECLINE_CONVERSATION、UAW_LIVE_CANCEL_CONVERSATION、UAW_LIVE_ACCEPTANCE_CONVERSATION。
未提供时test:live exit2/pending，不跳过并计通过。该请求已通过用户输入工具提出，当前
未收到实际一次launch和场景ID。原真实file/native账号根流程仍由A/D/用户确认，B不
自动点击批准、不用路径授权，也不从旧回执冒充真人本轮授权。

## 真实验证回执（分类独立，不叠加重跑）

| 命令/场景（repo根） | 最终实际结果 | ignored自身回执 |
|---|---|---|
| pnpm --dir apps/web generate | 固定18路径/169定义成功 | .test-results/u2-generate-m1.log + generated/source.json |
| pnpm --dir apps/web install --frozen-lockfile --offline --store-dir apps/web/.store | exit0，锁一致/Already up to date | u2-install-final.log |
| pnpm --dir apps/web test | **44单元通过**，0失败/错误/跳过 | u2-unit-final.log、u2-unit-final.xml |
| pnpm --dir apps/web test:e2e | **19受控Chromium通过**，tsc/build通过，0失败/错误/跳过 | u2-browser-final.log、u2-browser-final.xml |
| pnpm --dir apps/web test:backend | **1真实TCP后端匿名拒绝通过**，0失败/错误/跳过 | u2-backend-browser-final.log、u2-backend-browser.xml |
| pnpm --dir apps/web test:live | **exit2/pending**，5登录后场景未执行，不计pass/skip | u2-live-01.log、u2-live-pending.json |

均在本worktree apps/web/.test-results；准确源码SHA、原日志SHA256及XML计数在
**u2-final-receipts.json**。最终source上述ab14fe3；截图u2-full-delivery.png是受控fixture，
u2-real-anonymous.png是实际后端无cookie页面，两者分别目视检查，不能互称真实任务。
匿名实际API401、真实Failure展示、零POST/DELETE、刷新仍禁执行，仅证明匿名边界；
不是登录/Model/Runner/真人验收。实际无认证探测8000同样401，u2-backend-probe.json。
没有读取或复制A私有配置/credentials，SQL/LLM/Runner任务本包未运行。

Node24.21.0本工程私有依赖，pnpm10.17.0宿主Node22.13 engine警告保留；最终构建主JS
745.04KB/gzip215.46KB、CSS17.23KB/gzip4.92KB，>500KB chunk warning保留，未宣称
生产性能通过。独立pnpm锁无依赖新增，冻结安装真实通过。

## 原失败与未完成门槛

M1首轮类型拒绝错误假设Contract/DeliveryProposal有id，按实际无id DTO删假设；随后
测试transport tuple无参却索引参数，修测试准确签名。u2-typecheck-m1.log及
u2-typecheck-m1-repair.log保留，最终typecheck通过；未放宽schema或删断言。
本包最终各组件/受控/匿名suite无失败/错误/skip。原MS-U1失败与handoff全部保留，
没有重做其已接受组件或把37→42→43→44以及11→19重复验证累加成验收总数。

登录后真实任务5场景、真实固定模型费用/质量、真人文件选择/首次设备配对、文件→成果
整链仍pending，缺launch/场景来源不冒充通过。本包只交MS-U2局部组件；A审阅接受、
处理公共冲突/合入、接当前后台及跑整链/汇合全量。旧1691或A的真实ASGI模型回执不是
本包真实页面验收。P1整轮/MS-I2k全量未因此accepted；不开放flags/DAG/exec/安装/写入。

## 本包实际改动文件

只允许apps/web及B requests/handoff；Context暂停，其他session路径无修改：

```text
apps/web/README.md
apps/web/package.json
apps/web/playwright.config.ts
apps/web/scripts/backend.mjs
apps/web/scripts/generate.mjs
apps/web/scripts/live.mjs
apps/web/src/features/review/Review.tsx
apps/web/src/features/review/port.ts
apps/web/src/features/workspace/Workspace.tsx
apps/web/src/features/workspace/controller.ts
apps/web/src/lib/api/a2-adapters.ts
apps/web/src/lib/api/browser-session.ts
apps/web/src/lib/api/canonical.ts
apps/web/src/lib/api/client.ts
apps/web/src/lib/api/generated/openapi.d.ts
apps/web/src/lib/api/generated/schema.json
apps/web/src/lib/api/generated/source.json
apps/web/src/lib/cache/acceptance-lookups.ts
apps/web/src/main.tsx
apps/web/src/styles.css
apps/web/tests/a2-fixtures.ts
apps/web/tests/e2e/backend/anonymous.spec.ts
apps/web/tests/e2e/controlled/a2-workspace.spec.ts
apps/web/tests/e2e/controlled/auth.spec.ts
apps/web/tests/e2e/controlled/backend.ts
apps/web/tests/e2e/controlled/workspace.spec.ts
apps/web/tests/e2e/live/workspace.spec.ts
apps/web/tests/unit/a2-adapters.test.ts
apps/web/tests/unit/controller.test.ts
apps/web/tests/unit/review.test.tsx
apps/web/tests/unit/u2-recovery.test.ts
docs/coordination/requests/B/MS-U2-stage-client.md
```

最终本文件及handoffs/B.md增量另提交，历史原字节前缀保留。工作区clean后交付，本包
停止，不自动扩包/下一包；真实launch到达可由用户/A明确继续本包联调。
