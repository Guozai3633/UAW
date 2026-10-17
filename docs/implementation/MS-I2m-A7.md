# A7准确发布来源

2026-10-17，**ms-i2m-a7-source / d46f85d712161f77086610a15e225b294164a8de**。314不同节点通过，组件接受和实际产品pending按逐包回执；下文“待发布/待审批”保留为原始准备历史。需要复验时核对远端DISPATCH准确SHA，只消费固定tag，不合浮动integration。没有下一包或自动同步指令。

# A7 最新：组件与受影响链路验收通过，待固定源码发布

2026-10-17。B/MS-U4组件、C/MS-E1 M1–M3、D/MS-K1及D目录定向修复均已审阅并普通合入。**314个不同最终节点通过**：71 SQL、190单元、53受控Chromium；33个变动Python文件Ruff/格式、240源码类型通过。不是全仓或产品整轮通过。[逐包验收](../coordination/requests/A/MS-I2m-A7-worker-acceptance.md) · [完整去重/来源/失败回执](evidence/ms-i2m-a7-integration.json)。

审批服务现已恢复。实际D时钟、A原队列/Model Gateway/补充协议联调通过；原A6严格跨墙钟节点在A7修复后通过。A新二次澄清fixture补齐队列推进；D自己修正干净目录父目录建立，原47准备错误保留；B原53启动错误在匹配Chromium缓存补齐后复跑通过。所有原回执不删除，不累加重复节点。

B实际新服务/原Page、固定用户模型与实际elapsed wait、C实际候选/基线导出及真正人审、H02本人体验仍pending；Tool实际claim和新审批尚未消费执行段，继续保守拒绝。原H01-v5/本人记录/费用/flags/last_full保持。准确固定源码由远端DISPATCH正式记录；以下是本段早期准备状态的原始历史，不再代表最新门槛。

# MS-I2m A7：续跑期限修复、Tool 时间接口与阶段合入

2026-10-17，A / E:/UAW / integration。**本段仍在本地集成，尚未发布 A7 固定标签。**

## 1. 已做的工作

A 自有源码提交 `096be27`：

- 修复 `ConversationResumer` 的条件位置。没有显式执行段时仍检查原墙钟；有实际执行段时由原时钟、历史和剩余额度决定新调用期限。当前 open 问题始终阻断，不能因安装执行段而跳过。
- 原长等待夹具补齐恢复器的时间来源，先复现 A6 会拒绝的问题。以前仅前移 Agent、队列和执行段时间，没有前移恢复器时间，旧回执不能证明这处检查正确。
- 新增内部 `ToolDispatchTimingPort` 和 A 的 `RunToolDispatchTiming`。它们只是可供后续 Tool 原 worker 消费的来源接口，**ToolLedger 当前尚未消费，不宣称工具已支持长等待续跑**。
- 本地网页代理保留 `X-UAW-Schema-Version`，拒绝重复版本头；原 Origin、cookie、CSRF 和独立测试服务边界保留。当前后端也允许未带版本头的读取，不能把补传版本头描述成已经复现的接口失败。

本地已普通合入两个阶段，保留 worker 原提交：

| 阶段 | 原源码 / 接线提交 | A 合入提交 | 当前结论 |
| --- | --- | --- | --- |
| B MS-U4 M1 | `1e3447853b4d068955728b43099beb07d74ffac9` / `7676b135f670fa87409378ae9361ef4a6d3a8dd3` | `9949521` | 客户端和生成器已审阅、已本地合入；A 前端实跑及新服务联调 pending |
| D MS-K1 M1/M2 | `81d8f9989fc5825c531f9c568cf7898b1252a841` / `aae77f0c0e8190677a0af9bd63f9972422f6f896` | `5815c2abcffbf1f7110a8a273580bffd9573144f` | 接口与实现已审阅、已本地合入；A 原队列汇合 SQL pending |
| C MS-E1 M1 | `49d3fbfeaa1ec5a3aedcb1becccd1d5fa4683eee` / `5096a2c5816532efff729c612c3004a5723bf982` | 尚未合入 | 已收到严格离线接口和源码，原 MS-E1 M2/M3 继续 |

接口审阅、本地合入与整包验收分别记录；没有把 B/D 的阶段审阅标成整包 accepted。

## 2. Tool 时间来源的实现策略

准确接口和构造见 [A7接线说明](../coordination/requests/A/MS-I2m-A7-wiring.md)。端口只返回 None 或抛异常，不返回可供模型自行修改的 deadline。

适配器加入原 Tool claim 的 `RecordTransaction`，核对实际数据库、会话绑定、owner 和活跃事务。先取得原 `conversation:<id>` 事务锁，刷新当前 Run、ledger、conversation 及已显式安装的段/clock/binding，避免等待前 ORM 缓存的旧取消状态。锁顺序为 `tool-run → conversation`，反向获取禁止；锁内没有网络、模型、本机或嵌套事务。

实际当前来源验证 schema/修订、原会话/任务/主体、取消、超额和 Run 可执行状态。显式注入 segments 时调用 A6 的历史来源证明，结束时再核对实际时间；缺段或旧上下文保持过期。缺注入时沿用原 Run、ledger 和调用的最早截止时间。适配器不写 Run/预算/时钟，不签发段，不发送工具，不替代权限、审批、资源 Reader、reservation 或效果账本。

**尚缺的消费点：** ToolLedger 的原 claim 仍使用原账本期限；ApprovalService 对新审批的创建和读取也仍使用原账本上界。旧审批必须维持原期限；未来消费要区分“新段内新建审批”和“恢复旧审批”，不能统一延长。C 当前负责独立评测，本说明不扩大其目录或自动派发 Tool 修改。

## 3. 目录与验证

| 位置 | 职责 |
| --- | --- |
| `src/uaw/shared/tool_timing.py` | 内部时间检查协议，不改公开 DTO |
| `src/uaw/run/tool_timing.py` | 实际 SQL 来源、原事务锁与同源时间证明 |
| `src/uaw/run/conversation_resume.py` | 正确区分原期限和已证明执行段；当前问题阻断 |
| `ops/serve_existing_web.py` | 原代理传递显式版本，拒绝重复头 |
| `tests/integration/agent/test_tool_timing.py` | 旧上下文、取消后刷新、缺段、原事务回滚等 |
| `tests/integration/agent/test_execution_segments.py` | 统一受控时间，复现并覆盖旧恢复入口遗漏 |
| `tests/integration/agent/test_owned_clock_continuation.py` | 新增真实 D + A 队列/模型/补充汇合测试，尚未执行 |
| `tests/unit/agent/test_pinned_web_server.py` | 实际随机 TCP 端口、版本头、身份与 Origin 边界 |

最终已通过 **21 个不同 SQL 节点 + 14 个代理单元节点**。首批 SQL 19 通过/2 失败；修复非法 EventPayload 测试数据，以及“纠正会使旧问题 stale”的错误夹具假设后，仅复跑原两个节点通过，不重复累计。原长等待复现失败、两次代理临时目录准备错误均保留。详见 [机器回执](evidence/ms-i2m-a7.json)。

当前合入快照的严格 Mypy 233 源码通过，8 个 A 变动源码/测试的 Ruff 与格式通过。此前仅检查 `src/uaw` 漏掉 Runner 源码根导致类型错误；采用项目原命令同时检查 `src/uaw apps/local_runner/uaw_runner` 后通过，未增加忽略项。

## 4. 未执行的汇合门槛与实际停止点

真实 D + 原队列的三个测试已写好，覆盖暂停后的原任务续跑与停止、两次等待不重领主动额度、同事务失败回滚；使用实际 D 算法和真实 SQL、受控 provider/服务时间。**它们还没有执行结果**，不能计入通过数，也不能作为真实 elapsed wait 或 DeepSeek 质量证明。

执行命令提交自动审批时，服务因账户用量限制无法完成审查；该命令未启动。这不是测试失败，也不是动作被判不安全。当前不改用其他执行路径绕过审查。后续数据库汇合及 Git 固定版本发布需待该服务恢复，当前没有 `ms-i2m-a7-source` 或远端 A7 准确 SHA。

恢复后依次完成：A/D 汇合 SQL；B 阶段前端受影响验证；C M1 审阅合入并确定实际观测导出；发布准确 A7 源码/标签和各阶段验收结论；独立新候选服务及 B 实测。worker 保持原连续 M1–M4，不读取其未提交源码或操作其分支。

默认真实 clock/segments 仍未装到用户测试服务；H01-v5、原用户记录、模型费用/pending费用、flags 和 last_full 保留。没有新真实模型调用，没有本人确认/接受代操作。
