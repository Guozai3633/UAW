# MS-I2j M1：浏览器与文件桥接接入清单

日期：2026-10-10。M1浏览器身份已实现并通过真实SQL/HTTP验证；旧MS-I2i固定来源完整1691项已先行封存。后台实际执行、成果HTTP和本机授权仍在后续里程碑接入。

## 1. B的客户端先消费什么

| 操作 | 方法/路径 | 已有输入→输出契约 | 目前实际状态 |
| --- | --- | --- | --- |
| 选模型 | GET /v1/models | ModelsListRequest→ModelPage | CLI开发入口已实现，浏览器待会话入口 |
| 创建会话 | POST /v1/conversations | ConversationsCreateRequest→Conversation | CLI开发入口已实现；自动模型/记忆/项目绑定仍有明确不可用分支 |
| 查会话 | GET /v1/conversations/{id} | ConversationsGetRequest→Conversation | 已实现 |
| 发原文 | POST /v1/conversations/{id}/turns | TurnsSubmitRequest→RunRecord | 持久受理已实现；实际后台Agent执行由本轮接入 |
| 查运行/控制 | GET /v1/runs/{id}；POST /v1/runs/{id}/control | RunsGetRequest/ RunsControlRequest→RunRecord/ Acknowledgement | 已实现；取消先请求，实际停止不能靠页面推断 |
| 理解提示 | GET /v1/tasks/{id}/frame | TasksFrameRequest→TaskFrame | 已实现；发送后显示，不覆盖原文 |
| Items/事件 | GET /v1/conversations/{id}/items、/events | ItemPage/ EventPage | 分页及签名cursor已实现 |
| 事件正文 | GET /v1/events/{id}/payload | EventsPayloadRequest→EventPayload | 已实现 |
| 人工审批 | GET /v1/approvals/{id}；POST /v1/approvals/{id}/decisions | ApprovalRequest/ ApprovalGrant | 已实现 |
| 成果/核验/接受 | 本轮补已拥有成果和CompletionBundle读取/决定入口 | 复用ArtifactRecord、VerificationReport、CompletionAcceptance | 内部组件已实现，HTTP待本轮接入 |
| SSE | /v1/conversations/{id}/events/stream | 已有EventsStreamRequest→EventEnvelope | 契约已定义，处理器未实现；先显式分页轮询 |

POST仍使用 `{meta,payload}`，RequestMeta中的request_id稳定且同请求不换ID，schema_version保持现有值；GET路径参数不放进query，query重复字段拒绝。成功是 `{kind:"ok",payload,...}`，错误消费既有Failure；不能把200/202当任务完成。准确字段和union以 contracts/uaw.schema.json、contracts/openapi.json及实际实现清单为准。

分页cursor固定本次watermark：走完本批页面以后重新取当前快照检查新增，不把最后一个cursor当无限追尾订阅。Item按id/revision更新，事件按seq去重；刷新查原请求/Run，不能再发一个turn。

## 2. 浏览器会话协议（M1已实现）

仅显式配置的localhost Web origin，禁止通配Origin、管理员浏览器登录和供应商key进入前端。原无Origin的CLI Bearer路径保持兼容。

| 目标操作 | 拟定路径 | 用法 |
| --- | --- | --- |
| web.launch | POST /v1/web/launch | 受认证用户CLI取得2分钟一次性启动URL，临时code只放URL fragment；管理员不得借此取得用户会话 |
| web.session.exchange | POST /v1/web/session | 该精确Origin用launch_code交换Host-only/HttpOnly/SameSite=Strict cookie；不传账号/owner/角色 |
| web.session.get | GET /v1/web/session | credentials:include，返回当前user Principal、期限和CSRF token，Cache-Control:no-store |
| web.session.logout | DELETE /v1/web/session | credentials:include及X-UAW-CSRF，服务端撤销会话并删除cookie |

阶段标签 `ms-i2j-a1`，源码固定 `c1045fde04a960d0345dc0881d86dba062de7f28`。GET成功返回HttpWebSessionGetResult；exchange、launch、logout分别返回相应HttpWeb*Result，仍沿用严格kind联合类型。DELETE用JSON正文 `{meta,payload:{}}`，不使用旧通用DELETE的If-Match约定。实际服务OpenAPI同时标记CLI Bearer与Web cookie两种认证，管理员路由只标CLI。

以上对象/操作已写入源契约及生成物，M1共36项聚焦验证通过。B按阶段标签的实际schema生成客户端，不自行修改服务端DTO。

cookie及一次code由独立浏览器签名密钥和随机ID生成，持久记录只保存身份、期限、版本、消费/撤销状态和令牌验证信息，不保存用户/管理员Bearer或供应商secret。短期code绑定独立认证的用户、配置Origin和账户凭据纪元，一次CAS消费；请求重放、换Origin/用户、过期或撤销拒绝。

实际M1字段如下（准确对象见公共schema，以下临时值只说明字段）：

```json
// POST /v1/web/launch；原无Origin用户Bearer，payload为空
{"meta":{"request_id":"launch_1","schema_version":"0.1"},"payload":{}}
// ok.payload: WebLaunch；code只在fragment中，不在query里
{"launch_url":"http://127.0.0.1:5173/#uaw_launch=短期一次码","expires_at":"实际UTC期限"}
// POST /v1/web/session；无Bearer，精确Origin，cookie不由请求正文控制
{"meta":{"request_id":"login_1","schema_version":"0.1"},"payload":{"launch_code":"上述一次码"}}
// ok.payload: WebSession；GET /v1/web/session也返回同一对象
{"principal":{"id":"配置的用户ID","kind":"user","auth_session_id":"web-session-随机ID"},"expires_at":"实际UTC期限","csrf_token":"实际64位十六进制值"}
// DELETE /v1/web/session；cookie + 精确Origin + X-UAW-CSRF
{"meta":{"request_id":"logout_1","schema_version":"0.1"},"payload":{}}
// ok.payload复用Acknowledgement
{"operation_id":"logout_1","status":"completed"}
```

launch_code是临时凭据，B交换后立即用history.replaceState移除fragment；不持久缓存。交换丢失回应先查询实际session，没有cookie时重新取得启动链接，不自动重放已消费code。错误包括origin_denied、csrf_denied、authentication_required/failed、web_ticket_invalid/expired/used、web_session_revoked/expired及capability_unavailable；依据真实Failure和HTTP状态显示，不能把错误降级为匿名执行。

建议B本机Vite将 `/v1` 代理到 `http://127.0.0.1:8000`，前端固定 `http://127.0.0.1:5173`，代理保留真实Origin。这样现有same-origin客户端能消费Host-only cookie；A同时验证实际API Host/loopback来源，不接纳转发头声明的远端身份。后台配置缺Origin或独立签名密钥时这些接口保持不可用。

浏览器状态修改必须精确Origin、实际cookie会话和X-UAW-CSRF同时满足；不能只增加CORS或删掉现有Origin拒绝。只允许loopback后端与可信Host，不信任转发头；原生本机程序不是因为SID/PID就能自证UAW账号。

配置未启用/缺独立密钥时网页登录不可用。启动脚本仅输出短期URL，禁止打印主凭据、写进VITE变量或localStorage。用户不需要配置模型/第三方API，这些继续由管理员控制。

## 3. 成果与用户控制接入约定

后台调度器拥有Run执行入口，单Agent拥有动作提案；Completion Controller拥有终态提交。用户接受按合同要求触发，前端只提交绑定真实Bundle/Artifact版本的决定。

页面先按已登记Run→Item/Event显示状态。本轮成果读取返回真实文本/Markdown版本、逐项VerificationReport和实际提案。缺证据/测试保持not_run/blocked，用户点击不能抹掉失败或未知外部效果。浏览器退出/身份变化阻止后续授权动作；重新登录可以读本人历史，继续旧执行或接受需按当前会话/版本重新核对。

## 4. C→A→D 文件接口责任

C继续使用 ToolExecutorPort.execute(call,spec,ctx)、ToolOutputVerifierPort.verify(data,call,spec,ctx)、ToolRecoveryAccessPort.check。C M1的新内部port从受信组装注入，输入完整已归一化原call/spec/ctx，输出已有command_ref/receipt_ref/RunnerReceipt；不让模型指定command、signer、owner或absolute root。

A维护原Tool调用→独立RunnerRequest/Command登记的桥接，以及既有 RunnerPipeClient.read(command_ref, recover=False/True)。A核对原call/工具版本/动作参数、budget attempt、当前设备/项目/根、签名与lease/fence；恢复使用同一原登记，不能重新签新command冒充原结果。

D维护真实本机确认、RootSelection一次消费、根句柄和活连接/签名journal。C不导入D开发分支，A也不在缺native确认时给真实用户目录造测试授权。C M1接口到达后A按其正式签名接适配，不在私有类型中偷加授权字段。

只读file_access/local_files与process_exec/code_execution独立。网页传字符串path不授予根权限；绑定须经过本人真实native选择/确认及当前服务端注册权威。

## 5. 阶段交付

- 初稿：只准备接入设计，旧回归仍收尾，未开放新端点/flags。
- M1实现后：补实际接口schema、错误示例、localhost启动方式、验证回执和固定阶段SHA。

M1完成：36项阶段验证和严格检查通过，原失败保留；启动用 `ops/browser-development.toml`、`ops/web_launch.py`，详见[实际M1记录](../../../implementation/MS-I2j-M1.md)。配置仍显式opt-in，旧全量1691不作为本轮代码的回执。

## 6. 已到达的阶段接口审阅

这里只确认接线签名；源码合入和模块验收另有回执，不能把阶段说明当成整包接受。

- B M1源码 `99c71df3a86b0788459f105e1bbab2e9a684491b`，交接 `bec9e8c`：12个既有用户路由、完整运行时schema验证、同源cookie和内存CSRF消费方式可以兼容。A新增会话协议后B按固定公共版本生成客户端。A在M2补服务器会话列表、原request_id→Run只读查询、真实成果/报告/合同读取及准确版本的接受；不存在的SSE/草稿理解继续明确不可用。
- C M1源码 `c8b5676d4cb65a65a38391b304095600b0ffed54`，交接 `9195a2e`：A采用 `ToolFileReadBridgePort.ready/resolve/execute/recover` 和 `FileReadEvidence` 正式签名。原snapshot必须来自同一原签名读取，不能通过重读文件补造。当前Runner whole/16,384字符边界先明确保留；lines/cursor和超界文件不注册为可用能力。非空project_id仍需独立项目准入，A不直接去掉既有拒绝。
- D M2源码 `88bb0f33a86560a5bce89421e84f1f75cb7d3a09`，交接 `af19a01`：真实 `WindowsNativeConfirmation` 和 `NativeReadAuthorization.select/bind/revoke` 可作为本机适配器接入。A仍须提供认证用户→独立设备/通道挑战登记；已有配对夹具和自动取消测试不证明真人批准。缺该来源时保持不可用。

这三份阶段接口已在旧MS-I2i固定回归期间只读审阅，未改worker工作区或运行来源。A的浏览器身份先服务网页任务；本机根授权只有真实人确认及当前登记全部通过后才加入相应Run的范围。
- B/C/D继续同包独立实现，原ms-i2j-start不移动；必须的兼容契约变更由A单独发布供受影响方按约定同步。
