# MS-I2c：公共消费接口与下一轮边界

日期：2026-10-08。发布版本 `ms-i2c`。本文件是 A 对 C-002 和 D-R2a-001 的接线决定；worker 原提案及回执保留。

## 1. 预算读取：已有真实实现

位置：`src/uaw/shared/ports.py` 的 `BudgetStatePort`；实现：`src/uaw/run/budget.py` 的 `BudgetService`。现有 `Container.budgets` 同时满足读写两个 port。

| 方法 | 输入 | 返回 | 拒绝与约束 |
| --- | --- | --- | --- |
| `get_ledger(ctx)` | 内部可信上下文，必须有 Run | `RootBudgetLedger` | 主体、会话、任务不匹配拒绝；当前项目作用域尚不支持；不存在统一 `resource_missing` |
| `get_reservation(reservation_id, ctx)` | ID、同一可信上下文 | `BudgetReservation` | 再比较所属 Run、operation、trace、attempt；跨尝试返回 `attempt_scope_denied` |

一次 SQL SELECT 读取所需记录，使用同一 MVCC 观察点；返回当前 revision，检查行 revision 与 DTO 一致。查询没有写入、授权或延长期限。允许取消/过期后查询原尝试，供释放或核对；实际准入和 dispatch 仍走原 `BudgetPort`。读后状态可能变化，写操作必须 CAS。

C 的 MS-T2b 必须注入读 port，不再直接查询 `budget.*` 私有记录；缺 port 明确不可用，不能改回越过接口的读取。业务调用账本仍由 C 持有。

`Usage.resources` 为 pending 时仅币种必填，未观察维度省略；未知金额不能写成 0。estimated/confirmed 保持完整 ResourceVector 必填。BudgetService 对每个省略维度继续保留原预留额度；这一点不改变既有结算实现。

## 2. 工具结果核对：有契约，尚无生产 Reader

`ToolReceiptReaderPort.read(receipt_ref: Ref, ctx) -> ToolReconciliationReceipt` 是内部可信注入接口。完整对象见 [ToolReconciliationReceipt](../../../api/objects/ToolReconciliationReceipt.md)。字段全部必填：

`action_ref, attempt_id, provider_ref, receipt_ref, outcome, evidence_refs, usage, observed_at`。

- outcome 为 applied / not_applied / unknown；两个确定结论至少一条证据，未知可为空。
- Reader 校验提供方实际来源、主体权限、版本/摘要、签名或协议完整性；模型输出不能冒充回执。
- C 比较固定动作 Ref、实际尝试、固定提供方及读取 receipt_ref；usage.attempt_id 必须相等。对证据重新检查访问与固定版本，不能只看有 Ref。
- outcome 与费用分别核对。未应用不意味着零费用；费用 confirmed 也不意味着业务已应用。
- 不从 timeout、账本未记 dispatch、HTTP 200 或预算释放推导未应用。unknown 禁止另起尝试重发写动作。
- 跨服务核对采用固定请求计划、CAS、持久回执、重放去重；不持有 Tool 会话锁调用 BudgetService。重复/冲突/崩溃不得重复计费或把效果倒退。
- 取消后的账务恢复不创建新动作或扩大授权。来源已撤销而不能读取时保留 unknown；不要用准入错误替代真实效果结论。

本轮没有真实 executor 或回执服务。C 可实现核对算法并用明确的受控 Reader 做组件/真实 SQL 验证；缺实际 Reader 时返回不可用，不启用产品工具。

## 3. 异步 Runner：有 port / DTO，尚无生产 authority

`AsyncRunnerAuthorityPort.current(command: JsonObject, *, authenticated_principal: Principal) -> RunnerAuthoritySnapshot`。

位置：`src/uaw/shared/ports.py`，字段见 [RunnerAuthoritySnapshot](../../../api/objects/RunnerAuthoritySnapshot.md)。它对应 D 的 CommandAuthority，但使用 JSON Timestamp/Ref 与严格完整 schema；所有字段必填。D 可在拥有的 workspace/contracts.py 中定义严校验的 typed wrapper，并转换为内部类型。

认证主体只能来自可信通道适配器。command 内上下文是待比较的声明；权威必须从已登记请求、Run、政策、设备/根、租约、开关和取消记录独立重建。设备主体映射到用户主体需要真实拥有者关系验证，没有映射适配器就不可用。

MS-R2b 只实现异步协议消费入口和组件校验，不要求 D 自行提供未实现的服务端权威。禁止 asyncio.run 桥接、事件循环阻塞、跨尝试缓存 authority 或拿命令自报上下文作为返回值。await 后重新取实际时钟复核期限；对关键外部检查后的变化再次取当前权威并比较，最后 admission CAS 不能用 await 前的旧租约。

旧同步协议保留兼容；新入口不得静默退回同步 authority。真实 IPC 缺失时不挂载网络入口。配对 V2 的挑战/持久 DTO 留到独立公共版本；本轮内部 Ticket.document 的签名不能重解释为网络协议。

再次查询不能让不同服务的状态变化自动成为原子事务。MS-R2b 验收的是异步协议消费与 admission 去重；实际发送/执行前仍需服务端租约、撤销和动作消费协调。本轮不声称消除了真实执行的跨域竞态。

## 4. B 的模型输入公开边界

`uaw.model.ports.ModelInputPort.resolve(ref, ctx) -> ModelPrompt` 已存在。A 将 `uaw.model.contracts.ModelPrompt` 明确为公开消费结果，B 可只读导入并构造：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| messages | tuple[JSON object, ...] | 实际固定指令与材料；外部资料保持数据身份；不输出私密思维链 |
| tools | tuple[JSON object, ...] | 实际获准 ModelToolSet 转换的模型函数 schema；来源缺失不得假造空工具 |
| estimated_tokens | int | 完整输入含序列化开销、工具 schema 的保守估算；Model 网关另做原生请求估算 |

ProviderRequest/ProviderResponse 仍是 Model 私有类型。B 的新适配器放 `src/uaw/context/model_input.py`，使用自己已有 Composer/Repository/Reader/Rules/Window ports 重查版本、来源、epoch 和当前权限。A 后续负责组装与不同 purpose 的输入路由，不修改理解专用 seed.py/intent.py。

## 5. 本轮保持的实施范围

这些新增内部 port 不新增 HTTP 路由或已实现 Runtime 数。生产 Reader / authority 未注入，Tool/Workspace/通用 Context 绑定仍缺失。D01/D03/D06、实际配对、安装/写入/exec、真实 LLM 与 Agent 闭环尚未满足；完整 MS-I2、P1-02/03/04 继续开发中。
