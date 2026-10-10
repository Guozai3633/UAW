# MS-I2l：首次本人授权、资料消费与页面恢复

2026-10-10。共同开工标签 `ms-i2l-start`，准确SHA **`8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0`**，与远端标签精确核对；不能用浮动integration代替。开工标签不移动，后续接口用独立阶段标签。A/D 必需接口先固定在 [AD-contract v1](MS-I2l-AD-contract.md)，实际源码 `6277fd12c238629c1d5d998b7c83aeaeeb539ed6`。

## 1. 来源与未完成门槛

上一轮B/MS-U2及三个修复、C/MS-T2h、D/MS-R2h最终源码/handoff均已正常合入A。真实办公成果已本人接受且独立Run completed，重启复读没有模型重发。学术已生成正文/逐项核验，最近回执仍等待本人接受；不能替用户操作。首次证明管道已实际验证，但完整installed首次等待、真人目录授权、文件→Context→固定模型→成果和浏览器审批拒绝取消、汇合全量仍未完成。MS-I2j/MS-I2k不能标整轮accepted。

本轮不是让worker重做旧组件。B修实际刷新/身份/恢复与设备状态页面；C在已有单文件Reader之上做有界多资料消费；D扩展首次等待和初始化取消；A接真实源及最终跨模块。纯组件工作可并行，不要求真人门槛已通过才开工。

## 2. 独占目录和基线同步

| Session/包 | 工作区/分支 | 本轮开发目录 |
| --- | --- | --- |
| A / MS-I2l | E:/UAW / integration | 原api/run/agent/model/infrastructure/composition/shared及A测试、ops、全局文档；不改worker业务源码 |
| B / MS-U3 | E:/UAW/.worktrees/context / dev/context | apps/web与B requests/handoff；暂停新Context优化 |
| C / MS-T2i | E:/UAW/.worktrees/tool / dev/tool | src/uaw/tool、tests/unit/tool、tests/integration/tool、C requests/handoff |
| D / MS-R2i | E:/UAW/.worktrees/runner / dev/runner | apps/local_runner/uaw_runner、session/D原列明workspace四文件、D测试/requests/handoff |

worker自行检查干净→fetch origin --tags→通过 `git show origin/integration:docs/coordination/DISPATCH.md` 只读核对本轮正式发布准确SHA→merge --ff-only ms-i2l-start→HEAD等于标签commit→按锁同步独立环境。正式发布回执是标签之后的文档元数据，基线内“准备待发布”仅保留当时状态；已核对本轮远端发布与精确SHA后，不因旧准备字样再次停工。不要合并浮动integration源码代替基线。同步失败保留现场，不reset/rebase/stash。A不操作worker工作区。公共DTO/锁/权限/flags归A；有缺口交具名提案，不私加授权字段。模块SQL各自55433/55434/55435，A55432，不能复制A配置/凭据。

## 3. A / MS-I2l：真实来源与装配

| 阶段 | 连续任务、目标 | 设计/实现目录与交付 |
| --- | --- | --- |
| M1 | 基线已具备原policy/progress与factory复核。继续每次真实启动的安装配置/locator、当前用户与OS实例/双方keys/原挑战来源、具体paired factory；先交worker需要的消费示例和生产缺源错误 | infrastructure/enrollment_*、run、composition；阶段接口与源码。原15秒/首次90秒不可由body切换 |
| M2 | 消费D等待/stop实现，原证明管道→native owning journal→complete→实际ReadonlyHelper；localhost可达、受保护设备状态及当前file route/root/data authority装配 | api/infrastructure/composition；真实Windows双进程及同用户HTTP，模拟Yes与真人分开 |
| M3 | 单文件及C有界多资料→低信任Context→固定用户模型→成果/准确引用；unknown先读原journal不重发，撤销/取消/模型与提供方版本在等待后复核 | agent/context A adapter/产物；不得直接Blob/SQL绕C Reader，缺根不读目录 |
| M4 | B实际页面刷新/身份恢复、原学术接受、办公/学术文件、审批拒绝/取消/用户接受；记录全部模型尝试/失败/用量/pending费用。阶段逐包审阅，实际消费者汇合后一次全量 | A跨模块测试/真实回执/全局接受说明；上次1691保留旧来源 |

用户必须实际选择本机目录和接受合同成果。自动审批服务拒绝时保留动作与原因，不绕过。实际来源没齐明确503；不能把fake current registry或受控native作为production装配。

## 4. B / MS-U3：当前会话恢复与真实状态

M1：修实际页面刷新会自动选最新会话的问题。URL `?conversation=<id>`、当前用户、服务端可见会话必须一致；缺失/越权/注销不显示旧内容。草稿按身份/会话隔离，刷新只读、不自动提交。阶段交UI入口/恢复签名和源码。

M2：消费已有enrollments四HTTP显示实际pending/active/revoked/unavailable，留原请求/版本绑定；不猜root授权API。A新launch/状态接口仅在正式阶段DTO到达后接入；可先做可注入的明确unavailable UI和受控组件，不等A完整native链才继续。关联文件引用/完整Markdown/核验限制，pending不表示已授权。

M3：原提交/接受unknown恢复、撤销或身份变化、过期Run/成果hash、切换会话和取消竞争。保留原request_id，未知先查询。现有全局一次Recovery只能对原请求，明确返回该会话；本轮不私自扩展多Run调度。完成只取服务端Run与独立接受回执。

M4：必要单元、契约生成器字段保留、类型/构建/受控Chromium及A可达服务真实联调。只使用A限时launch，禁止读取私有配置/凭据；受控与实际页面分计。A使用B交付构建物，不执行worker环境或替B安装。设计目录沿apps/web/src/lib/api、features/workspace/review、tests/unit/e2e；本人确认不能由Playwright替点。

## 5. C / MS-T2i：有界多资料消费与恢复

单文件 `FileMaterialAdapter.export/read` 已实现并验证，不重新发明。新能力是一次消费若干**已存在的完整material Ref**，用于比较材料，不新执行file.read、不并发打开文件、不增加权限。

M1：在C私有模块固定 `FileMaterialSetLimits`、冻结 `FileMaterialSet` 和 `FileMaterialSetAdapter(reader, limits=...).read(refs,ctx)`：输入为1–8个完整Ref tuple；默认集合正文总量≤16384字符、≤65536 UTF-8 bytes，允许更小正界限；保持输入顺序，重复Ref拒绝，不截断或拼接正文。输出冻结tuple[FileMaterial,...]，沿每项原refs/Usage，不新增public DTO/裸正文cache。先交MS-T2i-stage-interface.md及源码，A按签名消费。

M2：实现逐项owning Reader与返回前来源复核；等待中撤销/错版本/缺项/超总量整体拒绝、不返回部分材料。不能承诺所有模块全局原子授权快照；最后复核之后发生的撤销无法收回已返回字节。重复读取没有新attempt/预算/execute/open，也不把metadata缓存当权限。

M3：原多材料/单材料的丢回应、重启与数据拒绝；费用恢复独立允许时仍可处理已接受原计划，不能反向获得正文。精确full-file/fragment/material hash分别保持，等待后当前来源变化拒绝。A production bridge到达后按完整call/provider/ctx/命令回执复核，业务错误在C范围修；缺A来源明确pending。

M4：自己的55434实跑受影响SQL和新边界节点：两材料顺序/重复、读取第二项期间第一项撤销、UTF8总量、跨主体/provider、重启零新执行、账务独立恢复。单文件/办公工具只按受影响兼容复跑；旧369/81不计新覆盖。设计目录src/uaw/tool/providers/file_material_set.py、C测试；既有FileMaterialReaderPort保持兼容。交完整构造/关闭或无资源声明、失败回执、去重节点清单与最终源码/handoff。

## 6. D / MS-R2i：首次等待、初始化取消与真实装配

M1：严格实现AD-contract的兼容start(first_start,on_progress)与HelperBootstrapProgress；普通15秒、首次原policy最长90秒、一次waiting、固定ready返回。所有读帧/回调共用单绝对deadline，源变化不延长。M1阶段SHA到立即供A接线。

M2：helper_host在factory.create期间监听stop/EOF；取消初始化、native自有窗口、迟到helper/线程/句柄/管道，close幂等。拒绝、期限、错hash/多waiting/伪ready/进程退出及长native等待受控验证。真实隐藏Windows双进程和随机凭据清理；模拟长等待不等于本人授权。

M3：消费A固定installed首次factory/受保护原proof/current key和登记，实际helper连接→本人根选择→一次read→原签名journal；丢回复/新连接只恢复原command，不新执行。A源缺失不能fixture补生产；不自建账号HTTP、不从SID/PID推UAW用户。

M4：真实Windows/双进程/取消与重启、本人操作指南和原journal恢复证据，逐项区分受控/真实本人及缺A生产源。设计目录helper_process.py/helper_host.py/native/runtime/ipc及D原tests。只回收自有进程，不访问未经本人选择的目录；写入安装exec关闭。最终源码/handoff分开，停止在本包。

## 7. 并行节奏和接受

四包连续M1→M4，不在M1交接口后自动停包。M1发布阶段接口，M2交可运行阶段SHA/样例后继续；A阶段到即审阅接线，不等三包齐。公共提案A优先处理，业务错误交原worker，A不改worker业务目录。共享接口如变更发布独立兼容阶段，不移动ms-i2l-start。

每包包括实际源码/交接两个提交、变更范围、锁定输入、构造/调用/限额/关闭和错误样例、每个测试节点最后结果、全部失败修复、生产缺口/回退。组件接受、真实消费者接受、本人操作、全量分别记录。缺Docker先启动自身DB并迁移，SQL不能仅收集；受影响先跑，全量只在A汇合里程碑一次。

默认固定用户模型；不启子Agent/DAG/本机写入安装exec，文件flags不自动打开。费用pending金额是持有额度，不是实际账单。本轮增量不是完整产品通过，不重复旧真实模型任务来制造调用数。
