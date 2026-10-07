# UAW 管理端配置与联网服务

状态：v0.1 讨论稿。用户确认成品应用不要求终端用户配置联网搜索、模型或第三方 API；先预留管理接口，后续建设管理员界面。接口、配置对象和运维实现尚未落地。

## 1. 控制层与执行层

新增逻辑控制层 Configuration Service，不增加第八个领域 Runtime，也不要求单独微服务。内部划分 ModelCatalogConfig、ToolProviderConfig、CredentialBindings、EnvironmentTemplates、CapabilityPolicy、Validation/Activation、Audit/Versions。管理员负责受控配置，Runtime 只读取已启用快照与凭据引用。

管理接口提供 draft/validate/activate/list_versions/rollback/disable/revoke；首期可用管理员 CLI/API，网页 UI 后置。终端产品只展示可选模型、可用能力与必要状态，保留用户已确认的模型选择/子 Agent 显式覆盖；不把凭据配置和模型选择混为同一设置。

| 配置对象 | 管理内容 | 消费模块 |
| --- | --- | --- |
| ModelProviderProfile | 适配器、endpoint、凭据引用、可用模型/能力、限额和价格版本 | Model Runtime |
| ToolProviderProfile | 搜索/内容读取/MCP 等实现、能力契约、凭据引用、额度、超时与等价替代 | Tool Runtime |
| EnvironmentTemplate | 版本/digest、工具链、受控初始化/依赖源、网络/资源限制 | Workspace Runtime |
| CapabilityPolicy | 产品 flag、用户可见范围、角色权限上限、预算 | Ingress 与各 Runtime |
| Reference/DeliveryPolicy | 可保留快照范围、预览/下载生命周期、必需检查 | Context / Workspace / Agent |

管理员身份与普通用户身份分别验证；模型和任务工具没有调用管理接口、读取密钥或自授权配置的能力。后台配置的扩展性通过 provider adapter + schema/contract 版本实现，不让任意 endpoint 或脚本配置自动取得宿主执行权限。

## 2. 联网搜索与内容读取链路

```text
管理员启用搜索/读取提供方并配置受控凭据
→ Tool Registry 形成可用 ToolSpec，更新语义索引
→ Agent 按任务发现并选择搜索/读取能力
→ Tool Runtime 校验政策、预算与健康状态
→ 适配器调用服务 → 规范化候选/内容及取证时间
→ Context 注册版本化 Reference → Agent 使用证据与引用交付
```

search.query 与 web.read 分别表达发现候选和获取具体内容；可注册多实现，tool_id/版本与 provider_id 明确。固定业务流程不替代 LLM 选择，但真实授权/网络校验由代码执行。检索关键词由模型按任务生成，结果范围、新鲜度、语言等参数受契约约束。

搜索结果包含标题、URL、摘要、排序、时间字段及实际 provider；摘要不是完整正文。读取内容包含实际最终 URL、抓取时间、content hash、抽取器版本与可定位正文；无法获取时说明范围，不能伪造来源。网页资料与用户上传材料都作为数据处理。

读取服务对允许协议、目标地址、重定向和响应大小做受控验证，公共搜索工具不自动取得服务器内网/云元数据访问能力。未来组织内部连接器采用显式资源域与账号权限，不能借公共 URL 任意穿透。网络限制是 Runtime 边界，不靠主 Agent 提示词保证。

Tool Runtime 可以在登记 EquivalenceContract 的提供方间恢复；功能/范围改变返回 Agent 决策。搜索与正文读取不天然等价；不同索引覆盖也不能凭相同工具类别自动当成等价。限额耗尽或全体服务故障返回服务状态，用户不用临时提供自己的 API key 才能继续。

## 3. 配置生命周期与凭据

Provider profile 使用 draft/validated/active/disabled/revoked；健康状态与生命周期独立。验证检查 schema、适配器存在、凭据绑定、能力及最小连接测试；连接测试有费用时记录成本。先验证草稿再原子启用，失败不替换当前可用配置。

ConfigSnapshot 带 revision、启用对象版本和政策引用。新 Run 固定所需快照用于可追溯；调用前检查当前撤销、权限和额度。普通配置变更默认影响新 Run，安全撤销立即阻止后续调用。密钥轮换通过受控引用解析，不要求把旧密钥留在 Run 快照；无法保留旧提供方则返回 typed failure，不静默改变效果。

管理员下线用户显式选定的模型时，该调用受阻并反馈当前 LLM/用户；不能违背已有模型继承契约自动换模型。Auto 只在用户授权范围与管理员开放目录的交集中路由。提供方恢复不代表用户授权的模型已可被另一个模型替代。

密钥本体保存在独立 CredentialStore；prompt、ToolSpec、向量索引、前端和日志只使用不敏感引用。Provider adapter/受控代理获得必要秘密，不把成品搜索或模型 API key 注入任意项目代码/安装脚本。第三方用户账号连接与平台 API 配置不同：未来访问私人资料仍需该用户明确授权，管理员 API key 不自动授予资料权限。

回滚生成新配置 revision 并重新校验当前政策，不能恢复已撤销授权或泄漏旧密钥。配置审计记录管理员、时间、非敏感 diff、激活/回滚结果与原因；普通用户只能看到适合产品交互的可用性/错误，不暴露 endpoint 凭据或内部日志。

## 4. 配额、缓存与故障反馈

平台总额度、用户/任务额度、并发、超时分别管理；调用前预留，成功/失败后按实际用量核算。费用未知记录 unknown 而非免费。健康探测与熔断避免各 Agent 同时重试耗尽服务；管理员可观察错误率、成本、延迟和启用版本。

工具候选缓存绑定 Registry/Profile/Policy 相关版本；结果缓存绑定账号可见域、来源版本和新鲜度。禁用/撤销阻止执行及数据返回，后台索引更新延迟不能继续授权。管理员更新 parser/model/provider 版本按真实依赖失效，不靠清空所有缓存解决一切。

端点返回错误按 credential_invalid/provider_unavailable/quota_exceeded/capability_unavailable/policy_denied 等类别反馈，公开消息给出是否可重试、是否已有部分结果；技术诊断在管理端。Agent 可继续使用获准资料或交付缺口，不把配置故障编成答案。

## 5. 首期交付边界

先实现配置对象、版本化读取、凭据引用、校验/启用接口、审计及禁用控制；首个模型/搜索/读取和环境适配器通过这些接口消费配置。完整管理 UI、多管理员组织治理、市场和大量 provider 后续增加。

设计验收：终端用户无 API key 配置流程；普通用户/Agent 不能改平台配置；启用失败不覆盖现有配置；撤销立即生效；变更可追溯；密钥不进入代码沙箱或日志；指定模型下线不擅自替换；平台配置不能绕过用户私人资料授权；额度故障与网页证据缺失清楚区分。以上尚未实际测试。
