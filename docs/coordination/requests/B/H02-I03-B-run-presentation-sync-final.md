# H02-I03 B：任务展示、模型理解与成果同步交接

2026-10-18。仅原 H02-I03 定向修复，工程组件已验证；真实最终 Page 复验由 A 部署准确构建后执行，未标 MS-U4/H02 整轮 accepted。

## 固定来源与实际提交

- 实际原工作区 `E:/UAW/.worktrees/context` / `dev/context`；原干净 HEAD `9504d70f650318f025d24531d6e8bbbba1ed5fb8`。app绑定的另一个detached checkout未改，未建替代worktree或session。
- fetch tags后只读origin/integration DISPATCH正式A15发布，核对remote/local `ms-i2m-a15-source`均为 **`3f10b6af27ed5f56a726a7bafe8ee1d083f2bd2b`**；执行普通 `git merge --no-edit ms-i2m-a15-source`，A15已包含B全部旧交付，实际快进且HEAD同SHA。原提交/handoff祖先检查通过，无浮动integration/reset/rebase/stash。
- 阅读固定源码内 `H02-I03-B-run-presentation-sync.md` 与 `MS-I2m-A15-presentation-wiring.md`；uv frozen/pnpm原锁离线同步通过，没有改后端/公共schema源/锁/flags或C/D。
- 阶段源码 **`a5f30e1feca102370c5f0de7707fdc473c137fa7`**，9定向单元/6受控浏览器后已在本聊天交付；A报告已普通合入1507cad并审阅。随后按A意见将技术状态收进详情，分离读取错误和提交提示、补503→200恢复，源码 **`ab0fdce90023065d99162e7b20db9f6bee9e7785`**（113/66通过）保留。
- **最终源码 `af3889f209054b2485aa5ff7aeab6479878342b0`**：自动成果对齐共用展示读取上限，不再误重置为手动新窗口，补2个计数/在途取消单元，115/66通过。本页与handoffs/B.md是随后独立docs提交，准确handoff SHA见最终回报。

## 精确接口与统一来源

生成器锁固定A15及其准确SHA，消费实际新增只读 **`GET /v1/runs/{run_id}/presentation`**、`X-UAW-Schema-Version:0.2`；无body/query，沿原同源cookie身份，`cache:no-store`。生成31路径/209完整定义；原1404 canonical定义逐对象不变，重复生成无diff，旧HTTP及0.1写入保持。没有复制自造公共DTO。

```ts
const port = new HttpPresentationPort(client);
const presentation = await port.read(actualRun, signal);
// 返回实际生成的 RunPresentationView；read前后身份与Abort复核。
const reads = new PresentationSession(port, conversationPort, continuationStore);
const source = await reads.read(client.currentSession()!.identityKey, actualRun, signal);
// source={identity,presentation,conversation,receipts,pending}，仅本组件内存展示。
reads.invalidate(); // 取消/卸载或消费方观察代次结束；不产生服务器操作。
```

默认main注入真实HttpPresentationPort，可信host可选 `window.uawWebHost.presentation`；Workspace新增可选presentationPort，旧嵌入可不提供，继续原显示兼容。默认生产入口缺新来源显示不可用，不用Frame或消息文字假造当前理解/阶段。PresentationPort.read(run,signal)及新增可选组件展示参数不更改原Conversation/Review提交端口。

`PresentationSession`以完整Web identity+conversation+Run绑定，实际核对Run id/conversation/revision/input_revision、understanding input、delivery四Ref/kind/Run修订和输入版本；终态phase必须与权威Run相同。presentation和原ConversationView核对完整同Run对象/输入；如出现变化只补一次presentation GET，仍不一致则拒绝发布混合快照。原回执不越过当前输入/Run版本。每次等待后Abort/generation复核，拒绝旧input/Run修订/较旧captured_at；phase/understanding在Run修订未变时仍更新，不能只依赖revision增加。captured_at只作显示顺序防回退，不是授权或命令。

Workspace、ConversationPanel、任务理解与Review共享该已核对来源。ConversationPanel的原submit仍由HttpConversationPort在本人显式动作前重读Run/input/question CAS，不缓存授权；unknown沿原request_id恢复，草稿不清除。来源读取中保留上一份已核对内容并标后台更新；读取失败保留且标历史/不可用，提交和接受禁用。读取错误独立于提交/unknown提示，503→200时旧读取错误消失，不擦除提交对账提示。身份/会话/Run改变中止旧代次，不借另一身份复用。

自动展示轮询3秒、每观察窗口最多120个完成读取周期；周期包含当前图/Conversation/有界原回执等GET，不能将120误称为总HTTP上限。自动Review对齐共用该计数，不打断在途读取；只有明确手动刷新或观察边界变化开始新窗口。原Item/event/Delivery读取策略保持，不宣称整个应用只有120个GET。无新增模型、运行写入、续期、SSE或权限缓存。

## 页面与权限边界

- awaiting_acceptance显示“成果已就绪，等待你审阅”，宽屏/1050px均有查看成果入口，仍保留修改和停止路径；不把Run改completed或自动释放原新请求限制。默认只显示中文阶段，Run.status、phase、Run/input修订保留在默认折叠的“任务状态详情”。受控断言显式展开后核对原值，没有删除或改写权威状态。
- finalizing显示“正在收尾”，stopping显示“正在停止”且禁重复停止，都不当作completed/cancelled。实际终态只由权威Run决定；needs_revision/unavailable准确提示。
- 理解只取真实Model记录投影的summary/assumptions及原decision/model_output Ref版本；不把TaskFrame复制原文当独立理解。not_provided显示“按你的原文执行，本次未单独提供理解摘要”；只有pending才等待。本人草稿仍为输入基准，无额外模型调用。
- Review按共享presentation当前delivery选准确版本，同时保留Item的同版本hash限制，不以展示Ref绕过被篡改的Item hash。全文/核验仍从原DeliveryReader读取，对齐四Ref+原Run修订/input来源；不符则只读并请求统一重读，不能接受。历史Artifact仍可阅，不能当新输入结果。
- 接受仍执行原Delivery再次读取、完整Ref/hash/contract/verification/Run修订及CAS/身份/Abort复查；phase本身不授予接受权。接受丢响应只查实际acceptance，不换ID/重发；finalizing后仍等权威completed。没有自动提交、停止、审批/native确认或接受。

## 真实验证回执与失败历史

锁内node24.21.0/pnpm10.17.0；外层pnpm引导node22 engine提示、Vite原大chunk提示如实保留，未改门槛屏蔽。

| 命令/检查 | 实际结果及自身ignored回执 |
| --- | --- |
| `uv sync --frozen` | exit0，h02-i03-b-uv-sync.log |
| `pnpm --dir apps/web install --frozen-lockfile --offline --store-dir apps/web/.store` | exit0，h02-i03-b-install.log；无锁改动 |
| `pnpm --dir apps/web generate` + generated diff | exit0，h02-i03-b-final-generate.log；31路径/209定义、无diff |
| 原A8 1404定义与A15 canonical逐定义比对；本包公共schema/锁diff | 相等/无本包改动 |
| `pnpm --dir apps/web test --reporter=default --reporter=junit --outputFile.junit=.test-results/h02-i03-b-bound-final-unit.xml` | **115不同单元/23文件，0失败/错误/跳过**；h02-i03-b-bound-final-unit.log/.xml |
| `pnpm --dir apps/web test:e2e` | `tsc --noEmit`+Vite构建通过；**66不同受控Chromium，0失败/错误/跳过**；h02-i03-b-bound-final-browser.log/.xml |
| `git diff --check` / 原B HEAD祖先检查 | exit0 |

去重为原107单元+新6协调读取+新2hook上限=115；原60浏览器+新6=66。阶段9/6、早先113/66与重复跑不叠加。新覆盖包括精确header/DTO、同修订阶段变化、迟到响应、输入变化、缺源/身份/Abort、读中保留、not_provided、stopping/finalizing、未知接受、旧Artifact拒绝、宽屏/1050px和503→200。模型/HTTP/时间为明确受控DTO，不冒充实际认证/SQL/LLM/本人体验。SQL为本前端包N/A，A原10 SQL不累计进B。

自身 `apps/web/.test-results/h02-i03-b-final-receipts.json`保存准确不同节点、日志/XML/hash与环境。原 `h02-i03-b-receipts.json`对应早先ab0fdce，保留。失败均保存：

- 首次phase误传RunStatus类型、测试Promise未标Response、旧fixture括号tsc错误，原initial typecheck日志保留，修正类型/语法后通过。
- 首轮Chromium62过4失败：旧断言要求缺源隐藏提交区/等待成果的旧中性文字，A15现要求保留旧值并禁提交/显示就绪；另2项旧注入host没有测试Principal导致原ConversationPort拒绝。夹具显式提供受控Principal，更新语义断言并保留禁止写入/Ref/hash/接受断言，未添加生产权限fallback。
- 第二轮65过1失败：停止提示在原POST到达前已显示，立即读fixture计数为0；改等待实际原POST计数，不改权限或测试时限，原失败log/XML/trace保留。
- A阶段审阅的技术值常驻与读取错误残留已修，503恢复定向覆盖。后续113/66、最终115/66通过。1440/1050截图仅受控数据，已目视核对。
- 上限修复首个工具动作因自动审批账户额度不足未执行；正常流程恢复后修复/测试完成，未绕过。不是测试失败或被认定动作不安全。

## 最终构建与文件

**最终准确构建为 `E:/UAW/.worktrees/context/apps/web/.test-results/h02-i03-b-final-dist/`，源码af3889f。A只读复制，不执行B环境。** 与最后通过构建的dist字节/hash相等；旧 `h02-i03-b-dist/` 是ab0fdce历史构建，不作为本最终交付。

| 文件 | bytes | SHA256 |
| --- | ---: | --- |
| index.html | 411 | 691209ac20ffa101925f0bd1f8bd1238434bd8dd5e1281fcd7b9bd687068537d |
| assets/index-BMQtQCI7.css | 21051 | e237d3788925a7c0d3fb4ff7897173b4e62672c34bf79621e43e2954852b8b7f |
| assets/index-DcQ18qX1.js | 865669 | f85248b12b07521048a02eb407e09b9509f6bdc39f305827b52b80761fbf6516 |

相对固定A15仅25个apps/web文件，加本B最终文档与handoffs/B.md：

```text
scripts/generate.mjs
src/features/conversation/ConversationPanel.tsx
src/features/presentation/port.ts
src/features/presentation/usePresentation.ts
src/features/review/Review.tsx
src/features/workspace/TaskUnderstanding.tsx
src/features/workspace/Workspace.tsx
src/lib/api/client.ts
src/lib/api/generated/openapi.d.ts
src/lib/api/generated/schema.json
src/lib/api/generated/source.json
src/main.tsx
src/styles.css
tests/e2e/controlled/a2-workspace.spec.ts
tests/e2e/controlled/backend.ts
tests/e2e/controlled/h02-presentation.spec.ts
tests/e2e/controlled/h02-terminal-feedback.spec.ts
tests/e2e/controlled/run-state.ts
tests/e2e/controlled/u3-workspace.spec.ts
tests/e2e/controlled/u4-conversation.spec.ts
tests/e2e/controlled/waiting-feedback.spec.ts
tests/e2e/controlled/workspace.spec.ts
tests/presentation-fixtures.ts
tests/unit/presentation.test.ts
tests/unit/presentation-hook.test.tsx
```

## A实际来源与接线要求

A已报告H02-v6固定A15在5183/8013 ready，原账号/DB/cookie沿用，新增presentation认证HTTP曾返回原v5/input1 awaiting_acceptance+understanding.available，0新模型/运行写入。B未读A私有environment/HTTP正文/凭据，没有操作这些服务、连接替代浏览器、交换launch或代本人提交/停止/授权/接受。原Page一度被浏览器URL策略拒绝，未绕过；随后本人手动刷新恢复，A已回到原反馈会话，负责部署准确最终dist和同Page实际核对。

**最新A来源变化单独保留：原Run现为failed/v6，understanding.available，当前delivery为空，旧报告可历史读取。** A正查原等待审阅期间计时未暂停的失败原因，属后端来源变化，B未复活/重发或更改Run。最终真实UI复验须显示真实失败、真实理解及旧报告只读；不能把之前v5等待接受硬恢复。本包awaiting_acceptance证据为先前A认证HTTP和受控测试，不宣称当前实际任务仍待接受。

A合入阶段+ab0fdce+af3889f及本独立handoff，核对最终三文件hash后装配到同源A15，使用原Page刷新；无新后端接口或schema改动。逐项核对最新Run/输入/理解/旧报告、默认中文主状态/折叠原状态详情、1050px入口、无代操作和原历史/费用保持。真实最终页面、本人满意、计时失败原因与独立事实质量继续由A分别记录；B115/66是组件门槛，不标H02整轮accepted。交付干净后停止，不自动扩包。
