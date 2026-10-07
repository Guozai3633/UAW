# 接口共同规则

版本：0.1，2026-10-07。这里规定所有接口的共同执行约束；[接口总入口](README.md)列出具体功能。**这是拟实现契约，不是已上线接口说明。**

## 1. 五类入口和信任边界

| 类别 | 谁可以调用 | 身份与权限从哪里来 |
| --- | --- | --- |
| HTTP用户API | 已登录用户 | 认证会话；请求只选资源，不能指定owner |
| HTTP管理API | 具有管理角色的主体 | 服务端管理角色；普通用户不能自报admin |
| LLM工具 | 当前Run的获准Agent | ToolRuntime注入Run/实例/政策/预算，不接受模型自报 |
| Runner协议 | 已配对设备及签发服务 | 设备会话、命令签名、本机批准的根和能力，逐层复核 |
| Runtime/私有组件 | 对应Facade或受控适配器 | 独立参数 `TrustedExecutionContext`，不拼入用户正文 |

`ScopeSelector`是请求缩小范围；`Scope`是服务确认的范围。两者不能互换。模型输入里的文件路径、引用、角色名称和“我已批准”都不能产生真实权限。多用户尚未建设，但每条记录和索引仍带主体，避免单用户阶段埋下跨账号读取问题。

用户主体、管理员主体、Runner主体、Agent实例是不同对象。审批不能增加原用户、设备或产品不存在的能力。用户选择固定模型后，主/子Agent默认继承；只有真实用户明确指定子模型才能覆盖。模型不可用时反馈给当前LLM/用户解决，不能自动改成便宜模型。

## 2. 请求与实际HTTP字段位置

POST/PATCH的实际请求：

```json
{
  "meta": {"request_id": "request_001", "schema_version": "0.1", "expected_revision": 3},
  "payload": {"patch": {"title": "新的工作标题"}}
}
```

路径中的 `conversation_id` 等从URL取得，不在payload重复发送。文档输入对象把路径和业务参数合成后展示，OpenAPI描述真正的线上字段位置。重复路径字段属于未知字段，拒绝。

GET参数来自path/query；meta来自可选 `X-Request-Id`、`X-UAW-Schema-Version`。未传request ID时服务生成并回传。DELETE必须有 `X-Request-Id` 与 `If-Match: "3"`，CAS修订由header转换为RequestMeta；不使用DELETE正文。

工具参数没有HTTP外壳。ToolRuntime产生操作ID、可信上下文及实际尝试ID；工具草案中的 `creation_key`、`action_id`、`client_definition_key` 分别承担对应业务去重，不替代认证。

## 3. 字段约定与大小

| 字段类型 | 单位/含义 | 0.1限制 |
| --- | --- | --- |
| ID | 不透明稳定标识 | 1–128字符；无路径或密钥含义 |
| Revision | 对象单调修订整数 | ≥0；0只用于尚不存在对象的创建比较 |
| Version | 内容/格式/提供方版本标签 | 1–128字符，不能转成Revision进行大小比较 |
| Timestamp | RFC 3339时间 | 时区明确；持久存储规范化UTC |
| Duration、`*_ms` | 毫秒 | 通用最大7天；wait最多60秒；进程timeout>0 |
| Count、`*_bytes` | 非负整数 | 通用最大2,147,483,647；按接口进一步收窄 |
| Decimal | 非负十进制字符串 | 不用浮点金额，最多9位小数，伴随币种 |
| Text | 有限内容 | 最大16,384字符；大内容走blob/Ref/分页 |
| RelativePath | 项目根内相对路径 | 禁绝对路径、盘符和`..`分段；Runner再查真实路径和链接 |
| 普通数组 | 有类型元素列表 | 通常最大256，接口可收窄，如创建16个角色、等待8个实例 |
| 分页limit | 每页元素数 | 1–100，缺省20；不声称总量以避免昂贵计数 |
| JSON请求正文 | UTF-8 JSON | 建议部署硬上限1MiB；超出413，内容改走上传 |
| 单资产上传 | 二进制 | 最大100MiB；部署可降低，必须校验真实字节和整体摘要 |

JSON Schema的 `default` 是说明，不能假设验证器已经自动补值。DTO规范化层只对文档明确默认的字段补值。省略字段不等于null，null不自动代表删除；删除使用明确操作。未知字段一律拒绝，避免拼错参数或注入可信字段。`Object`/`Schema`/`JsonValue`只用于动态工具参数、JSON Schema片段、批准适配器设置等明确扩展点，随后还要按对应ToolSpec/profile校验；不得把业务实体都变成任意字典。

JSON传输拒绝NaN/Infinity等非JSON数值。用户授权来源使用UserInputRef，结构只允许input，服务仍核验真实主体及行为。TaskFrame引用用kind=task_frame、id=task_id、version=理解修订；TaskRecord用kind=task，两个域的版本不能混用。

大小上限是首稿默认政策，不是架构永远固定数值。管理员只能在发布配置中调整获准范围；当前调用消费固定配置版本。

## 4. 返回状态和HTTP状态

每个接口的结果结构是 `ComponentResult<业务payload>` 的严格实例：

```json
{"kind":"ok","payload":{"operation_id":"op_001","status":"accepted"},"output_refs":[]}
```

`ok`只表示当前接口成功。例如创建Run成功后，Run仍可处于queued/running。`waiting`没有成功payload，必须有wait_ref指向审批、用户问题、进程或实例。失败不是返回空payload；必须有Failure并说明阶段、是否可重试和恢复提示。

| HTTP状态 | kind/返回 | 常见原因 |
| --- | --- | --- |
| 200 | ok | 读取或提交当前操作成功；不代表整个任务结束 |
| 202 | waiting | 本接口尚等审批、用户或异步执行；携带wait_ref |
| 401 | AuthenticationFailure | 未认证，不回显被保护资源ID |
| 403 | denied | 无权限、旗标关闭、策略不允许 |
| 404 | missing | 资源不存在；未获准用户也可统一404以避免泄露存在性 |
| 409 | conflict | CAS失败、同幂等键不同请求、写集合冲突 |
| 412 | stale | 引用/审批/环境/成果基线已过期 |
| 422 | failed | 参数schema、协议版本、业务条件错误 |
| 429 | failed | 配额/预算/速率不足，可有retry_after_ms |
| 500 / 502 / 504 | failed | 内部/依赖/截止失败；不得通过换模型隐藏 |
| SSE 410 | stale | 断点已过期，应先加载会话快照再续接 |
| 413 | 入口拒绝 | 传输正文超过上限，未进入Runtime业务执行 |

Failure.code使用稳定机器码；message面向用户；recover_hint说明读取新版本、等待、澄清或对账。HTTP状态映射不能改变ToolResult的真实业务status和副作用状态。内部Runtime不使用HTTP状态码表达状态。

## 5. 幂等、版本冲突、原子边界

去重作用域为 `(principal, interface, resource, request_id)`；参数规范化后哈希。相同键与参数返回同一已受理操作及当前状态；相同键不同参数409。首稿默认至少保留24小时去重记录，活跃Run/未决外部写期间不得回收。去重记录与受理状态同事务提交。

角色创建每项再用client_definition_key；委派用creation_key；外部动作用action_id及提供方business_key；进程用command_id；触发器用occurrence_key。attempt_id每次真实尝试不同，重试不生成新逻辑动作。

更新、撤销、局部接受、审批、控制权转移、合并及任务关联必须提供目标Revision或内容Version。HTTP meta.expected_revision负责域修订；工具业务参数显式expected_revision；如同时出现两处，必须相同。文件操作还校验文件摘要/树Version，审批还校验参数Hash和目标Ref。

CAS冲突后读取新版本，再重新决定；禁止自动“以当前版本覆盖”。跨多个Runtime不假设一个巨大数据库事务：同域提交使用原子仓储/CAS，跨域以操作记录、不可变引用、Outbox事件和补偿/对账衔接。仅当全部域固定版本已提交才产生Checkpoint。外部效果无法随数据库回滚抹除。

## 6. 分页、等待、流式续接

Cursor是不透明签名值，包含主体、资源、筛选Hash、快照和位置。不能跨筛选/账号/版本复用；默认游标有效期由部署政策固定，失效返回stale并给重新读取入口。结果读取固定快照；新资料通过新查询看到。大输出保存Ref，不能通过截断悄悄变成完整结果。

`agents.wait`最多8目标，`wait_ms=0`立即返回；等待60秒到期仍返回最新状态和timed_out，不宣称失败。进程poll读取实际状态及输出游标；exit_code在终态才出现，缺省不等于0。用户输入和取消可打断等待。

SSE连接先验证会话权限，按提交seq有序传递；网络重连可能重复，前端按event_id/seq去重。`id:`是可续接Cursor，`event:`是EventType，`data:`是EventEnvelope JSON。心跳是注释，不推进持久seq。Last-Event-ID和cursor必须一致；慢消费者有界缓冲，超限断连后续接。

## 7. 状态机与事件项目

Run主链：queued → preparing → running → verifying → completed。按当前状态可进入waiting_for_user、waiting_for_merge、failed、cancelled；等待后回到对应工作阶段。仅Completion Controller在当前成果/要求/证据/副作用版本一致时提出终态提交。completed之后新要求创建新Run，不重写旧结果。

Node/Agent的completed只表示该节点/实例结束；结果可以partial或failed，不等于整个Task成功。子失败由父收集后决定重试、改计划或交付partial。stale结果不能继续喂给Join当有效证据。状态转移由代码执行白名单，模型只提出行动/结果候选。

InteractionItem有稳定ID、开始/终态和增量/替换区分。前端用item.type/status和关联资源决定展示，不分析“努力奔跑中”等模型文字来判断成功。终态项不再追加delta；修订产生新项或受控替换。事件类型与payload类型由注册表对应，Ref内容读取后还要按该事件schema校验。

## 8. 审批与本地执行

- manual：需要审批的动作由用户决定。
- assisted：批准的审查服务在既有政策内帮助判断；拿不准或越界交给用户。
- automatic：政策内动作无需额外用户确认，真实权限和禁用能力仍执行。

这些是专项文档暂定的语义，产品文案尚待确认。任何模式都不扩大真实权限。批准绑定动作ID、规范参数Hash、资源版本、范围和有效期；拒绝后停止该动作，并可让Agent提出另一方案；超时不是批准。审批后必须recheck；参数或资源变化产生新审批。

Runner对每条命令验主体、设备、签名、期限、项目根、权限交集、租约栅栏和argv/shell策略。目录/venv不能冒充OS沙箱。文件访问检查realpath和链接；命令可能影响根外资源，因此exec需要实际OS隔离或明确本机原生授权，不能仅靠cwd承诺隔离。安装环境使用批准模板和来源，预装优先；安装失败保留真实日志，不能伪ready。

## 9. 失败恢复、取消、撤销

ToolRuntime负责有界退避、熔断和登记了严格等价契约的提供方切换。非等价工具替换由Agent重新选择并记录证据/结果差异。固定用户模型禁止恢复时暗换模型，Auto也只能在明确授权集合内。

先持久化动作意图，再派发；网络超时可能已经成功，所以external_write效果unknown必须先查询回执，不能盲重试。无法查询则挂起等待人工/提供方确认。所谓“正好一次”不跨任意外部服务承诺；使用幂等键和账本达到可对账执行。

取消传播到节点、子Agent及进程树。调用无法立即打断时，结果标记不再贡献旧目标，效果仍进入账本。断连lost不能假称stopped。只读/模型调用已经发生的成本计入预算。

文件撤销基于before/after和当前内容，保留用户后续改动；局部合并、撤销和用户修改会使相关测试报告失效。外部发布/发信/删除不是文件undo，只有提供方明确可逆动作才支持补偿，并再次审批和记录结果。

## 10. 缓存、引用和完成

模型前缀缓存保持稳定的系统规则、角色/技能版本与工具schema顺序，动态输入放后段；实际缓存Token来自提供方usage，不能凭前缀相似宣称命中。结果缓存仅用于可复用只读/派生结果，键包含主体、资源版本、配置/政策、模型/提示词/参数和时效依赖。审批、未知写、进程状态、用户意图修订不得直接从缓存当新执行结果。

缓存命中也检查权限与时效；删除记忆、撤销连接、禁用能力、变更配置、文件修订均传播失效。single-flight仅合并同scope同依赖的计算；失败不长期负缓存，临时失败有短期策略。bounded_age必须从关联政策取得max_age，否则拒绝不明确时效。

引用必须指向实际读取内容及位置，检索摘要只能当线索。语义判定可以说明inference/insufficient，不虚构网页、文件路径或执行日志。核验逐要求覆盖，命令exit0只证明那条检查完成；未运行必须not_run/blocked。用户接受与模型核验是两个对象，用户接受不补造缺失测试。

## 11. 管理配置和历史存储

模型、搜索API、环境模板和能力包由管理员发布；普通用户不配置平台密钥。私人账号连接另需用户授权。秘密write-only，日志、trace、模型上下文和普通用户视图不返回凭据值或秘密句柄。

本稿同时支持cloud_authoritative和local_authoritative部署。没有确认权威位置前不启用双主写入；本地缓存只加速，上传/离线重放用明确去重和CAS。保留、删除和加密政策随部署配置版本记录，不能假设“缓存就是永久历史”。

## 12. 契约版本与验证限度

0.x允许审阅后修改，必须记录迁移映射。新增可选字段也须先发布对应版本，旧版本拒绝未知字段；删除/改类型/改语义属于破坏变更。工具定义固定schema版本；OpenAPI `/v1`为拟定外部路径，不代表对象契约已经到稳定1.0。

当前使用[OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html)描述HTTP，用[JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-core)定义对象。schema可以校验结构；权限、引用存在、DAG无环、CAS、审批有效、环境隔离及实际业务效果都必须由Runtime实现后验证。

生成：`python contracts/build_interfaces.py`。检查：先在独立验证环境安装jsonschema，再运行 `python contracts/check_interfaces.py`；也可使用 `--dependency-root <目录>`加载隔离依赖。本次验证依赖装在系统临时目录，没有选择UAW正式技术栈。检查报告明确区分schema检查与尚未执行的后端集成测试。
