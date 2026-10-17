# MS-U4 最终接线：原Run问题、纠正与恢复

2026-10-17。组件源码及受控工程验证完成；M4实际新服务联调 **pending**，H02/P1-14/P1-15/整轮不标accepted。只读来源缺失不计通过或skip。

## 实际分支、固定来源与提交

- 原工作区 `E:/UAW/.worktrees/context`，实际分支 `dev/context`。app绑定的detached checkout没有改动，未创建替代worktree/session。
- 原干净HEAD `c13232bd8b8af813e448c14b8d39b8e4789662ba`。fetch核对远端正式DISPATCH及local/remote tag，只快进 `ms-i2m-start / 1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe`，HEAD相等；再只快进固定 `ms-i2m-a6-source / b16c69a92d81124c00fb859ce8123748f56df054`，HEAD相等。旧提交/handoff保留，uv frozen、pnpm原锁离线同步通过。
- M1源码 `1e3447853b4d068955728b43099beb07d74ffac9`，阶段说明 `7676b135f670fa87409378ae9361ef4a6d3a8dd3`；M2源码 `b210f4bb61d0bff9852497b854c7820b345a51ed`，阶段说明 `4697e8a6f34722237a4a14b9fd629fdc817ddf47`。阶段到即在当前聊天交付，随后继续本包M3/M4，没有等待最终合并。
- 最终源码 **`5e0b37d90d12641d20e3acf4b704cf79bca3a13d`**。本页与handoffs/B.md是随后独立文档提交，准确handoff SHA见最终回报。
- 最终源码提交后干净fetch只读复核 `origin/integration / 49cf4026464c74e441b05f0a6f90fc6b4df793b4` 的DISPATCH，仍为A6：D实际clock/Tool时间adapter/新服务未装配。只取正式发布说明，没有merge浮动integration/reset/rebase/stash，也没移旧tag。

## 公开接口与行为

生成器固定A6 tag和完整SHA。30路径/33方法/204完整schema定义，包含description、if/then、Ref与所有生成字段；再次generate无diff，原公共schema不改。client新增 `runConversation / clarification / answer / correct / continuation`，消费精确五HTTP。新GET和写请求均带 `X-UAW-Schema-Version:0.2`，写meta为 `ConversationRequestMeta`；旧turn/control/approval/acceptance继续原0.1，不强转。

```ts
const port = new HttpConversationPort(client);
const view = await port.read(actualRun, signal);
const scope = {conversationId:view.run.conversation_id, runId:view.run.id};
const meta = conversationMeta(view.run.revision); // 本人一次提交只创建一次
const receipt = await port.submit(view, 'clarification_answer', exactUserText, meta, signal);
await port.lookup(scope, meta.request_id, signal); // unknown只查询原id
// correction同port，kind='correction'；不改Run id或固定用户模型。
```

`ConversationPort.read(run,signal) / question(scope,itemId,signal) / lookup(scope,requestId,signal) / submit(view,kind,text,meta,signal)` 与 `HttpConversationPort(client)` 为稳定消费入口。scope/当前版本/实际问题关联每次复核；submit冻结原view/meta/原文，先重读Run/input，回答再读原question，版本/终态变化拒绝；模型或外部等待后身份/Abort检查保留。`ControlPreflightError`表示没有派发的本地复查失败，POST transport/无效响应保留原lookup未知状态。没有新HTTP、权限缓存、自动写入或后台进程。

默认main已注入真实HTTP port及 `ContinuationStore(storage=localStorage)`；可信host可注入 `window.uawWebHost.conversation`。嵌入组件可省略port隐藏组件；默认应用缺后端能力由真实503/缺源显示不可用，不假造空图。`ConversationPanel`默认3秒串行轮询，单个观察阶段120次成功读后停止自动读并提示手动读取；身份/会话/Run版本变化和卸载中止旧读取，失败不无限重试。没有SSE实现，继续如实标分页轮询。

```tsx
<ConversationPanel port={port} store={new ContinuationStore()} run={actualRun}
  identity={client.currentSession()!.identityKey} connected={true}
  onSource={setAvailable} onBusy={setBusy}
  onChanged={() => controller.reconnect()} />
// 组件可配置pollMs/pollLimit；传入的可信port仍须遵守相同当前权威/身份复查。
```

页面只从RunConversationView发现开放问题，显示原问题/原因/候选与自由回答；普通消息问号、批准/接受文字不产生问题或操作。回答同Run、运行中纠正，原文不trim/改写。`accepted`仅“已收到，尚待生效”，`applied`仅真实回执并保留applied_at，`superseded/cancelled`各自显示；页面不置completed。终态无续跑动作，下方原turn输入仍为明确新请求；既有审批、完整成果/hash/Refs/逐项核验/合同接受门槛保持。

持久化仅本人草稿与原请求ID/CAS查找元数据，绑定完整Web身份（含session/expiry）+conversation+Run。回答草稿另按question id，纠正另键。draft最多50 scope、每文131072字符；每原Run最多64 pending、存储索引4096上限。每request独立key避免两页覆盖别人的pending；保存并读回成功才POST。损坏/串scope/ID碰撞/清理失败保守阻止重发并提示。确认原scope/request/kind/base input/question版本的实际receipt才清原lookup；不缓存许可、问题图、patch状态、模型输出、secret或审批。退出清理，身份切换不能继承；没有自动停止、换ID、新Run、接受或重发。两页同Run的用户草稿使用同一scope的最后保存版本，pending不合并成一个可覆盖行。

## 精确验证及失败历史

实际环境：Windows原B独立`.venv`与apps/web本地依赖。锁内node **24.21.0**、pnpm **10.17.0**；外层pnpm引导node22.13.0会有engine提示，脚本执行用本地锁内node24。未改依赖/锁。Vite原大chunk提示保留，未改门槛屏蔽。

| 命令（仓库根） | 实际最终回执 | 范围 |
| --- | --- | --- |
| `uv sync --frozen` | exit0，ms-u4-uv-sync.log | 原B独立环境 |
| `pnpm --dir apps/web install --frozen-lockfile --offline --store-dir apps/web/.store` | exit0，ms-u4-final-install.log | 原锁无变化 |
| `pnpm --dir apps/web generate` + generated diff | exit0，ms-u4-final-generate.log；无diff | 完整定义/字段保留单元同时通过 |
| `pnpm --dir apps/web typecheck` | exit0，ms-u4-final-typecheck.log | 源码及B全部测试 |
| `pnpm --dir apps/web test --reporter=default --reporter=junit --outputFile.junit=.test-results/ms-u4-m3-unit.xml` | **96不同单元/20文件，0失败/错误/跳过** | 原82+新14，不累加阶段/复跑 |
| `pnpm --dir apps/web test:e2e` | 构建成功，**53不同受控Chromium，0失败/错误/跳过**，ms-u4-final-chromium.log/.xml | 原43+新10，不是实际认证/模型/SQL |
| `pnpm --dir apps/web exec playwright test --project=chromium u4-conversation.spec.ts --grep 'graph question/options/free answer'` | 1视觉截图复跑通过，ms-u4-visual.log | 已包含在53中，不另累计；截图已目视核对 |
| `git diff --check` / 原HEAD祖先核对 | exit0 | 只改允许路径、旧提交保留 |
| 仓库`apps/web`内 `pnpm exec node scripts/u4-readonly.mjs` | **exit2/pending**，ms-u4-live-guard.log/pending.json | 三变量缺失，未尝试CDP/HTTP连接；不计通过/skip |

自身ignored `apps/web/.test-results/ms-u4-final-receipts.json` 保存准确不同节点名、日志/XML/hash、环境、来源/文件；回执不复制到公共evidence。单元88/95阶段、targeted8和视觉1均不叠加；SQL为N/A（前端组件包），真实新模型调用/账单/native/授权/合同接受未执行。

保留原失败：M2首次缺括号类型失败、nullable收窄失败、测试Storage替身缺clear导致build失败；均修正后通过，原ms-u4-m2-*-initial.log保留。M3初次8浏览器7过1失败：测试在pending记录刚保存、原丢响应POST仍返回途中就切换服务夹具身份，导致新的图被旧POST改写；增加等待实际transport未知返回，再切身份，保留隔离和无重发断言/原超时，8/8及最终53通过；原ms-u4-m3-chromium-initial.log/.xml和ms-u4-m3-identity-initial trace/screenshot保留。两次M2自动审批额度限制拒绝的工具动作没有执行，不算测试失败；按原审批流程获准重试后成功，没有绕过限制。

10项新浏览器节点覆盖：真实读图发现/原文CAS；纠正与双击/替代回执；丢响应/原ID刷新；问题412；两页pending竞争；取消409；身份/缺源/认证；普通文字不产操作；原Page验证器严格GET；缺源/跨Run私密拒绝。受控模型、时钟及HTTP不冒充真实来源或本人体验。

## 冻结构建与修改清单

A只读复制本worktree **`apps/web/.test-results/ms-u4-final-dist/`**，不执行B的环境，不热改H01-v5；内容与本轮最后build的dist一致。源码5e0b37d，三文件SHA256：

| 文件 | bytes | SHA256 |
| --- | ---: | --- |
| index.html | 411 | 7abf73d60c2c8de9ecb952b0f3969bef35a6d58e164809ef18ee4f8fa2dd34a5 |
| assets/index-Bf4x2xo2.css | 19093 | b7d60e370ceecc4df7024e3f97366150998a76902a291c6fbe09d7552d2d5aa8 |
| assets/index-DpAgQSfE.js | 847979 | 4f1ad1f955eaa90219870f053169c6cf7b24908bd24804c6e79cc38e03a71325 |

相对A6源码仅21个apps/web文件，加本包B阶段/最终文档及handoffs/B.md：

```text
apps/web/scripts/generate.mjs
apps/web/scripts/u4-readonly.mjs
apps/web/src/features/conversation/ConversationPanel.tsx
apps/web/src/features/conversation/port.ts
apps/web/src/features/conversation/store.ts
apps/web/src/features/workspace/RequestGuidance.tsx
apps/web/src/features/workspace/Workspace.tsx
apps/web/src/lib/api/client.ts
apps/web/src/lib/api/generated/openapi.d.ts
apps/web/src/lib/api/generated/schema.json
apps/web/src/lib/api/generated/source.json
apps/web/src/main.tsx
apps/web/src/styles.css
apps/web/tests/conversation-fixtures.ts
apps/web/tests/e2e/controlled/u4-conversation.spec.ts
apps/web/tests/u4-readonly/authenticated.spec.ts
apps/web/tests/u4-readonly/owned-page.ts
apps/web/tests/unit/continuation-store.test.ts
apps/web/tests/unit/conversation-panel.test.tsx
apps/web/tests/unit/conversation-port.test.ts
apps/web/u4-readonly.config.ts
```

不改Context/后端/公共schema/uv或前端依赖锁/Model/Run/装配根/flags/其他worker，也没读取A配置、key或复制真实用户正文作fixture。

## A接线与真实pending

A合入这些B提交，审五HTTP、实际current owner/原Run及input/question CAS、原队列/时钟与真实Model消费后，部署上述准确dist到独立新H02版本。默认客户端无需新增服务器字段；候选装配必须提供真实clock/剩余主动段/Tool时间adapter，503不能在前端填空或伪造applied。旧0.1和H01-v5原快照/失败/账本/本人历史保持。

A明确提供 **新版本URL、原拥有者CDP地址和真实原Run ID** 后，可在apps/web内运行 `pnpm exec node scripts/u4-readonly.mjs`；三个名称是 `UAW_U4_WEB_URL / UAW_U4_OWNER_CDP_URL / UAW_U4_RUN_ID`。URL只允许loopback、原conversation query、无hash/凭据；CDP只附着唯一已存在同URL Page，绝不newContext/newPage/launch交换/导航/退出。也可由A直接调用 `verifyOwnedConversationPage(originalOwnerPage, actualRunId)`。

验证器在原Page凭现有同源cookie只GET session/原conversation/Run/0.2图/指定问题/原receipts，前后身份/expiry/读图一致，核对scope/版本；只输出状态/版本/计数，不输出原文、cookie/CSRF/IDs，不存localStorage、不截图/trace/video、不开native、不点提交/审批/接受，不关闭A页面。活跃状态在读中变化则明确拒绝本次观察，不把旧/混合版本算通过。当前入口仅缺源guard已实跑，实际原Page验证仍pending，不能凭两个受控验证器节点算完成。

实际回答/纠正/长等待/刷新与文本成果的生产链、本人原Page体验、费用与独立质量均待A新服务及本人操作；B不代点。B交组件后停止本包独立开发，后续依赖到达再按准确来源联调，不自动扩Context/多Run或下一包。
