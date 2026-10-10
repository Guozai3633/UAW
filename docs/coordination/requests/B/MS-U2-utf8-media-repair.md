# MS-U2 UTF-8 文本成果类型修复

2026-10-10；`E:/UAW/.worktrees/context` / `dev/context`，同一已授权实际页面契约修复。

## 固定来源、连续提交

- 固定公共源 `ms-i2k-start / b7b79b150470a80f37b28fd52a2177f6de5b3124`；原 MS-U2 与首修完整保留。
- 首修源码 `3799b92b2d89ec0281e82594b1ba04f3bcfb8352` / 独立 handoff `6c7493760e969eb373e7d58f0801a36fcf2ab5ce`；A报告已精确合入 `3f67e54`，真实页面 TaskFrame、已连接与新建恢复。
- 本次源码 `106fecdbddba3656503866a45f815f1237a67ae7`；本说明和 B handoff 为随后的独立文档提交，完整交接 SHA 在最终回报与 Git 中。
- A报告真实 ArtifactRecord 为 `text/markdown; charset=utf-8`，原 Run `run-eb7af1282636488f99e6559898e0623f`。这是 A 实际观察值；B 没有读取 A token/私有配置或当前未发布源码，没有同步 worker 分支，也没有代操作真实后端。

## 修复与接口边界

只将 `checkReview` 的 media_type 精确字符串比较替换为明确的文本 UTF-8 判断。支持 `text/plain` / `text/markdown` 无参数，或唯一 `charset=utf-8` 参数；ASCII 空格/Tab、类型/参数大小写和带引号 UTF-8 值可识别。拒绝其他媒体类型、非 UTF-8（包括 utf8 别名）、未知/重复/额外参数、残缺引号/值、末尾分号、CR/LF 或非 ASCII 空白。原 ArtifactRecord.media_type 字符串不改写。

公开 ReviewPort/checkReview/HTTP DTO 签名不变；原 UTF-8 正文字节数、SHA256、固定来源记录摘要、目标/合同/报告/提案/Run Ref、合同接受与当前身份全部核验保留。没有删字段、放宽 schema/additionalProperties、假造正文或 completed。

源码改动：

- `apps/web/src/features/review/port.ts`
- `apps/web/tests/a2-fixtures.ts`
- `apps/web/tests/e2e/controlled/a2-workspace.spec.ts`
- `apps/web/tests/unit/review-media.test.ts`


## 实际验证与失败保留

| 命令（原 B PowerShell） | 回执 | 自身 ignored 文件 |
| --- | --- | --- |
| `pnpm --dir apps/web exec vitest run tests/unit/review-media.test.ts`，临时原判断/finally 恢复修复 | exit1；2 failed /1 passed，合法带 charset 成果和完整 HTTP读取失败 | `u2-media-original-contract-failure.log/.xml` |
| `pnpm --dir apps/web typecheck` | exit0 | `u2-media-typecheck.log` |
| `pnpm --dir apps/web test` | exit0；51 passed /0失败/错误/跳过，包含全部首修48 | `u2-media-unit.log/.xml` |
| `pnpm --dir apps/web test:e2e`（tsc +Vite build +Chromium） | exit0；21受控 passed /0失败/错误/跳过，包含全部首修20 | `u2-media-browser.log/.xml` |

新增3单元（正向、18种拒绝输入、完整RunDeliveryView/正文/长度/摘要/合同/Ref变化）和1浏览器不支持媒体类型拒绝。A2完整成果 fixture 默认改为 A 实际 media_type，原默认页面正文/逐项核验/固定Refs接受、未知回执/刷新/旧hash/取消/身份变化整组回归同跑；这是受控 HTTP DTO 回放，不冒充真实登录或模型质量验收。

测试最初 CRLF 字面量转义写错，造成新测试未被收集；已修复并保留 `u2-media-test-parse-failure.log/.xml` 和两份 typecheck 原失败。它们不记通过；之后在原精确判断上重现真正的两个契约失败，最终完整回归通过。首修 `u2-repair-*` 原失败/通过回执不覆盖。

目录 `apps/web/.test-results/`；新索引 `u2-media-receipts.json` 包含实际源码、所有日志/产物 SHA256。Node宿主入口 engine warning 与 >500kB chunk warning 保留：JS777.65kB /gzip223.83kB，CSS17.23kB /gzip4.92kB，无性能收益宣称。未新增依赖、改锁或全局环境。

完整真实 RunDeliveryView wire 尚未在 A 已指定回执目录出现，已请求只提供公开 DTO（不含认证信息）；因此原真实完整 wire 的逐字回放 pending。完成的回归使用固定公开完整 DTO 与 A 实际类型值；B 未执行新的真实 SQL/LLM/认证页面。A 新固定 DeepSeek 办公场景的真实页面复验与真人目录授权仍由 A 回执确认。

## 新构建摘要与 A 接线

现有 `E:/UAW/.worktrees/context/apps/web/dist` 对应本源码；A只读复制到自己发布目录，不执行/安装 B 环境。必须更新 index.html 及新引用 JS，不能沿用首修 JS。

| dist 相对路径 | 字节 | SHA256 |
| --- | ---: | --- |
| `assets/index-C59qjNr6.js` | 777654 | `0856429c7aaee7259a39f9b75208740b5e6ab6c6b1eca45f089b49ff5f877c17` |
| `assets/index-CET1bJ_O.css` | 17238 | `b60144ba2892d88f914e5132aba8fb41b916e894c32fd0ab9f6f24086842b5e8` |
| `index.html` | 411 | `0b5a1bd29fcb3899a402519dbc699df51e7a80acb2c0638c4ea99d2a37a15908` |

A精确合入本源码及后续独立交接，核对上表，再在当前 localhost 登录读取原/新 RunDeliveryView，验证 Markdown全文与逐项核验、实际合同接受和刷新原请求恢复。不改变服务器媒体字段来迎合客户端，也不放宽合同、Ref/hash、Origin/CSRF。真实页面复验未由B报告通过；P1/真人文件授权未accepted。源码/交接分别提交、工作区干净后停止同一修复，不自动扩包。
