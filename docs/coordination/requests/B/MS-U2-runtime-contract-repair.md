# MS-U2 运行时契约修复交接

2026-10-10；B 原 worktree `E:/UAW/.worktrees/context`，分支 `dev/context`。

## 实际来源与提交

- 固定公共来源 `ms-i2k-start / b7b79b150470a80f37b28fd52a2177f6de5b3124`，18 路径 / 21 方法 / 169 reachable definitions；未同步 A 当前未提交源码或改公共契约。
- 本修复前 HEAD / MS-U2 独立 handoff `0b6d9edf9646a38bb8deb56b2cbdf21b65761bfc`；原最终源码 `ab14fe3063d4a1e781196aeab8a81e452cd5f207` 完整保留。
- 修复源码 `3799b92b2d89ec0281e82594b1ba04f3bcfb8352`；本文件和 B handoff 后续独立提交，准确交接 SHA 在最终回报与 Git 中。
- A 请求只读来源 `E:/UAW/docs/coordination/requests/A/MS-I2k-B-runtime-contract-repair.md`；原失败 `E:/UAW/tests/.artifacts/A/MS-I2k/m4-original-event-schema.json`，SHA256 `d545a0e909c37387e08778338003f390228251e638ac4688fc97b272432b83fd`，未修改原回执。

## 最小修复与公开接口

生成器删除整个递归 `clean`：直接保留固定源的说明元数据、properties 中业务字段定义和全部运行时约束。`OutputSpec.description` 恢复为实际公开类型与验证字段；没有放宽 additionalProperties、忽略非法事件或改变 HTTP/DTO/RecoveryPort/ReviewPort 签名。类型投影原有 if/then 条件处理保留，运行时 169 个定义逐项 deep-equal 固定源，包括嵌套注释和名称映射。`generated/source.json` 固定来源摘要没有变化。

实际 HTTP200 `task.frame.committed` 原 wire 只复制其无凭据业务正文到 B fixture：保留用户原文、3 个 output_specs.description、原 task/input/semantic Ref。测试同时验证 HTTP envelope 与 TaskFrame，拒绝额外字段和数字 description。这是 A 实际失败正文的受控回放，不是 B 新执行 SQL/LLM/生产登录。

历史错误时原控制器仍阻止新建/发送，顶栏“重新读取并连接”不受 connected 门槛限制。单元回放实际事件和 Chromium 受控测试证明：坏历史拒绝 → GET 合法重读 → 恢复已连接和真实 task/run 投影 → 新建可用，不重发原 turn，不 POST 控制/审批，不伪造 completed。因此生产控制器/页面无需改动。

源码修改清单：

- `apps/web/scripts/generate.mjs`
- `apps/web/src/lib/api/generated/openapi.d.ts`
- `apps/web/src/lib/api/generated/schema.json`
- `apps/web/tests/e2e/controlled/backend.ts`
- `apps/web/tests/e2e/controlled/workspace.spec.ts`
- `apps/web/tests/fixtures/a-runtime-task-frame-event.json`
- `apps/web/tests/unit/controller.test.ts`
- `apps/web/tests/unit/generated-contract.test.ts`

## 验证与原失败

在本 worktree PowerShell 实跑：

| 命令 | 实际结果 | 自身 ignored 回执 |
| --- | --- | --- |
| `pnpm --dir apps/web test -- tests/unit/generated-contract.test.ts`（修复前） | exit 1；47 项中 2 failed / 45 passed；包含原44回归，未计为通过 | `u2-repair-original-failure.log/.xml` |
| `pnpm --dir apps/web generate` | exit 0；固定 18 路径 /169 定义 | `u2-repair-generate.log` |
| `pnpm --dir apps/web typecheck` | exit 0 | `u2-repair-typecheck.log` |
| `pnpm --dir apps/web test` | exit 0；48 passed /0 failure/error/skip | `u2-repair-unit.log/.xml` |
| `pnpm --dir apps/web test:e2e`（包含 tsc + Vite build） | exit 0；20 受控 Chromium passed /0 failure/error/skip | `u2-repair-browser.log/.xml` |
| PowerShell 原 pnpm 入口重复 generate，比较三份生成物 SHA256 | exit 0；字节一致 | `u2-repair-generate-repeat-fixed.log`、`u2-repair-generation-deterministic.json` |

所有相对回执在 `apps/web/.test-results/`；索引及每份日志 SHA256 在 `u2-repair-receipts.json`。新增 4 单元、1 Chromium，计数采用本次最终覆盖，不累加历史运行。

附加辅助检查首次从 Python 子进程解析到错误的 `pnpm.cmd`（11.25.0），被工程 engines 拒绝，未生成产物、未改变锁；原辅助失败日志 `u2-repair-generate-repeat.log` 保留。使用原 PowerShell pnpm 10.17.0 入口重跑成功。未安装/更改全局版本。常规命令入口仍有宿主 Node22 engine warning，pnpm 脚本使用已有锁定 Node24；构建 chunk >500kB warning 保留。JS 777.53kB /gzip223.75kB、CSS17.23kB /gzip4.92kB，无性能收益宣称。

## 已构建产物与 A 接线

已交付产物 `E:/UAW/.worktrees/context/apps/web/dist`（ignored、与本修复源码匹配），A 可只读复制到 A 自己的发布目录，不运行 B 依赖或修改 B 目录。每份 SHA256：

| dist 相对路径 | 字节 | SHA256 |
| --- | ---: | --- |
| `assets/index-CET1bJ_O.css` | 17238 | `b60144ba2892d88f914e5132aba8fb41b916e894c32fd0ab9f6f24086842b5e8` |
| `assets/index-D2OGI462.js` | 777534 | `e96b910ab8364619061acaeb2170d79384495872675432b8f1fa702be1eb7feb` |
| `index.html` | 411 | `574d7c8e4fa283faeb3ec910a0c631e05754d791c06a0f8491c2c9060765d53e` |

A 精确合入本源码及后续独立文档提交；确认已复制新 `index.html` 和其引用新 JS/CSS，校验上表摘要。A 用现有当前 localhost 登录重新读取原研究会话的 task.frame.committed、完整成果，验证新建与刷新恢复；如果保留旧页，刷新实际静态资源。A 的代理 Referer 修复/后端 Origin/CSRF 不在 B 范围内。

B 本次未执行真实认证联调/SQL/LLM，不把实际失败 wire 回放或受控浏览器算产品整链接受；A 原失败保留，修复后真实页面回执仍 pending A。首次真人配对/文件授权和 P1 整轮接受仍独立 pending。原 MS-U2 handoff 未覆盖，不自动扩包；源码和交接分别提交、工作区干净后停止。
