# B/MS-U1 M1 客户端接口（2026-10-10）

worktree E:/UAW/.worktrees/context；分支 dev/context。
固定基线 ms-i2j-start = abb4590f2bfe53c601e0f6a4a3b65447ba4ec502。
clean→fetch tags→ff-only→HEAD==tag→uv sync --frozen成功；无reset/rebase。
M1源码 99c71df3a86b0788459f105e1bbab2e9a684491b。本说明单独提交；继续M2/M3/M4。

## 实际工程与签名

apps/web 独立 package/pnpm-lock：pnpm10.17.0，Node24.21.0（本工程dev依赖私有
二进制；全局Node22.13未更改），React19.3.0 / TS5.9.3 / Vite8.3.4 / React插件6.1.2。
Tailwind4.3.3，Ajv2020 8.20.0，react-markdown10.1.0/remark-gfm4.0.1，
Query5.104.1 / Router8.4.0 / RadixDialog1.2.0 / Playwright1.64.0均精确锁。
根Python锁/依赖、公共schema、后端/认证/flags无改动。当前pnpm宿主仍报告Node22
engine警告，实际pnpm exec node及script构建为v24.21.0，不将警告隐藏成无兼容问题。

生成器 scripts/generate.mjs 只选实际12个用户路由，类型来自 contracts/openapi.json；
准确请求和完整响应运行时校验来自contracts/uaw.schema.json。source.json保存两者SHA256。
类型生成移除不可表达的if/then及required-only条件anyOf，保留字段形状；Ajv运行时仍
完整保留所有条件，包括path参数、required、additionalProperties、正文/附件约束。
仅登记date-time/uri格式，未知format拒绝。设计OpenAPI的其他路由不冒充已实现。

| client方法 | 实际方法与路径 | payload/输出 |
|---|---|---|
| models | GET /v1/models | ModelPage |
| create | POST /v1/conversations | ConversationsCreateRequest→Conversation |
| conversation | GET /v1/conversations/{id} | Conversation |
| items | GET /v1/conversations/{id}/items | cursor/limit→ItemPage |
| events | GET /v1/conversations/{id}/events | cursor/limit→EventPage |
| payload | GET /v1/events/{id}/payload | EventPayload |
| submit | POST /v1/conversations/{id}/turns | TurnsSubmitRequest去path字段→RunRecord |
| run | GET /v1/runs/{id} | RunRecord |
| frame | GET /v1/tasks/{id}/frame | TaskFrame |
| control | POST /v1/runs/{id}/control | UserControl→Acknowledgement |
| approval | GET /v1/approvals/{id} | ApprovalRequest |
| decide | POST /v1/approvals/{id}/decisions | ApprovalDecision→ApprovalGrant |

`UawClient(session:()=>WebSession|null, transport:typeof fetch=fetch)`，cookie same-origin、
no-store、AbortSignal；POST仅{meta,payload}，path字段不在body。WebSession是B内部
host注入接口 identityKey/csrfHeader{name,value}，尚无服务器认证协议，不是私造HTTP DTO。
默认没有认证来源/审批/成果权限。只允许用户会话host，不能传管理员bearer或模型key。

`Result<T>`显式ok(payload)/waiting(wait_ref)/missing/denied/conflict/stale/failed/cancelled
(failure)；即使HTTP202也由kind决定，错误展示Failure.message，缺JSON/坏协议/丢失POST
为TransportError(uncertain=true)，不自动重试，不解析模型文字猜成功。超时/Abort传播。

示例：
```ts
const meta = requestMeta(conversation.revision);
await client.submit(conversation.id, {text:originalUnmodified,attachment_refs:[]}, meta);
// 同一POST回应未知后保存meta.request_id和原conversationID，先GET已知Run/对账。
// 原request查询端点缺失：不重发、不文本匹配推测；等待A明确查询协议。
await client.control(run.id,{mode:'cancel',preserve_refs:[],reason:'用户请求停止'},requestMeta(run.revision));
// 决策前重新GET当前Approval，复核revision/hash/refs/expiry，once或reject，仅本次；不默认scoped。
```

Projection按Item ID/revision、Event seq/event_id及delta base/result revision推进；原页面恢复
将在M3实现。旧游标失效从Item/Run当前快照恢复；本标签无SSE，使用明确分页轮询。
ReviewPort是B内部可选消费契约（ArtifactRecord/VerificationReport/CompletionAcceptance
来自已有schema）；尚无实际HTTPadapter，默认不可用，不猜accept/content路由。
[最小公共接线缺口及消费影响](MS-U1-api-gaps.md)交A，继续独立页面开发。

## 真实回执与未完成项

命令：pnpm --dir apps/web install；generate；typecheck；test；build。
本工程ignored install-stage.log/typecheck-stage.log/unit-stage.log/
unit-stage-repair.log/build-stage.log，.test-results/unit.xml。生成12路径145定义，
类型通过，构建通过，4客户端测试通过。无真实后端/LLM联调回执，真实M4 pending。

历史：注册表下载若干ECONNRESET/timeout自动重试后成功；Node私有包初次bin生成警告
后preinstall完成且node24实际核验；TS7与生成器peer不兼容→锁TS5.9.3；生成器漏named
inline请求/条件anyOf产unknown→修类型生成但不删运行时校验；测试误用permission而非
实际authorization类别→首次3pass/1fail，修复4pass。原失败日志保留。

等待A：浏览器认证/精确Origin/CSRF/退出；原request→Run查询；成果内容/报告/合同接受
的真实契约与HTTP；服务器会话列表；真实执行调度。B将依据已发布兼容基线接线，不使用
其他session未交接源码、不修改其他worktree、不承认产品P1整轮验收。


## M2 页面与控制阶段

源码2093d647cb1357dd8ca4518a9afba671fb6ba2a2；本说明另行提交，继续M3/M4。
会话侧栏/创建时实际目录模型选择/原文聊天/浅色自适应理解框/实际Run状态/审批
approve_once与decline/取消等待/Markdown成果摘要与可选正文接受已实现。输入框编辑
显示“发送后根据原文理解”，不假装已有预发送AI；TaskFrame.summary来自服务器。
当前scope/model/原文不由UI升级。unknown发送不重发，已知Run恢复GET；默认无
认证host，页面显示不可用，不放token输入。ReviewPort默认缺失，只展示Item摘要。
审批等待点击前重新读当前版本/hash/refs/expiry，再CAS；不缓存授权。控制接受ACK
不当作cancelled；Run终态由GET/Event确认。安全Markdown禁HTML、危险URL和远程图片。

M2 typecheck/build通过；15单元通过（客户端4/投影4/草稿3/controller3/Markdown1）。
ignored unit-m2-repair.log/build-m2.log。历史类型首次拒绝新fixture错误的model_policy/
event_payload Ref及UserInputRef泛型；按后端实际policy/event和kind泛型修测试，未
放宽schema。页面首次拒绝动作错误reject，按实际decline修复。所有原失败日志保留。
真实认证/API/模型/成果接受/执行联调pending；未把15受控组件或截图标产品验收。

A可注入 `window.uawWebHost`（B内部host adapter），`session()`返回可信identityKey
与已发布CSRF header；subscribe通知退出/换身份，logout完成服务端失效；
recovery.find(conversationId,requestId,signal)查原Run或明确undefined；review实现
B ReviewPort.read/accept，必须由A真实HTTP契约适配，不能生产挂fixture。身份Key需含
issuer/subject/workspace/epoch的可信分区标识，非密码；body/model不提供此权威。


## M3/M4与A1已发布协议消费

M3/M4首版88c6bd8dda2bf198119e92177ffa0a5c2f879e6b；最终固定Ref/可读核验修订 d2ece8d1682a4ae1de2ed811fc24e304e3584569。
A的ms-i2j-a1 / 202544f452c485c84eb7fe08675576e31c75cad3 已只读消费公共契约，
新增实际GET/POST/DELETE /v1/web/session；生成器固定git show该标签，不覆盖共享文件，
不开另一worktree，不声称B HEAD等于A1。现在13路径/15方法/152定义，原12方法保持。
原生fetch默认改箭头包装，POST/DELETE JSON和实际X-UAW-CSRF；默认BrowserSessionHost
交换一次码前移除fragment，丢回应GET对账，内存CSRF/10秒当前复查/退出，无Bearer输入。
显式UAW_WEB_API_TARGET=127.0.0.1:8000代理保留Origin，开发5173；受控preview测试5177。
33单元＋11受控Chromium、类型/构建/冻结离线锁通过，原失败回执保留。
实际8000后端只读探测URLError，真实5场景环境未提供，test:live exit2/pending，
不计真实通过/skip，不做Model/SQL/Runner验收。原request/成果/完整执行/接受HTTP仍需A。
准确源码、命令、全部文件、失败历史和注入/缺依赖说明见[最终接线](MS-U1-final-wiring.md)。
