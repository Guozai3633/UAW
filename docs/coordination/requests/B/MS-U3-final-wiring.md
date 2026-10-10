# MS-U3 最终接线与真实状态边界

2026-10-10。实际worktree `E:/UAW/.worktrees/context`，实际分支 `dev/context`。

## 固定输入与提交

开工时工作区干净；fetch origin --tags，读取远端 `git show origin/integration:docs/coordination/DISPATCH.md` 正式记录，并核对远端tag/本地tag/准确SHA。只 merge --ff-only ms-i2l-start，开工HEAD等于 `8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0`；uv sync --frozen成功。基线内旧准备字样未作为停工依据，没有合并浮动integration、reset/rebase/stash。全部原U1/U2及修复/handoff保留。

- M1源码 `8dcaeecca269c1e2a1fe434d3506745cf3eb8762`；阶段接口 `da39707c20030a1d096ccaed97eb159f2a9f5f5c`。
- M2源码 `d35725b0899c17b8df67581a18ac8e9b3dead0a0`；阶段交付 `c03b453317e91131b7805b7e9dea76b31fbef36d`。
- 最终M3/M4源码 `3c182ccc4c54dbfc6f429e8e9e2e2d0fbeb3301b`；本页与B handoff为其后的独立文档提交，准确交接SHA见git log/最终回报。

阶段均交付后继续同包，不等待A合入。末次fetch只读远端正式记录；没有新的MS-I2l HTTP阶段DTO。暂停Context优化，没有改backend/shared/flags/worker/Python或pnpm锁。

## 接口与页面行为

WorkspaceController.start(initialId?:string)/open(id)/reconnect原签名保留。选择次序是显式URL、同身份且服务端可见的上次activeConversationId、服务端首项；原全局Recovery独立保留，不抢选择。Conversation.id/owner/current principal/服务端可见列表必须一致；显式不可见URL不fallback。取消/身份变化/denied/missing/当前owner变化或最新可见列表移除时清旧正文、Run、理解、审批和显示草稿。popstate沿URL只读恢复；侧栏打开同步URL。读取会话期间输入框禁用，防止新会话尚未打开时丢掉用户刚输入的原文。

DraftStore.select(id)只存当前标识；草稿按identity/conversation保持原字节。Run/消息/权限/审批/模型key均不持久缓存。现有单次全局Recovery只保存原conversationId/requestId/runId，不扩多Run调度；另一会话草稿保留，提供“返回原请求会话”。未知发送沿原request_id RecoveryPort查询，刷新、断线、返回原会话均不自动POST、不换ID。Run状态来自实际服务端，不由接受HTTP或pending写成completed。

生成器固定 `ms-i2l-start`，完整保留22paths/25methods/181defs及所有递归业务字段（含description）；runtime schema逐定义对照原固定源。新增client方法仅消费已有：

| 方法 | 精确HTTP / payload |
| --- | --- |
| enrollment(id,signal?) | GET /v1/runner/enrollments/{enrollment_id} |
| beginEnrollment(candidate_id,meta,signal?) | POST /v1/runner/enrollments，payload={candidate_id} |
| confirmEnrollment(id,meta,signal?) | POST .../{id}/confirmation，payload={}，meta.expected_revision=原revision |
| revokeEnrollment(id,meta,signal?) | POST .../{id}/revocation，payload={}，meta.expected_revision=原revision |

请求仍{meta,payload}，cookie/CSRF来自当前内存WebSession。没有新路由、approved字段、native证明或目录权限。

```ts
// 来自已认证同源 host 的可信 locator，下面只是构造形状，不是实际生产来源。
interface EnrollmentSourcePort {
  current(signal: AbortSignal): Promise<{candidateId?: string; enrollmentId?: string}>;
}
const port = new HttpEnrollmentPort(client, trustedHostSource); // 可省source
await port.read(originalEnrollmentId, signal);                 // GET实际原登记
await port.decide(currentRead, 'confirmation', signal);         // 本人确认Reader+空payload/CAS
await port.decide(currentRead, 'revocation', signal);           // 当前原版本撤销
```

EnrollmentPort公开locate/read/begin/decide/uncertain，可注入 `window.uawWebHost.enrollments` 或 `.enrollmentSource`；不是public schema变更。省source时首次登记明确unavailable，仍可由本人输入原登记ID查询。不会让用户填写candidate/owner/PID/key/proof或路径来授权。read校验原id、proof_document.enrollment_id及当前完整owner；决定前重新GET原版本/proof/原expiry，等待后核对身份/Abort。UI实际pending/active/revoked/expired，不输出proof/nonce/public key；pending不是批准，active不代表目录授权。

未知设备请求在发送前只存原requestId/candidateId或enrollmentId/基准revision；同身份刷新先prefill原ID再GET，当前原版本未变化仍禁止重发。初次begin失回没有公开request lookup HTTP时明确未知阻塞，依赖可信来源交付原enrollmentId再读，不猜接口。存储失败禁止派发。注销/身份变化清本地设备查找；record/proof/state/权限始终只在内存，组件关闭/身份变化中止读取。没有任何后台自动确认或首次配对启动。

完整成果仍走实际RunDeliveryView/UTF8正文/hash/固定artifact及bundle Ref/合同/逐项report；显示核验与来源Ref的版本/hash/location。材料不会成为规则或授权。旧hash、过期审批、取消/接受竞争、未知acceptance和新身份拒绝沿原模块检查：未知先读实际acceptance，无回执不能换ID重发。接受按钮只适用于绑定实际Run revision的running/waiting_for_user交付；回执仅触发重新读取，不代写完成。

## 验证命令与准确回执

```powershell
uv sync --frozen
pnpm --dir apps/web install --frozen-lockfile --offline --store-dir apps/web/.store
pnpm --dir apps/web generate
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web test:e2e  # 含tsc/build，controlled Chromium，非真实native/LLM
pnpm --dir apps/web exec node scripts/u3-readonly.mjs
pnpm --dir apps/web exec node scripts/u3-readonly.mjs --authenticated
```

最终66单元（原54+本包12）、29受控Chromium（原22+本包7）、1真实localhost匿名TCP浏览器分别通过；各最终XML0失败/错误/跳过，不累加阶段57/63/65或重复跑。类型、冻结离线安装、生成器完整字段保留与重复生成字节不变、构建和git diff --check通过。Node实际脚本24.21.0，宿主22.13 engine warning、主chunk>500KB warning保留；不宣称生产性能接受。

66个单元与29个浏览器准确节点、日志hash和产物hash见自身ignored `apps/web/.test-results/u3-final-receipts.json`。原U2 actual event fixture只是原真实wire回放，其中HTTP/后续动作受控，不是本包新增模型调用。1真实匿名节点直接访问实际8000、B最后构建5178→8000同源代理，读实际401/denied，刷新零修改；没有A launch/本机来源，不证明认证恢复、配对或成果接受。

新MS-U3受控覆盖：显式较旧URL/最新列表/两会话草稿刷新/返回；不可见URL无fallback；当前身份变化清旧草稿；原全局Recovery返回原Run并保留另一草稿；设备三种实际枚举标签与缺源/无root；未知确认跨刷新只GET；最新可见列表移除清正文。额外单元覆盖begin失回、lookup保存失败、迟到身份/取消、原owner不匹配；原hash/接受unknown/取消竞争/审批/分页/Markdown回归保留。

### 原失败及修复

1. 锁安装首次store入口失配：--store-dir .store触发无TTY拒绝；没有删除模块或改锁，使用原 --store-dir apps/web/.store成功。u3-install-store-failure.log/u3-install.log保留。
2. M1首轮导航检查迟延但实际57通过；切到popstate入口后57复验。原u3-m1-navigation-original.log保留，不称原测试失败。
3. Chromium首轮27通过/2失败：设备Dialog用了不存在的dialog-content，遮罩挡住按钮。复用现有dialog样式，未强制点击或加长超时。u3-m3-browser.log/initial.xml/initial目录原截图trace保留。
4. 次轮28通过/1失败：测试运行中改localStorage，被已初始化内存草稿覆盖。改为启动前单次准备恢复fixture，保留原刷新、原文和零POST断言；u3-m3-browser-second.log/.xml/目录保留。
5. 后续28通过/1失败：新会话列表先可见但正文未打开，输入可能被切换清掉。页面读取期间禁用输入，原创建测试增加精确原文断言，5秒/30秒时限不改；u3-m4-create-race.log/.xml/目录保留，最终29通过。
6. 辅助编辑脚本首次默认GBK读取UTF8失败，未写入；改显式UTF8后成功，没有测试断言删减。

受控截图u3-controlled-device.png已目视核对Dialog层级/按钮/原期限与撤销状态；不是真实本人截图。原失败日志/trace、阶段构建和U1/U2历史回执未删除。

## 最后构建与A接线

A可只读复制 `E:/UAW/.worktrees/context/apps/web/.test-results/u3-final-dist/`，不要执行或安装B环境。固定source为3c182ccc4c54dbfc6f429e8e9e2e2d0fbeb3301b，阶段M2独立dist/manifest也保留。最终文件：

| 文件 | SHA256 |
| --- | --- |
| index.html | 02aa11b71c656f620bbbcc2724108f23b60b7bc45a47ca144becaa2d6904255a |
| assets/index-C0Lw-9jO.js（798081 bytes） | 2087c1d4c2465d6ac396a5033b9287be9c9286088ca13c5d9d1c1e17e03a1d83 |
| assets/index-g0vbB5zk.css（17542 bytes） | 0599b8cecf47c6922bb90e8377bb9a6cf05dd717e71a9e0acaaf060ed62d103b |

A在已声明同源loopback入口部署该准确构建，原生产cookie/CSRF/真实用户保持。开发代理仍只允许显式UAW_WEB_API_TARGET=http://127.0.0.1:8000，无admin token/model key前端输入。

认证只读脚本需受保护环境 `UAW_U3_WEB_URL`、`UAW_U3_LAUNCH_URL`、`UAW_U3_CONVERSATION_ID`、`UAW_U3_ENROLLMENT_ID`。只使用限时同源launch交换一次，去fragment，读取实际可见会话/刷新/原登记。禁止其他写请求，截图/trace/video关闭，不记录正文、证明、cookie或launch。当前4项均缺，脚本exit2且u3-authenticated-pending.json明确pending，测试没有收集后假报通过/skip；没有运行原U2真人决定suite。

具体未通过与公共缺口：
- 实际认证页面当前会话刷新/原登记GET及成果实际来源复验：pending A限时launch和当前可见ID。
- 首次可信candidate/current locator、native本人确认、原journal/control/device源：pending A生产装配；省source明确unavailable。
- root授权没有HTTP：pending A正式固定DTO/命名入口；UI不可用，不猜路径或由active状态生成权限。若需页面根状态，A先发布当前用户可见的固定来源、过期/撤销错误语义，不把证明/key交前端。
- 真实文件→Context→固定Model→成果/真人接受及实际取消审批：pending A与本人，B未代点，没有重复真实模型调用增加计数。

最小A消费变更仅注入可信EnrollmentSourcePort或完整EnrollmentPort、提供只读实际lookup和部署B准确构建；如果要新增HTTP，A发布阶段契约后B按具名输入接入，不能用fixture冒充来源。A负责审阅合入、公共冲突、独立真人回执和汇合全量；默认模型/flags/D01/D03/D06不变。模块交付不代表MS-I2j/MS-I2k/MS-I2l/P1整轮accepted。本包结束，不自动下一包。

## 相对固定基线的全部前端修改

- `apps/web/scripts/generate.mjs`
- `apps/web/scripts/u3-readonly.mjs`
- `apps/web/src/features/devices/Devices.tsx`
- `apps/web/src/features/devices/port.ts`
- `apps/web/src/features/review/Review.tsx`
- `apps/web/src/features/workspace/Workspace.tsx`
- `apps/web/src/features/workspace/controller.ts`
- `apps/web/src/lib/api/client.ts`
- `apps/web/src/lib/api/generated/openapi.d.ts`
- `apps/web/src/lib/api/generated/schema.json`
- `apps/web/src/lib/api/generated/source.json`
- `apps/web/src/lib/cache/drafts.ts`
- `apps/web/src/main.tsx`
- `apps/web/src/styles.css`
- `apps/web/tests/e2e/controlled/u3-workspace.spec.ts`
- `apps/web/tests/e2e/controlled/workspace.spec.ts`
- `apps/web/tests/enrollment-fixtures.ts`
- `apps/web/tests/u3-readonly/anonymous.spec.ts`
- `apps/web/tests/u3-readonly/authenticated.spec.ts`
- `apps/web/tests/unit/enrollments.test.tsx`
- `apps/web/tests/unit/u3-selection.test.ts`
- `apps/web/u3-readonly.config.ts`

文档另含MS-U3-stage-interface.md、本页和B.md追加记录；均在B允许路径。
