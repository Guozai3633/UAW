# UAW 任务完成校验、引用与代码工作区

状态：v0.2 讨论稿，配套架构 v0.8。用户纠正为首版支持授权本地项目访问与测试；联网搜索、模型和第三方服务配置由管理员提供。三种审批与语义核验详见 [LOCAL_APPROVAL_SEMANTIC.md](LOCAL_APPROVAL_SEMANTIC.md)。本文协议尚未实现或通过真实任务验证。

## 1. 首版资源边界

支持用户授权连接的本地项目、主动上传附件、获准网页/远程内容、会话、可选云端工作区与成果。上传材料不自动授予持续本地读取；输入路径字符串不等于已绑定项目。真实本地项目通过客户端/配对 Runner 读取和执行测试，范围由用户授予。

WorkspaceBackend 提供 allocate/import_snapshot/read/write/apply_patch/list_changes/merge/export/release；首版含 LocalWorkspaceAdapter，CloudSandbox 可选。ProjectRootBinding 与本地授权纳入协议，本地执行可用能力由实际 Runner 报告。SandboxPath 与 LocalPath 不可混用；宿主服务器文件系统不向 Agent 暴露。

AssetRepository 负责上传/下载、版本、归属、删除和持久保存；Workspace Runtime 负责本地/云端执行副本与变更。已连接本地项目可纳入未提交修改形成快照；上传材料或获准远程仓库也可作为输入。远程仓库连接是可选适配器。具体本地隔离、配对和权限见 LOCAL_APPROVAL_SEMANTIC.md。

## 2. 完成协议与模块细分

保留七个 Runtime。在 Agent Runtime 下设 Completion Controller：Contract Resolver、Criterion Tracker、Verification Coordinator、Semantic Reviewer Adapter、Completion Gate。不是每次另起 Reviewer Agent；简单回答可以在当前调用中核对，复杂交付按实际条件选择工具和审阅。

| 所属模块 | 内部职责 | 对外结果 |
| --- | --- | --- |
| Intent / Agent | 从原文及用户纠正整理 DeliveryContract、修订完成条件 | 条件 ID、来源、适用版本、必需/建议、验证方法 |
| Context | Reference Registry、Source Resolver、Locator Mapper、证据读取 | 可定位的版本化来源与证据 |
| Tool | Validator Registry、发现、执行、结果规范化、失败恢复 | 真实工具调用与结构化检查结果 |
| Workspace | 环境准备、不可变快照、命令/浏览器执行、产物导出 | 环境、代码版本、ChangeSet、Artifact |
| Agent | 按条件汇总检查、审阅内容、选择补救或申请结束 | CompletionProposal 与缺口 |
| Run | 校验合法终态、原子记录报告/版本、发布交付 Item | Run outcome、Delivery 状态、用户可读结果 |

DeliveryContract 的条件区分用户明确要求、产品必需要求和 Agent 建议；建议必须标注来源。Agent 不能删除失败的必需条件来宣布完成；减少用户要求走明确用户修订，产品硬约束不能由模型或用户输入绕过。普通概念回答只需目标覆盖等轻量条件，不因建立契约而自动运行编译器或网页测试。

单个 Criterion 最小字段：id、description、source_ref、required、method、subject_refs、expected、freshness_policy、status、check_refs。CheckResult 状态为 passed/failed/blocked/not_run/inconclusive/not_applicable/stale，说明判定依据；LLM 语义评估附理由和证据，不将主观分数当确定事实。

SemanticAssessment 围绕当前任务目标、成果与证据给出 satisfied/partial/unsupported/uncertain/blocked/stale 的判断及理由/缺口，不使用固定推特业务字段。Criterion 动态来源于任务语义；结构化记录仅用于关联和追踪。模型选择检查/补救方法，Runtime 校验真实引用、版本及执行事实，不能用语义判断伪造已跑测试。

## 3. 四层验证与完成链路

1. 资源层：成果/来源存在、归属正确、版本一致、可按权限访问；文件可解码或按对应格式打开。
2. 结构与运行层：格式、字段、公式、编译、测试、接口响应、关键交互等确定性检查。
3. 任务语义层：满足用户目标、范围、受众、口径与必要证据；网页能打开不证明支持结论，编译成功不证明用户功能成立。
4. 交付层：实际内容与检查对象一致，有可用预览/下载/引用，重要缺口可见；用户接受另外记录。

这是校验分类，不是要求所有任务按四次模型调用执行。任务契约决定适用检查；不能为每个回答强制生成任务图或启动审阅子 Agent。

```text
原文/用户纠正 → 适量完成条件
→ 执行与产物版本 → 按需检查 → Criterion 与证据关联
→ 不满足：有界修复 / 补证据 / 询问 / 明确部分交付
→ 申请结束 → 对版本、必需条件、可访问性和未决动作做最终核验
→ 固定交付版本及报告 → 发布成果 Item → 用户查看/接受/继续修改
```

CompletionProposal 含 task/contract revision、成果版本、条件结果、检查引用、未验证范围、未决副作用、建议 outcome。Runtime 从真实记录解析这些引用，不接受模型伪造日志、exit code 或验收证据。模型生成了结束文本不直接赋予 completed 状态。

Run execution_status 扩展为 queued/preparing/running/verifying/waiting_for_user/waiting_for_merge/completed/failed/cancelled。终态另带 outcome=succeeded/partial/blocked/failed/cancelled，completed 只表示本次执行结束，界面依据 outcome 呈现“完成/部分完成/受阻”。资源限制但已有可用成果可 completed + partial；环境阻碍且无法继续可 completed + blocked；需用户回答且仍计划继续则 waiting_for_user。保持现有 Run/Task/Delivery 三者独立。

只有全部适用必需条件通过、没有未决必需动作且交付可访问时才能 succeeded。建议条件未完成要公开限制；检查未跑或环境受阻不能写“测试通过”。必需副作用结果 unknown 阻止 succeeded，但可在有界核对后终止并保留 unknown 记录，不能自动重发。用户要求先给现有结果允许部分交付，不伪称全部完成。

Run 完成不等于用户接受；Delivery 继续使用 delivered/under_review/accepted/partially_accepted/revision_requested/rejected。用户审阅若是 Task 契约的必需条件，Task 在接受前保持未完成，避免 Run 长期占用执行资源。

## 4. 校验绑定真实版本

VerificationReport 含 report_id、contract_revision、snapshot_ref、dependency_refs、environment_manifest_ref、validator/version、实际命令/参数/cwd、started/ended_at、exit_code、统计、日志/截图/trace 引用、结果来源与缺口。公开日志隐藏凭据，原始敏感输出限制访问；报告不能包含凭据本体。

检查在固定快照或隔离验证副本运行。测试可能生成/修改文件，前后记录变更，修改验证对象时不得继续把报告指向旧内容；需固定实际受测版本或在纯净副本复验。验证数据库、端口和测试目录各实例隔离，避免并行 Agent 相互污染。

修改、撤销、合并、局部接受或依赖更新后，比较相关输入与环境。依赖不变且 validator 契约允许才能复用报告，否则 stale 并重验；未知依赖范围保守扩大。Completion Gate 对预期版本做 CAS，交付引用不可变快照；检查到终态提交之间发生用户修订时拒绝旧完成提案。

父 Agent 核验子报告的目标、条件和实际成果版本；兄弟分支各自通过并不证明合并版通过。合并后至少运行契约要求的受影响整体验证。验证失败返回当前 Agent 自主选择补救；总重试/时间/成本有界，不能无限修补。

## 5. 统一引用对象

Reference 是可定位对象；Citation 是某个回答片段或论断与 Reference 的关联。点击可访问性与论断支持程度分别验证，不能用一个 citation_valid 布尔值混在一起。

Reference 最小字段：ref_id、kind、owner/scope、resource_id、revision/content_hash、title/media_type、locator、provenance、observed_at、availability、access_policy_ref。可选 public_url、published_at、valid_until；敏感内部存储键不返回前端。公共网页版本来自实际抓取的内容 hash，不假设 URL 固定等于内容固定。

| kind | 资源 | locator 示例 | 展示 |
| --- | --- | --- | --- |
| web | 实际读过的网页/远程内容 | 标题/章节、段落、选文位置及文本 hash | 来源标题、原网页、读取时间；合法保存时可查看快照 |
| asset | 用户上传材料 | PDF 页码、表格 sheet/range、段落 ID | 附件预览对应位置 |
| content | 会话消息、生成内容、证据片段 | Item revision、block/span | 跳到对应内容；标明用户陈述/模型生成/外部证据 |
| artifact | 生成文件/报告 | artifact_version、页/单元格/文本行 | 打开成果预览、下载、版本 |
| workspace | 云端代码/文件 | workspace snapshot、相对路径、行号 | 文件查看与 diff |
| verification | 测试、检查和浏览器记录 | report/check/process ID | 测试详情、日志、截图或 trace |
| local | 已连接本地项目文件 | project/device binding、相对路径、版本、位置 | 本地文件/编辑器定位，断开或无权限时明确状态 |

代码路径以工作区为根，规范化后拒绝越界与经链接逃逸；行号绑定文件版本。页面更改或文档重排导致旧锚点失效时标注旧版本/定位失效，不悄悄跳到不相关段落。路径是定位信息，不是授权凭证。

Citation 含 citation_id、answer_item/revision/span 或 claim_id、reference_ids、support_kind、check_status；support_kind 区分原始证据、二手报道、用户材料、推导依据和执行证据。来源标题/URL 必须取自已登记对象；内容中的“忽略规则”属于资料，不能成为系统指令。

搜索摘要可作为发现材料，未读取正文时明确其证据范围，不能冒称核验全文。动态网页要求当前信息时重新获取/核验，记录取证时间；支持关系可由模型审阅，但不承诺普遍自动证明所有论断。引用过多时按关键论断覆盖组织，不靠堆链接证明质量。

前端通过 authenticated resolver 按 ref_id 解析可用动作，每次检查归属、删除和访问权限，再签发短期下载或代理预览；原始签名 URL 不作为持久引用。云端 /workspace/main.go 是内部定位，不直接作为用户电脑的文件链接。缺失、撤销、过期引用有明确状态，删除同时阻断派生索引和缓存。

本地引用由客户端 Local Resolver 根据绑定项目/设备解析，校验路径、链接边界及实际版本。网页需连接 Runner 才能读本地文件；用户明确保留的历史快照有独立身份，不能把离线快照冒充当前文件。

## 6. 工具设计：通用执行器与专业验证适配器

| 面向 LLM 的工具草案 | 所属模块 | 用途 |
| --- | --- | --- |
| references.resolve/read | Context | 核实来源和位置、读取获准内容 |
| workspace.read/apply_patch/changes/export | Workspace | 云端文件修改、差异与成果导出 |
| environment.inspect/ensure | Workspace | 检测能力、申请受控模板和项目依赖 |
| process.exec/poll/stop | Workspace | 受控命令执行、持续输出、取消 |
| verification.run/report | Agent + Tool + Workspace | 按 validator/范围运行检查并返回版本化报告 |
| browser.open/interact/capture | Workspace 浏览器适配器 | 沙箱应用预览、交互、截图/trace |
| tasks.verify | Agent Completion Controller | 汇总当前契约与证据，反馈缺口 |
| artifacts.publish | Workspace + Run | 将允许交付的版本登记并提供预览/下载，不代表公网部署 |

LLM 调用均经 Tool Runtime；工具名最终需按实际职责拆分 schema。process.exec 优先采用 executable + argv + workspace_ref + cwd + timeout + resource_profile；需要 shell 语法时显式 shell 模式，在同一隔离边界执行。限制进程树、资源、网络、凭据和挂载，不能只用命令关键词判断安全。

Go、Python、Node 等 ValidatorSpec 可登记说明、适用条件、所需工具链、参数 schema、命令构造、结果解析、证据格式、覆盖能力和限制。go test 是命令/验证能力，不必每条命令都变成单独 ToolSpec。验证适配器方便生成标准报告；通用执行器保留发现的新方法。无适配器时原始退出码与日志仍可保存，无法解析的统计保持未知，不填造通过数。

校验、安装和测试仍有副作用与成本，Tool Runtime 负责权限/失败治理，Workspace 负责执行边界。tasks.verify 是按需主动查看入口；每次申请成功结束时 Runtime 仍执行必要完成核验，不能因模型漏调工具而跳过。

## 7. 环境准备：预装工具链、按任务补依赖

以下模板方案适用于云端或受控隔离环境。本地项目优先读取现有解释器/编译器及依赖版本，获授权后只在项目范围准备必要依赖；原生执行的实际 OS 隔离能力必须说明。不自动 apt/yum 修改用户全局系统，所有安装和执行遵循独立的能力范围与审批模式。

建议采用分层环境，具体沙箱实现、发行版和版本另议：

1. 管理员维护有版本的基础环境模板，预装常用语言解释器/编译器、必要系统库及通用操作工具。可分 python、go、web 模板或在成本合适时组合，避免每次任务安装整套语言。
2. 每个任务从模板分配隔离工作区，根据项目清单选择版本与依赖。Python 在任务虚拟环境装包，Node 按锁文件使用项目包管理器，Go 按模块清单获取依赖；不能凭文件名无证据地忽略版本不匹配。
3. 缺少系统能力时 environment.ensure 提交结构化需求，由 Provisioner 选受控模板或执行受控扩展。超出开放范围返回 environment_unavailable，不自动扩大主 Agent 权限。是否支持多个语言版本由管理员目录决定。

apt/yum 等通常处理操作系统包，pip/npm 等处理对应项目生态依赖；Python venv 提供包环境隔离，不构成执行恶意代码的安全沙箱。任务代码、安装脚本、测试脚本都运行在单独沙箱；不能直接在 Python Agent Runtime 服务环境执行。

管理员维护的镜像构建/Provisioner 可以按既定策略安装系统包，普通任务进程默认无宿主权限。不把 root 凭据或第三方生产 API key 放入可读任务环境；确需外部访问使用受控代理/范围凭据。语言工具链的自动下载、包安装 hook 与构建脚本同样遵守网络/安装策略。

EnvironmentManifest 记录模板 digest、OS/架构、实际工具链与依赖版本、锁文件 hash、初始化动作/结果、网络策略和验证能力。准备失败返回 preparation_failed，区分工具链缺失、依赖失败、网络限制与项目代码失败。恢复重建环境需核对 manifest，不能把环境重新准备误称为结果复现。

下载/构建缓存按平台、语言版本、锁文件和配置隔离；私有依赖有账号可见范围。共享缓存以受控内容存储读取，不把一个任务可写缓存直接作为另一任务可信构建输入；缓存命中要在报告说明。已有 CACHE_DESIGN.md 的权限与失效规则继续适用。

后台预览进程有租约、日志和停止入口，浏览器只能访问许可环境/网络。临时预览链接有认证及到期时间，持久下载成果另存 AssetRepository；任务结束保存所需报告/成果后停止进程和回收环境。临时预览不等于已上线公网网站。

## 8. 代码工作实际链路

```text
用户目标 + 上传/已授权云端项目
→ 读取结构、项目规则、清单与现有测试
→ 按需制定步骤/委派 → 取得匹配环境
→ 修改代码 + 必要的功能/回归用例
→ 相关测试/构建/静态检查 → 观察真实失败 → 有界修复
→ 网页/接口任务按要求启动并验证关键流程
→ 合并后核对最终版本与验收证据
→ 发布代码/成果/diff/检查报告及未验证项
```

这是能力链路示例，LLM 按信息和结果选择动作，不要求每个代码任务固定跑所有检查。优先已有测试和实际受影响的功能；新增测试需能发现具体故障，避免复制实现或为低影响可逆修改增加无意义测试。独立审阅只在契约/任务需要时启动。

Go 示例可使用 go test -json ./... 并解析统计/日志；要求新执行或测试依赖未受缓存完整跟踪时采用 go test -json -count=1 ./...。报告区分缓存复用与实际新执行，不为了提高命中率跳过必须的验收。race/build/vet 按问题和支持环境选择，不默认所有任务全跑。

Python 示例在已准备的任务环境中运行 python -m pytest 等项目实际测试入口；pytest 并非 Python 标准库的必有组件，缺失应准备依赖或报告。Web 示例使用项目脚本做构建/测试，必要时浏览器验证交互，保存 screenshot/trace。一次启动或截图不能替代契约规定的交互断言。

测试退出码 0、没有测试、全部跳过、只构建通过、已有测试实际通过分别记录。测试数未知时不伪造；新增自测也不能证明所有用户需求覆盖。第三方线上效果只能根据实际授权执行结果核验，测试 mock 不冒充真实发布。部署属于独立授权动作，首版代码交付不自动部署。

## 9. 前端与首批协议验收场景

成果卡片展示：当前交付版本、预览/下载/查看变更、重要引用、适用检查的通过/失败/未运行/受阻状态及限制。详情展示命令、环境、测试统计、日志和证据；用户不用配置工具链或 API key。复杂版本/Agent 信息按需展开。

增加 verification.started/completed/stale、reference.unavailable、delivery.ready/revised 事件及 verification/reference 相关 Item；状态来自真实对象。检验进入 verifying 可映射“马上到终点”，但不能把没有依据的完成时间或进度百分比写死。

首批协议验收：授权本地项目可读取并运行现有测试，未绑定/越界路径拒绝；上传文件按页引用；本地/云端代码按版本定位；假引用被拒绝；网页可访问但不支持论断时不能通过语义核验；无测试/全部跳过不写测试通过；环境受阻不伪装代码失败；修改和合并后报告失效；最终版本竞争拒绝旧完成；子 Agent 通过但合并失败阻止成功；临时预览过期仍可下载持久成果；部分交付保留明确缺口。

## 10. 官方资料边界

Go 的结构化测试输出与测试缓存控制参考 [go command](https://pkg.go.dev/cmd/go)。Python 包环境与安装分别参考 [venv](https://docs.python.org/3/library/venv.html)、[PyPA 安装指南](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)。浏览器执行记录参考 [Playwright Trace viewer](https://playwright.dev/docs/trace-viewer)。

这些资料仅支持命令和工具能力；UAW 的完成契约、版本化报告、引用解析与沙箱/配置边界是自己的拟定架构。本文未安装语言环境、执行项目测试或承诺支持全部工具链。
