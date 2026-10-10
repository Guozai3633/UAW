# MS-U2 固定交付等待与原请求导航修复

2026-10-10；同一已授权实际页面契约修复，`E:/UAW/.worktrees/context` / `dev/context`。

## 连续来源与精确提交

- 公共固定源 `ms-i2k-start / b7b79b150470a80f37b28fd52a2177f6de5b3124`；未同步 A 当前源码、移动分支或修改别方 worktree。
- 前源码 `106fecdbddba3656503866a45f815f1237a67ae7` / 独立 handoff `31951f6373eb25bf4c8e1759a15d0d8ae218f646`，schema 首修 `3799b92b2d89ec0281e82594b1ba04f3bcfb8352` / `6c7493760e969eb373e7d58f0801a36fcf2ab5ce`，原MS-U1/U2源码和交接均保留。
- 本次源码 `c0cd90a84cb2a64b93c5828e95a312707b51559b`；本文和B handoff 后续独立 docs 提交，交接完整 SHA 在最终回报和 Git 中。
- A准确说明：只读 `E:/UAW/docs/coordination/requests/A/MS-I2k-delivery-wait-contract.md`；A报告运行源码4c3f159，真实office正文与核验已显示。原Run `run-eb7af1282636488f99e6559898e0623f`，status=running/revision5，job delivery/waiting，保持 proposal 绑定版本。
- 真实完整来源：只读 `E:/UAW/tests/.artifacts/A/MS-I2k/m4-live-run-eb7af1282636488f99e6559898e0623f.json` 的 `delivery.result.payload`；完整输入文件 SHA256 `8fd084b06031d2db51e329995354828d98596fa53bc463651500aee8fb264c24`，前后核对一致。requires_acceptance=true、stale=false、无acceptance、proposal.run_ref.version=5、UTF-8正文及全部原固定Ref/hash有效。

## 最小行为与公开接口

Review按实际固定RunDeliveryView决定接受门槛：running/waiting_for_user，实际 delivery.run_id/proposal.run_ref.id 与当前Run匹配，proposal Run版本与当前Run.revision匹配，视图和快照都要求接受，未过时、无接受回执、无未知决定。按钮与派发前均检查，缺完整交付来源、其他阶段/终态、取消/断线/当前mutation、旧版本或未知请求保持拒绝。原决定前重读、完整sameReview、正文bytes/SHA256/源Ref与合同核验、身份/取消Abort、未知接受只查回执不换ID全部保留。公开 ReviewPort/HTTP签名不变。

CompletionAcceptance只显示接受回执并请求原Controller重新读取。UI不置Run.status/completed、不调整proposal绑定版本、不判断费用或未知效果已解决。只有实际读取的Run返回completed才显示完成；待费用/效果复查的服务器可以继续返回running。受控Chromium证明接受后/刷新后仍running，之后独立GET返回completed才更新；A真实Controller费用/unknown-effect复查属于A组合回归，本次不冒充其完成。

跨会话采用明确导航方案，不扩多请求并发存储：另一会话仍有原Recovery时，新会话草稿和原ID保留、发送仍受限；增加解释和“返回原请求会话”按钮，使用原conversationId打开，按原runId读取。导航不清Recovery、不换request_id、不重发、没有假connected。单元实跑返回原会话/再返回学术草稿，全部GET且原草稿/ID不变。独立并发发送不是本次范围，限制已在页面明示。

修改文件：

- `apps/web/replay.config.ts`
- `apps/web/src/features/review/Review.tsx`
- `apps/web/src/features/workspace/Workspace.tsx`
- `apps/web/tests/e2e/controlled/a2-workspace.spec.ts`
- `apps/web/tests/replay/delivery.test.tsx`
- `apps/web/tests/unit/review.test.tsx`
- `apps/web/tests/unit/workspace-recovery.test.tsx`


## 安全读取与回放边界

自动审批拒绝最初“将A完整真实payload写入B可提交fixture”的操作，理由是可能披露用户正文/内部成果，未明确获准持久保存到该目的地。该命令未执行。采用已批准的安全替代：真实wire只在测试内存中读取，不复制正文到仓库或日志、不输出DOM正文，回放错误统一脱敏；机器回执只保存输入文件SHA和计数。没有待审批的数据复制，也没有向A或其他聊天主动发消息。

两项独立实际wire回放验证默认HttpReviewPort的完整schema/Ref/hash、UTF-8正文以及实际running/version5交付的UI接受门槛。HTTP transport和接受receipt均受控；Run投影按A已报告id/status/revision构造。不是新的真实浏览器登录、SQL/LLM调用或真实接受派发。前一MIME交接的“完整实际wire尚未提供”由本次只读回放补齐；原历史记录不覆盖。

## 验证与原失败

全部在本worktree PowerShell运行：

| 命令 | 实际回执 | 自身ignored文件 |
| --- | --- | --- |
| 原Review `pnpm --dir apps/web exec vitest run tests/unit/review.test.tsx` | exit1；2 failed/7 passed，running门槛失败以及补完整DTO后旧要求文本断言需修正；原失败保留 | `u2-delivery-original-failure.log/.xml` |
| 原Review只读真实wire `pnpm --dir apps/web exec vitest run --config replay.config.ts` | exit1；1 passed/1 failed：完整实际源已通过，实际running接受仍禁用 | `u2-delivery-replay-original-failure.log/.xml` |
| `pnpm --dir apps/web typecheck` | exit0 | `u2-delivery-typecheck.log` |
| `pnpm --dir apps/web test` | exit0；54 unit passed，0失败/错误/跳过，含前51 | `u2-delivery-unit.log/.xml` |
| 修复后只读真实wire，同上replay命令 | exit0；2 passed，0失败/错误/跳过 | `u2-delivery-replay.log/.xml` |
| `pnpm --dir apps/web test:e2e`（tsc +Vite build） | exit0；22受控Chromium passed，0失败/错误/跳过，含前21 | `u2-delivery-browser.log/.xml` |

真实wire套件刻意独立于一般unit，缺 `UAW_REVIEW_WIRE` 会明确报未运行，不把仅收集/skip计为通过。重放命令示例：

```powershell
$env:UAW_REVIEW_WIRE='E:/UAW/tests/.artifacts/A/MS-I2k/m4-live-run-eb7af1282636488f99e6559898e0623f.json'
pnpm --dir apps/web exec vitest run --config replay.config.ts
Remove-Item Env:UAW_REVIEW_WIRE
```

回执目录 `apps/web/.test-results/`，日志/构建SHA及来源索引 `u2-delivery-receipts.json`。原 `u2-repair-*`/`u2-media-*` 原失败与成功保留，不累加回归次数。宿主Node22入口engine warning、chunk>500kB warning保留；产物JS778.37kB/gzip224.07kB、CSS17.23kB/gzip4.92kB；未改依赖/锁或声称性能收益。

## 新构建物与A接线

源码对应的ignored构建物位于 `E:/UAW/.worktrees/context/apps/web/dist`。A只读复制至自己发布目录，不安装/执行/修改B环境，核对新index和新JS引用：

| dist 相对路径 | 字节 | SHA256 |
| --- | ---: | --- |
| `assets/index-CET1bJ_O.css` | 17238 | `b60144ba2892d88f914e5132aba8fb41b916e894c32fd0ab9f6f24086842b5e8` |
| `assets/index-iNwcoO7z.js` | 778372 | `473d13c9fea6440550628c13c89a81e6446fc557a184f334087a63d7cf9cef05` |
| `index.html` | 411 | `4b02d752c7405f32b22548bbdf63fc05ce208f94bbfcd9bb2572182bcb7258d3` |

A精确合入本源码及后续独立交接，复制校验构建后，以现有localhost登录重读原Run/version5完整交付、点击实际合同接受，核对CompletionAcceptance与独立完成Controller的复查/提交。不能修改后端Run版本迎合前端，不把收到receipt当completed；费用/未知效果、取消与旧Ref真实组合回归由A负责。也复验新学术会话看到明确返回入口、草稿与原ID保留，原Run经真实终态清Recovery后才发送新任务。

真实页面接受/完成复验待A回执，真人目录授权仍pending；不标P1整轮accepted、不扩新HTTP/权限。源码/交接分别提交，工作区干净后停止同一修复。
