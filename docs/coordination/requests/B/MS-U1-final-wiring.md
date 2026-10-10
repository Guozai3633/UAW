# B/MS-U1 最终接线与真实验证（2026-10-10）

## 固定来源与提交

worktree **E:/UAW/.worktrees/context**，分支 **dev/context**。
开工按 clean→fetch origin --tags→merge --ff-only ms-i2j-start→核对HEAD等于标签→uv sync --frozen 成功。
开工基线 **abb4590f2bfe53c601e0f6a4a3b65447ba4ec502**；独立Python环境按原锁同步，Python/锁/共享契约未改。
M1源码 **99c71df3a86b0788459f105e1bbab2e9a684491b**，阶段交接 **bec9e8c2c8fd2dcf567d38cde129c9fc8ab0037c**。
M2源码 **2093d647cb1357dd8ca4518a9afba671fb6ba2a2**，阶段交接 **41af11505d63fda2ef136234c148f7ab612f2d61**。
M3/M4首版源码 **88c6bd8dda2bf198119e92177ffa0a5c2f879e6b**；最终固定Ref/核验修订源码 **d2ece8d1682a4ae1de2ed811fc24e304e3584569**；本交接独立提交，其SHA由最终git log回执报告。

M4发现A已公开 **ms-i2j-a1 / 202544f452c485c84eb7fe08675576e31c75cad3**，立即读取其正式stage-api和公共schema/OpenAPI接入会话协议。此标签不包含B已提交阶段历史，未声称HEAD等于A1、未reset/rebase/覆盖共享文件或同步浮动integration。生成器仅用git show读取准确固定公共blob，核对标签SHA；生成物source.json保存开工基线、contract_ref/commit及两个原契约SHA256。A1的Runtime仍由A组装运行；B不复制A私有配置/凭据。

## 页面及公开组件

会话侧栏（已知/创建会话，不假装服务器列表）、后端获准目录选择固定模型、原文聊天、自适应浅色“AI理解的任务”、实际TaskFrame/Run状态、once审批/拒绝、取消、Markdown成果摘要、可选完整正文/核验/合同接受。编辑输入时显示未发送说明，不假造预理解。用户原文完整保留；理解提示不能替换它。Markdown禁原始HTML/危险URL/远程图片；未来Item仅只读降级，不放宽Run/审批或执行请求校验。桌面与390px移动版截图检查完成，输入框/发送和退出按钮在视口内，无横向溢出。

公开消费接口在apps/web：

- `UawClient(session, transport?)`：13个实际路径、15个HTTP方法，返回现有DTO；失败为ApiFailure，丢回应/坏协议为TransportError(uncertain)，读取和修改15秒超时，无自动POST/DELETE重试。除新增公开GET/POST/DELETE `/v1/web/session`，原12个用户路由不变。CLI launch不在Web取得Bearer。
- `BrowserSessionHost`：实际一次码交换、GET当前WebSession、DELETE退出。fragment交换前立即移除；POST丢回应先GET当前cookie，不重放code。身份分区为实际origin/user/auth_session_id/期限；CSRF只在内存，10秒GET复查，身份/期限/撤销清理旧投影。默认实际适配，不提供假登录。
- `WorkspaceController(client,host,drafts?,pollMs=3000)`：发送前保存非敏感requestId，已知Run恢复GET；unknown缺RecoveryPort就阻止新发。Item ID/revision保留最高版本；相同时间保留服务器顺序；Run/task按各自身份起版本边界。每批cursor固定watermark，最多64页×100；读完从当前快照继续。事件seq/eventId去重，缺序/冲突/旧cursor重新读，分页循环明确失败。无SSE，界面显示分页轮询。
- `WorkspaceHost`：可选可信host替换默认会话adapter；session/subscribe/logout，以及可选 `recovery.find(conversationId,requestId,signal):Promise<Run|undefined>`。A负责实际原请求查询协议，不用正文匹配、创建新Run或重发旧turn。
- `ReviewPort.read(artifactRef,runId,signal):Promise<ReviewSnapshot>`；`accept(snapshot,meta,signal):Promise<Result<CompletionAcceptance>>`。ReviewSnapshot消费已有ArtifactRecord/VerificationReport/Refs及正文、requiresAcceptance内部标记。默认缺适配明确不可用，仅显示Item摘要，不猜HTTP。正文校验UTF-8字节及SHA256，版本/目标/合同匹配；接受前完整重读并比较快照。等待中身份/Run/版本变化Abort；回执准确bundle pin后查询Run，不设置completed。派发后未知/已确认本视图阻止再接受；刷新没有自动POST，原接受请求对账仍须A协议。

localStorage仅草稿及conversation/request/Run查找ID；读取投影/审批/Run状态/预算/执行权威/CSRF/接受状态不持久缓存。换身份清理，旧等待不能写进新身份；页面操作不授权本机目录、flags或执行。

## A1本机接线样例

```powershell
# 在B worktree，从repo根；只改本工程环境变量
pnpm --dir apps/web install --frozen-lockfile --store-dir apps/web/.store
pnpm --dir apps/web exec node --version # v24.21.0
$env:UAW_WEB_API_TARGET='http://127.0.0.1:8000'
pnpm --dir apps/web dev # http://127.0.0.1:5173
# A运行自己的已发布后端，并交实际两分钟一次的fragment启动URL。
# B不读取/复制A credential manager内容，不代替A创建认证配置。
```

proxy只有显式设置才启用，只接受A固定loopback目标8000，changeOrigin:true修正API Host，保留Origin，xfwd:false。未设置则无代理；生产需A同源静态/API组装。A配置精确5173 Origin、独立签名密钥、HttpOnly/SameSite cookie和当前用户认证，保留CLI路径；缺来源明确不可用。退出使用A现有 `{meta,payload:{}}` 和实际 `X-UAW-CSRF`。

```ts
// A真实HTTP adapter的内部注入，不能生产挂测试fixture。
window.uawWebHost = {
  session: trustedCurrentSession, // origin/user/session/epoch有效分区；实际CSRF内存
  subscribe: onTrustedIdentityChange,
  logout: revokeActualServerSession,
  recovery: {find: findOriginalRequestRun},
  review: {read: readExactArtifactAndBundle, accept: acceptExactCurrentBundle},
};
// 不需要定制恢复/成果adapter时，不注入host：自动消费实际A1 session协议。
// 缺这两项时仍有原路由页面；unknown发送和完整成果接受保持不可用。
```

上例是签名消费说明，不是未发布服务器字段或路由。A随后补列表/原request/成果/报告/合同HTTP时，先发布公共固定契约，B/A再按已实现端点接adapter；不启用设计中尚无handler的SSE。

## 最终真实回执

| 命令（repo根） | 实际结果 | 自身ignored回执 |
|---|---|---|
| pnpm --dir apps/web install --frozen-lockfile --offline --store-dir apps/web/.store | exit0，锁一致，already up to date | install-final.log |
| pnpm --dir apps/web generate | A1固定13路径/152定义，成功 | generate-a1-repair.log + generated/source.json |
| pnpm --dir apps/web test | 33单元通过，0失败/错误/跳过 | unit-final-review.log、.test-results/unit.xml |
| pnpm --dir apps/web test:e2e | tsc/build通过，11受控Chromium通过，0失败/错误/跳过 | playwright-final-review.log、.test-results/playwright.xml |
| pnpm --dir apps/web test:live | **exit2/pending**，未运行真实5场景，不计通过或skip | live-final.log、.test-results/live-pending.json |
| 无认证 GET localhost:8000/v1/web/session，只读3秒探测 | URLError，不可达，非真实认证/运行验收 | .test-results/live-backend-probe.json |

汇总及日志SHA256 `.test-results/final-receipts.json`；所有回执都位于本worktree apps/web，自身ignored，不写共享evidence。真实suite准备5项：真实原文→理解→全文成果、审批、拒绝、取消、整份合同接受及刷新。A需要可达配置后端、一次启动URL和四个真实场景会话ID；cookie仅内存，无response截获/身份注入/模型替身，trace关闭，不打印短期URL。当前这些环境未提供且后端不可达。A1仅已发布认证；后台实际调度、成果完整HTTP、原请求恢复尚未到此组件。**11受控浏览器不是5项真实验收；SQL/LLM/Runner=未运行**。

Node24.21.0为apps/web私有dev依赖，全局Node22.13未改，pnpm10.17.0宿主engine警告保留；脚本用实际24。最终主JS727.12KB/gzip212.22KB、CSS17.00KB/gzip4.85KB，保留>500KB chunk警告，未宣称前端生产性能验收。

## 原失败、修复与未通过项

保留全部历史，不把重复跑累加数量：

1. M1注册表ECONNRESET/timeout重试后安装成功；私有Node首次bin警告后安装完成。TS7 peer冲突改锁TS5.9.3；类型生成条件anyOf/if无法表达，仅处理类型形状，运行时原schema完整。permission错误类别fixture改实际authorization，首轮3pass/1fail，修复4pass。
2. M2 fixture Ref误用model_policy/event_payload、Ref泛型和reject动作，类型拒绝后改实际policy/event/decline；M2 15pass。旧失败日志未删除。
3. M4初次浏览器7fail暴露原生fetch丢this，改箭头调用；第二次1fail卡初始/发送期间读；第三次6pass/1fail，trace显示冷Vite模块GET未完成、首次导航30秒超时。改用生产build+preview验证，不扩大行为时限、不删断言；7项全部通过。playwright-m4-01/02/03.log及playwright-history-01/02/03保留。
4. 新成果测试mock无参tuple导致tsc失败，签名修为ReviewSnapshot；playwright-m4-04.log保留。首次新增创建场景8pass/1fail，原因是“新建会话＋”可访问名称，明确aria-label修复；playwright-m4-06.log/history-06保留。
5. 修复创建后busy未清、旧身份清理、同时间消息顺序/输入框挤出视口、跨Run/task版本过滤及旧快照delta重复。新增断言覆盖，不删原断言。接受未知结果阻止本视图重发；最终复核补Ref可选content_hash与合同kind匹配，显示真实要求状态/理由/限制，33单元和11受控浏览器通过。
6. A1生成git show超过默认1MB缓冲ENOBUFS，改16MiB有界读取；main union的recovery属性类型明确WorkspaceHost。generate-a1.log/typecheck-a1.log及修复回执保留。
7. 执行工具自动审批额度曾不足，原动作没有执行；用户继续后正常批准完成，未绕过审批。没有尚待许可的动作。

当前未通过/未验：真实A后端→固定模型→完整成果链及真实用户认证/审批取消/接受回归、原未知请求及接受请求对账、服务器会话列表、SSE、本机项目授权/原生用户确认。这些是依赖接线或后续能力，未拿控制fixture、截图或queued状态替代。33/11只属于MS-U1局部组件；不标P1-10/P1整轮accepted。

## 累计修改文件及合入

只改apps/web（含独立锁/测试/生成物/README）和B requests/handoff；原Context源码/测试未改。本次累计前端文件：

```text
apps/web/.gitignore
apps/web/.npmrc
apps/web/README.md
apps/web/index.html
apps/web/package.json
apps/web/playwright.config.ts
apps/web/pnpm-lock.yaml
apps/web/scripts/generate.mjs
apps/web/scripts/live.mjs
apps/web/src/components/Markdown.tsx
apps/web/src/features/review/Review.tsx
apps/web/src/features/review/port.ts
apps/web/src/features/workspace/Workspace.tsx
apps/web/src/features/workspace/controller.ts
apps/web/src/lib/api/browser-session.ts
apps/web/src/lib/api/client.ts
apps/web/src/lib/api/generated/openapi.d.ts
apps/web/src/lib/api/generated/schema.json
apps/web/src/lib/api/generated/source.json
apps/web/src/lib/api/types.ts
apps/web/src/lib/api/validation.ts
apps/web/src/lib/cache/drafts.ts
apps/web/src/lib/events/projection.ts
apps/web/src/main.tsx
apps/web/src/styles.css
apps/web/tests/e2e/controlled/auth.spec.ts
apps/web/tests/e2e/controlled/backend.ts
apps/web/tests/e2e/controlled/workspace.spec.ts
apps/web/tests/e2e/live/workspace.spec.ts
apps/web/tests/fixtures.ts
apps/web/tests/setup.ts
apps/web/tests/unit/browser-session.test.ts
apps/web/tests/unit/client.test.ts
apps/web/tests/unit/controller.test.ts
apps/web/tests/unit/drafts.test.ts
apps/web/tests/unit/markdown.test.tsx
apps/web/tests/unit/projection.test.ts
apps/web/tests/unit/review.test.tsx
apps/web/tsconfig.json
apps/web/vite.config.ts
```

B文档：MS-U1-stage-client.md（保留M1/M2历史并补A1指向）、MS-U1-api-gaps.md（补发布现状）、本final-wiring，以及handoffs/B.md末尾新增记录。源码和handoff分开提交，旧B handoff原字节前缀保留。A审阅、合入、处理公共冲突及实际整链回归；本组件未改Model/Run/后端/schema/根锁/flags，不自动扩包。最终工作区clean后交付，本包停止。
