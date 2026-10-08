# 本轮可直接转发的消息

日期：2026-10-08。统一固定版本 **ms-i2c**，三个包互不依赖其他 worker 尚未合入的代码。继续使用原聊天和 worktree。

先确认工作区干净，再 `git fetch origin --tags`、`git merge --ff-only ms-i2c`，确认 HEAD 等于 `git rev-parse 'ms-i2c^{commit}'`。失败保留现场并报告，不 reset。依赖按新锁同步：`uv sync --frozen --extra agent-engine --link-mode copy`，缓存设在自己 worktree 内。不得复制私有配置、凭据或数据库 URL。

## 发给 B

```text
开始 UAW Session B 的 MS-C3。工作目录 E:/UAW/.worktrees/context，分支 dev/context。干净后 fetch origin --tags、merge --ff-only ms-i2c，核对 HEAD 与标签解析的 commit 一致，按锁同步依赖。
先读 docs/coordination/DISPATCH.md、docs/plan/sessions/B.md、docs/coordination/requests/A/MS-I2c-ports.md。
在 src/uaw/context/model_input.py 实现 ModelInputPort.resolve(ref, ctx) -> ModelPrompt。A 已明确 ModelPrompt 为公开结果，允许只读导入 uaw.model.contracts.ModelPrompt，不导入 ProviderRequest/Response。使用已有 Repository/Composer/Reader/InstructionSet，读取固定快照、实际来源、指令和 ModelToolSet，复核当前权限、依赖版本、epoch、取消与期限。保持指令和数据身份，保留用户原文；消息和工具 schema 都计入完整输入估算。agent_step 不使用理解专用模板；缺能力 Reader 或 authority 明确不可用，不假造空工具。
只改 B 允许路径，包括 model_input.py 和 B 测试。seed.py、intent.py、Model、组装根、共享文件和锁归 A；输入路由及生产 authority 由 A 后续接线。补组件和真实 SQL 用例：重启、跨 Run、来源删除/撤销、规则/工具/epoch变化、材料注入、窗口不足及取消。SQL缺环境可交 A 运行，不把收集成功记为通过。
提交实现与 B handoff，记录实际基线/提交 SHA、接口样例、验证命令、失败项和接线要求。范围是 MS-C3 组件，完整 P1-02/Agent 运行不自行标 accepted。
```

## 发给 C

```text
开始 UAW Session C 的 MS-T2b。工作目录 E:/UAW/.worktrees/tool，分支 dev/tool。MS-T2a 已由 A 合入并验证。A 修复 ProviderBinding 状态 active 兼容，并发布 pending Usage 可省略所有未知维度的公共契约；这些变更随 ms-i2c 同步，勿带回旧 connected 字段。干净后 fetch origin --tags、merge --ff-only ms-i2c，核对 commit 并同步锁。
读 docs/coordination/DISPATCH.md、docs/plan/sessions/C.md、docs/coordination/requests/A/MS-I2c-ports.md。
消费真实 BudgetStatePort（BudgetService 已实现），替换 Tool 对 budget.* 私有记录的直接读取；消费 ExecutionPolicyPort 统一父链决策，同时保留 Tool 的角色/资源/配置校验。恢复读不产生准入授权，后续写仍 CAS；取消/过期后的原尝试账务清理与新动作准入区分。
实现 ToolReceiptReaderPort 驱动的结果核对。使用严格 ToolReconciliationReceipt，校验 action/attempt/provider/receipt 绑定、usage.attempt_id、实际证据和版本。效果与费用分别处理，unknown 不重发；not_applied 不代表零费用，不从超时或未记 dispatch 推导未执行。固定核对计划和回执持久化，CAS 去重，不持有 Tool 会话锁调用 BudgetService。
补真实 SQL 重启、响应丢失、重复/冲突回执、并发核对、撤销/取消、无Reader及未知额度保留用例。测试 Reader 明示受控组件；没有生产 Reader/executor 返回不可用，不启用 flags、工具目录或真实 dispatch。只改 C 允许目录，公共缺口交 C requests。提交源码和 C handoff，附实际基线/提交/测试/接线要求。完整 MS-T2 继续等待。
```

## 发给 D

```text
开始 UAW Session D 的 MS-R2b。工作目录 E:/UAW/.worktrees/runner，分支 dev/runner。MS-R2a 已由 A 合入并验证，包含真实 Ed25519 和跨进程单次消费。干净后 fetch origin --tags、merge --ff-only ms-i2c，核对 commit 并同步锁。
读 docs/coordination/DISPATCH.md、docs/plan/sessions/D.md、docs/coordination/requests/A/MS-I2c-ports.md。
消费共享 AsyncRunnerAuthorityPort.current(command, *, authenticated_principal) 和严格 RunnerAuthoritySnapshot。在 D 的 workspace/contracts.py 定义 typed wrapper，在 Runner 增加异步 admission 入口，保留旧同步入口兼容。认证主体来自可信通道适配器，不能读取 command 的主体来自证；设备到用户映射须真实关系校验，缺映射/authority/IPC不可用。
全部字段与固定 command 声明比较，await 后重新取时钟检查期限；关键外部检查后再次查询当前权威，复核取消、key/root撤销、request/parameters/policy/workspace版本、flags、lease与fence，最后执行 admission CAS。禁止 asyncio.run 桥接、阻塞事件循环或缓存执行许可；取消及时传播。
测试异步期间过期、撤销/版本/主体变化、schema缺字段、错误通道主体、协作取消、并发/重启 admission，保持真实签名检查。测试 authority 明示组件来源，缺生产服务不挂载网络入口。
本轮不发布配对V2，不把内部 Ticket.document 签名重解释成公开协议，不决定 D01/D03/D06，不安装/写文件/exec。只改 D 允许目录；提交源码和 D handoff，列实际基线/提交、验证回执、缺口及接线要求。完整 MS-R2 继续等待。
```

## A 同时进行

A 维护公共契约、实际配置与权限所有者、Model 输入路由、Runner 服务端 authority/租约/设备关系接线，并逐包审阅交付。独立包达到合入条件就先合入，具体依赖的组合检查才等待对应包。后续公共变更另发固定版本，开发中不混用接口。
