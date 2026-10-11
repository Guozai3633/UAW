# MS-I2l 同轮并行续包：A8 后的页面、混合工具和原只读链

2026-10-11。正式发布后按本页与 DISPATCH 执行。A8已固定来源装配，86定向节点通过；生产文件到固定模型和成果尚未整链验收。B/MS-U3、C/MS-T2i、D/MS-R2i已交付组件，适合立刻续作，A无需独自承担它们所属模块。

| Session / 续包 | 范围 | A依赖与可立即独立做的工作 |
| --- | --- | --- |
| A / MS-I2l-A9 | 管理端 file provider/可用性发布、每Run范围、Context/成果、原审批HTTP和集成 | 先给生产准入/统一消费构造，再消费C路由与D执行证据；不代写前端/Tool/Runner业务 |
| B / MS-U3b | 网页本机启动/状态/停止、刷新与原身份、文件引用交付状态 | A7三个HTTP和DTO已固定，可现在实现，不等A9文件交付 |
| C / MS-T2i-b | 办公与文件工具的严格来源路由，原调用/结果/恢复隔离 | 下列私有组件输入已定义，可独立单元/SQL验证；A负责Agent/composition注入 |
| D / MS-R2i-b | A8原实例到真实只读命令/签名journal与恢复、等待边界和测量 | A8装配入口已固定，可用独立D数据库/测试目录验证；真人/实际页面由A后续组织 |

## 固定输入与执行规则

本次是 MS-I2l 同轮续包，不是 MS-I2m。续包执行快照 **ms-i2l-a8 / 06ff3ef56b68d391387bc7b154fa58ecb00571f9**，运行源码 **ms-i2l-a8-source / 16e0efaf6daff2fbbd0281473a8c6cc1f652d0e6**；原共同开工 ms-i2l-start / 8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0 保留不动。

先在自己原工作区检查干净，fetch origin --tags，按远端 DISPATCH 的续包发布记录核对上述两标签准确 SHA；使用 `git rev-parse 'ms-i2l-a8^{commit}'` 等带引号的 ref。只有本地当前 HEAD 是固定快照祖先时才 `git merge --ff-only ms-i2l-a8`；不合浮动 integration，不 reset/rebase/stash，不丢失自己的未合入提交。不能快进则报告准确 HEAD 与缺口，A先审阅来源。A不替worker同步或执行其环境。

本页与四份新提示词来自固定文档标签 `ms-i2l-a8-followup`，不在旧 A8 快照内。fetch 后先核对该标签与远端 SHA 相同，再用 `git show ms-i2l-a8-followup:docs/coordination/requests/A/MS-I2l-A8-continuation-packages.md` 和对应 messages 路径只读读取；不合并浮动 integration 来取说明。A7/A8已有契约可在执行快照内直接读取。

本轮源码/测试只能改自己独占目录；shared/schema/锁/flags/composition/backend归A。新接口首先交自己的私有 Protocol/阶段文档与源码，公共缺口提具名提案，不自行扩权限。保持原成功/失败/中断与独立handoff，不重做已接受组件，不自动进入下一包。

M1阶段接口和SHA到即交A，随后继续M2–M4；不等A整链完成才做独立模块。模块自己的SQL由自己实跑：B55433、C55434、D55435，凭据/环境独立；不用A配置或模型key。A先审阅/接线已到阶段，模块受影响回归各自跑，汇合全量A执行一次。缺源明确pending，不用fixture替代生产；受控测试与本人决定分别计数。

固定用户模型；子Agent/DAG/写入安装exec关闭；文件开关不自动打开，不代点本人native确认或成果接受。恢复只对账原动作和journal，unknown不重新执行。缺依赖不是零成本或已完成。

## B：MS-U3b

独占 apps/web、B requests/handoff 与B测试；继续 E:/UAW/.worktrees/context / dev/context。不要继续优化Context。

- M1：消费 `MS-I2l-browser-installed-v1.md` 的三个HTTP与严格 HttpRunnerLocalBegin/Get/StopResult、InstalledLaunchView。交 `HttpInstalledLaunchPort` 的 start/get/stop 私有前端签名与页面入口；不猜新目录API，不接裸路径/proof/approved。
- M2：本人点击“连接本机只读目录”才 POST 空payload，显示 starting/waiting_device/connecting/selecting_directory/ready 与失败、closed/unavailable。页面明确账号确认/系统目录选择/只读确认发生在系统窗口；202不表示授权，ready不表示文件Tool已可执行。可停止清理；有界轮询，退出/身份变化Abort并清除旧会话状态，不自动再次弹窗。
- M3：刷新沿身份隔离的原 launch id GET，pending/unknown保留原request_id/revision；丢启动回复且没有id时只能显式恢复原请求ID的POST，不生成新ID或刷新自动POST。有id先GET；丢stop回复先GET。相同账号新Web session不能接管旧实例。会话切换不得把设备状态变成执行权限；原成果与草稿/接受恢复链保持。
- M4：真实契约生成字段、类型/构建、必要单元与受控浏览器，覆盖双击、丢回应、刷新、退出/跨身份、超时/503/停止竞争及旧Review兼容；交准确dist每文件hash/独立handoff。A提供限时launch后做认证只读实连；native和接受由本人操作，未提供来源不算通过。

## C：MS-T2i-b

独占 src/uaw/tool、tests/unit/tool、tests/integration/tool、C requests/handoff；继续 E:/UAW/.worktrees/tool / dev/tool。不是重写原 ToolInvocation 或新的执行流水线。

设计目录建议 `src/uaw/tool/runtime_router.py`；首先按此契约固定C私有接口：

```python
class ToolResultReadPort(Protocol):
    async def read_result(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject: ...

@dataclass(frozen=True)
class ToolRuntimeRoute:
    tool_ref: Ref        # 完整 configuration Ref，含 ToolSpec hash
    provider_ref: Ref    # 精确原 provider 版本/hash
    facade: ToolFacade   # 已由A绑定原权限、审批/预算/executor/results的独立实例
    results: ToolResultReadPort

class RoutedToolRuntime:
    def __init__(self, registry: ToolRegistry, ledger: ToolLedger,
                 routes: tuple[ToolRuntimeRoute, ...], *, access: ToolAccessPort): ...
    async def discover(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...
    async def invoke(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...
    async def reconcile(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject: ...
    async def read_outcome(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject: ...
    async def read_result(self, action_id: str, ctx: TrustedExecutionContext) -> JsonObject: ...
```

- M1：冻结并验证1–128个显式routes、完整工具/提供方Ref、规格hash、唯一tool id/version；同registry和同原records store、原invocation存在且 `facade.invocation.access is access`，防止忽略Agent有效工具权限。不修改传入facade/invocation，不赋予角色/provider/flags。协议以现有五个方法输入输出契约为准，交阶段源码/构造及错误例。
- M2：discover沿共享当前access和原registry筛选已绑定route；不是LLM自动委派。invoke冻结原请求/ctx，用normalize选择唯一原facade，委托其已有ToolInvocation重新进行当前权限、审批、预算和dispatch；不能fallback、丢字段/Hash或自己生成action/attempt。不要新建一条绕过原服务的执行链。
- M3：reconcile/read_outcome/read_result从持久ledger原action/spec/ctx选择所属route，当前registry完整规格/提供方仍须相符，再委托原Reader。恢复不走新执行门槛或发命令；原结果正文授权失败不阻塞本来允许的独立账务恢复。没有route、错hash/provider/会话、登记版本变化明确拒绝，不扫描各provider“谁能读就用谁”。
- M4：自己55434实跑办公/file混合路由、审批pending/拒绝、取消/撤销、错provider/Hash、丢回应恢复零新执行、未绑定工具不可发现及Agent access不得替换；允许使用明确受控file bridge做组件测试，不称native已通过。只做受影响兼容，不重跑整套目录。交阶段/最终源码与独立handoff、原失败/不同节点和A消费示例。

A在Agent/assembly/composition实现structural消费与每Run绑定；C不修改这些A文件。私有Python类型若有具体兼容问题，先交具名提案与现有签名证据；不私加public DTO、deps或flags。

## D：MS-R2i-b

独占原local_runner/workspace四文件、D unit/integration/requests/handoff；继续 E:/UAW/.worktrees/runner / dev/runner。

- M1：消费A8 `MS-I2l-installed-file-sources.md` 与 `assemble_installed_file`，用独立55435实际Web/SQL拥有者、原installed factory/双方OS keys/真实Windows双进程连接与测试自己的临时根构造集成夹具。必要的provider连接元数据/初始文件flag必须明确是受控测试设置，新配置在新Run准入前固定，不能改旧Run固定配置或注册生产fixture；生产无来源不绕过。
- M2：沿原FileTool facade→用户审批→预算dispatch→RegisteredFileBridge→RunnerCommands→RunnerPipeClient→实际helper读一个自己的UTF8文件；复核原call/action/attempt/model/provider/owner/设备/root、签名回执和不可变原内容hash。不能直接读文件伪造执行、旁路approval或仅把route.ready当执行成功。记录具体期限/停止点；真实人类操作不自动触发。
- M3：丢原回复仅查询原journal并恢复已发生回执；结果恢复后原文件修改仍返回原已签名快照，读open/dispatch/预算不增加。取消/根或key撤销/通道停止/角色变化/原期限与版本变化在关键等待点拒绝；账务恢复与正文读分开。保留普通15/首次90/root120/原lease最早期限，不能因测试失败加时或删除断言。
- M4：分段记录callback完成、A source/approval查询、预算/lease、注册/发送、helper读、签名回执/恢复所耗时间与具体失败阶段，只记录有界元数据，不记录目录/proof/key/正文。A业务源码错误报A，D组件错误在自己目录修；阶段读链SHA/回执到即交A，不等所有场景。自己的SQL/OS/IPC必要回归和凭据/进程清理；不重跑已接受695全量。精确区分受控native输入、真实SQL/OS/IPC与真人验收。

## A：MS-I2l-A9与滚动集成

- 先提供真实 file provider 管理配置/可用性与每Run精确workspace准入；未有有效owner/root/role/model来源不给capability。原固定配置不可追改，运行中管理员关闭仍拒绝。新增public接口先固定DTO与契约后给B消费。
- 使用A8装配及C独立路由，Agent有效access贯穿每个工具原Invocation；原审批HTTP按持久request/action/完整ctx选择所属service，结果读和账务恢复分别用所属Reader，不设默认allow。
- file material原origin→低信任Context→固定用户模型→准确引用/Artifact/逐项Verification/接受；实际期限与取消/版本复查，unknown不重发。
- M1接口/M2阶段SHA到即审阅接线，业务错误返原worker；不等待三包齐。真实页面本人新授权与固定模型样例在来源实际装配后组织，全部失败/用量/pending费用保留。阶段通过不等于本轮完成，产品汇合后一次全量。

## 验收与发布

每个续包至少交接口/阶段源码、最终源码和独立handoff；回执写明不同节点、历史失败、是否SQL实跑、真实/受控边界、资源清理和待A接线。公共接口修改由A发布兼容阶段；源码标签不移动。B/C/D可并行开工，A在同一时间推进自己的A9来源/准入，不独自代写三个模块。
