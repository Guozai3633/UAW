# MS-I2a：审批与 Runner 签名公共基础

日期：2026-10-07。范围：开发组件接线；完整 MS-I2 / P1-03 / P1-04 仍在开发中。

## 已落实的内容

- `run/approval.py` 将固定动作、参数摘要、资源版本、可信上下文、Run 配置和审批政策保存到真实 PostgreSQL。人工决定与事件在同一事务提交；同一 action 在同一 Run 中只有一个审批身份。
- `approvals.get` / `approvals.decide` 使用现有认证入口。决定要求所属用户、预期版本、参数和资源匹配；拒绝/取消不能被新的 request_id 改成批准。相同决定请求重放历史回执，执行仍必须读取当前状态。
- `recheck` 核对 Run、预算取消和期限、当前执行政策、固定与当前审批政策、原动作/上下文及注入的实时动作权限。已批准不代表取得新权限，也不代表已经执行。
- 新增 `ApprovalPort`、`ApprovalAuthorityPort`、`BudgetPort`。`BudgetService` 原有真实 SQL 预留/dispatch/结算/释放实现不变；类型检查验证两个服务实际满足公共 port。
- `runner_signatures.py` 提供真实 Ed25519 签名/验证和有界 JSON 字节规则。cryptography 成为直接锁定依赖；RunnerReceipt 的成功、等待、失败/取消分支改为互斥，取消分类固定为 cancelled。
- A 因公共 schema 收紧，调整 Runner 回执入口的错误映射：结构错误仍返回原有 `schema_invalid` DomainError，不让提前发生的 Pydantic 错误泄漏。没有更改 D 的执行策略或测试预期。
- 使用既有 RecordStore 表，不新增迁移。审批创建/决定使用会话事务锁；查询和复核使用不生成幂等请求记录的实时事务读取。

## 明确边界

默认组装的 ApprovalService **没有 Tool 动作权限适配器**，创建/批准返回不可用；查询已有记录和拒绝仍可使用。测试中注入的 SQL 动作读取器只验证持久身份/资源变化，不能代表真实 ToolSpec、角色、提供方或本机权限已经接线。

本包支持 **manual + approve_once/decline/cancel + 空规则政策 + 无父政策的已授予 Run 权限**。assisted/automatic、持续授权、规则评估、父政策链、项目作用域都明确不可用，不能忽略政策后放行。审批有效期不得超过 Run/上下文期限；过期、取消、结束会持久更新审批版本。当前政策/资源变化由执行前复核拒绝，查询不保证主动刷新所有外部状态。

单次批准绑定一个逻辑 action；它不提供跨进程 dispatch 去重或副作用证明。C 必须将 action、attempt、调用意图、实际回执和结算写入持久账本。复核和实际发送之间的租约/fencing，以及按当前撤销停止执行，仍需 Tool/Runner 实际适配器落实。

Ed25519 原语不等于配对或 IPC。D 需要可信实时密钥目录、私钥保护、挑战证明、一次码/nonce 持久状态及本机确认。默认 Tool/Workspace 公共 Runtime 仍未绑定，能力 flags 保持关闭；不开放安装、文件写入和进程执行。D01/D03/D06 未替用户决定。

## 验证

本包新增 14 项 SQL/组装/审批/API 检查和 15 项真实加密/回执检查，最终 **251 passed，0 failure/error/skip**；Ruff/格式通过，Mypy 覆盖 77 个源码文件。全量回执和源码匹配见 [JUnit](evidence/p0-tests.xml)、[环境/源码摘要](evidence/environment.json)。验收包括服务实例重建后读取、CAS 并发、重复请求、拒绝、参数/资源/动作变化、权限及审批政策撤销、取消/过期、主体伪造、期限扩大和缺适配器拒绝。

```powershell
./ops/check.ps1 -WithPostgres
.venv/Scripts/python.exe ops/capture_environment.py
.venv/Scripts/python.exe contracts/check_interfaces.py
```

## 接续

拆出可独立开发的 **MS-T2a / MS-R2a**，共同基线使用新固定标签 `ms-i2a`。B 的 MS-C2 可以继续使用已发布的 `ms-i1`，无需中途切换；交付后 A 在新集成版本组合验证。MS-T2 / MS-R2 的完整真实执行依赖仍等待 MS-I2，详见 [公共接线说明](../coordination/requests/A/MS-I2a-ports.md) 与 [派发记录](../coordination/DISPATCH.md)。
