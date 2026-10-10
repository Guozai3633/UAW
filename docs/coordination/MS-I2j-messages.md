# MS-I2j：可分别转发给四个现有会话的提示词

日期：2026-10-10。四方沿用原目录和分支，固定 `ms-i2j-start`。
[完整包范围、接口责任、目录与验收](requests/A/MS-I2j-parallel-packages.md)。

这是开发开工基线；MS-I2i完整回归仍在收尾。B/MS-C7、C/MS-T2f、D/MS-R2f已经按组件接受，不重做原包。

## A：MS-I2j

```text
开始UAW Session A本轮MS-I2j：真实网页后台入口、用户控制、文件桥接与逐包集成。
继续E:/UAW、integration。读取docs/coordination/requests/A/MS-I2j-parallel-packages.md第1/2/3/4/8节、DISPATCH及docs/plan/sessions/A.md。B/C/D固定ms-i2j-start独立开发，B本轮转前端apps/web；不代替它们同步、切分支或重写提交。
连续完成四个里程碑：
M1先收尾MS-I2i原固定来源回归并复核失败，保留中断/原失败；结束前不修改本checkout运行代码、测试或契约，可先准备接口文档。随后交MS-I2j-stage-api.md，固定B所需最小HTTP/Item/Event及C文件桥接。解决当前Origin拒绝：仅localhost的真实浏览器会话/精确Origin/CSRF/退出失效，CLI Bearer兼容；管理员与用户分开，模型key和管理员token不进浏览器。
M2接网页提交→理解→已有单Agent循环→实际成果/逐项核验；稳定请求去重、有界后台执行及重启恢复。接真实人工审批/拒绝/取消、文本Markdown预览和合同要求的用户接受，普通Agent或页面不能直接completed。
M3把C原ToolCall/Spec/Context通过实际登记、审批/预算和RunnerPipeClient映射到D只读端；身份/设备/根/签名/版本/取消/期限分别复查。D的真实native确认独立接线，缺来源明确不可用；unknown先对账不重发。阶段SHA到即审阅接线，业务错误交原worker。
M4和B/C/D验实际页面、固定DeepSeek办公/学术材料及文件引用、审批取消、刷新重连和旧版本接受拒绝；保留全部模型尝试、失败和pending费用。逐包接受，最终里程碑回归。
只改A保留目录；apps/web归B、tool归C、Runner四文件及local_runner归D。默认用户固定模型，不开子Agent/DAG/写入安装exec。只读启用限显式本机开发配置和真实用户授权，不全局开flags、不冒称公网生产认证。MS-I2i收尾只更新旧验收与last_full，不能覆盖MS-I2j派发/归属/标签。
```

## B：MS-U1

```text
开始UAW Session B完整包MS-U1：真实最小Web工作区。本轮临时从Context优化转做前端。
继续E:/UAW/.worktrees/context、dev/context；干净后git fetch origin --tags、git merge --ff-only ms-i2j-start，核对HEAD等于标签commit，uv sync --frozen。失败保留现场，不reset/rebase。读docs/coordination/requests/A/MS-I2j-parallel-packages.md第1/2/3/5/8节、DISPATCH、session/B、Web技术设计和UI设计。
连续四项：M1在apps/web建立React/TypeScript/Vite/pnpm和独立锁，核验工具链；按已有schema/OpenAPI与实际routes建立类型客户端，交MS-U1-stage-client.md，不能猜服务器字段/未开放路由。M2做会话侧栏、聊天、输入框上方浅色自适应“AI理解的任务”、实际状态、审批拒绝/取消、文本Markdown成果预览和合同接受；原文是基准，模型从获准目录选择，Markdown禁用原始HTML/危险URL。M3按Item ID/revision和事件seq/cursor处理刷新/断线、去重与快照恢复；稳定turn_request_id，反馈丢失先查原Run，不重发。SSE未实现时显式分页轮询；敏感令牌/审批/权威状态不持久缓存，换身份清理草稿投影。M4类型/构建/必要测试与Playwright；A入口到达即接真实后端验证发送→理解→成果、审批/取消/刷新重连，mock与真实联调分开记账，缺依赖不伪报通过。
允许apps/web全部文件及其package.json/pnpm-lock.yaml/测试/客户端生成物、B requests/handoff；暂停新Context优化。可仅修原Context测试回执目录准备问题，不改断言/时限。Python锁、后端、schema、认证、全局文档归A。前端不暴露模型key/管理员token，不把未实现的file写入/exec/diff/子Agent显示可用。
M1/M2交阶段SHA后继续M3/M4，不等A最终合并；缺API继续独立页面和协议测试，真实联调记pending。最终MS-U1-final-wiring.md、源码及独立handoff提交，工作区干净，本包后停止。
```

## C：MS-T2g

```text
开始UAW Session C完整包MS-T2g：实际file.read工具、文件证据及恢复。
继续E:/UAW/.worktrees/tool、dev/tool；干净后fetch tags、merge --ff-only ms-i2j-start，核对HEAD/tag commit并uv sync --frozen；失败不reset/rebase。读docs/coordination/requests/A/MS-I2j-parallel-packages.md第1/2/3/6/8节、DISPATCH和session/C。
连续四项：M1消费现有ToolFileReadInput/FileContent与file.read契约，固定完整ToolSpec版本和file_access门槛；交MS-T2g-stage-file-port.md，明确C→A调用/恢复port：完整原call/spec/ctx→已登记command_ref/receipt_ref和实际RunnerReceipt，不从参数自授owner/approved/绝对根或shell权限。M2实现精确路由executor/verifier，沿原权限/审批/预算/一次发送；核对签名证据、原attempt/command、workspace/path/location、UTF-8/64KiB、整体与片段hash及cursor，Runner ok不能替代数据核验，兼容现有三工具。M3持久真实结果/来源范围/观察及使用量，恢复只查原登记和journal；unknown不重发，当前数据权限与新执行准入分开，欠费独立恢复。M4自己的55434真实SQL及临时测试根验证读取/分页/修改/旧摘要/坏签名/跨主体项目/撤销取消/并发/回复丢失/重启；基线已接受Runner或明确注入端口可独立测试，不依赖D开发分支，完整native用户授权链由A接线验收。
只改src/uaw/tool、C unit/integration、C requests/handoff。A负责实际控制端、角色/provider/公共契约/组装/flags；D负责本机确认，不直接导入其未合入私有代码。缺真实port明确不可用，测试适配器不登记为产品能力，不开写入安装exec、不改用户模型。
本worktree . ./ops/start-dev-db.ps1 -Session C，迁移并--require-postgres实跑，回执放ignored tests/.artifacts/C/MS-T2g，保留原失败。M1/M2阶段源码交出后继续M3/M4。最终MS-T2g-final-wiring.md、源码/独立handoff提交，工作区干净；本包后停止。
```

## D：MS-R2g

```text
开始UAW Session D完整包MS-R2g：Windows真实本机确认、目录选择与只读授权生命周期。
继续E:/UAW/.worktrees/runner、dev/runner；干净后fetch tags、merge --ff-only ms-i2j-start，核对HEAD/tag commit并uv sync --frozen，失败保留现场。读docs/coordination/requests/A/MS-I2j-parallel-packages.md第1/2/3/7/8节、DISPATCH和session/D。
连续四项：M1实现已有NativeConfirmationPort/RootSelectionPort的真实Windows选择确认适配，交MS-R2g-stage-native.md；优先已锁依赖/原生API，新Python依赖提案A。窗口展示账号/设备/只读范围/期限，用户亲自选择确认，取消/超时/无桌面明确返回，模型路径/布尔值不能代替授权。M2接PairingVerifier/LocalRoots/持久Ticket一次消费，绑定独立挑战、账号设备映射、当前key/角色/签名/document_hash/期限；Windows SID或PID不能自证UAW账号，绝对路径留本机，控制面仅不透明根句柄/签名selection。M3复用真实Windows IPC、ReadOnlyRunner和签名journal，接当前根身份/撤销/期限、owner/key/channel/Run/lease/fence；断线重连用新连接，unknown不重发，撤销阻止新读。M4临时测试根的native部件和实际双进程只读链，验证取消/错配/过期/重放/撤销/重启；清理随机OS凭据、管道和进程。真人确认单独准备可复现指南，未实际点击只标pending，不以自动化替身冒充真人授权。
只改D原workspace四文件、apps/local_runner/uaw_runner、D unit/integration及requests/handoff；A负责HTTP/认证/控制端/注册权威/公共契约/锁，生产账号来源缺失返回不可用。真实交互窗口可见，其余后台helper隐藏。仅只读，不写入安装exec、不全局开flags、不自行决定D01/D03或改用户模型。
M1/M2提交阶段源码后继续M3/M4；按需用本session55435，不碰别的库/项目。原始回执ignored tests/.artifacts/D/MS-R2g保留失败；最终MS-R2g-final-wiring.md、源码/独立handoff提交、工作区干净；本包后停止。
```
