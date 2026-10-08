# MS-I2d：执行租约与模型输入路由

日期：2026-10-08。发布版本 `ms-i2d`。B/D 原 handoff 保留；C 当前 MS-T2b 继续固定 `ms-i2c`，不要求中途同步。

## 1. 本轮接收决定

- D 的 MS-R2b 合入 `38492df`，真实复验 172 项通过。新增异步入口、严格 wrapper、当前权威重查与本机 guarded CAS 接受为组件；生产映射/authority/可信 IPC 不因此可用。
- B 的 MS-C3 合入 `0d6521d`，107 个组件检查通过；15 个 SQL 用例首跑准备失败，修复测试 Ref pin 兼容后又发现 Windows subprocess 循环不兼容。两处最小平台/共享边界修复只在 A 的集成目录，原 worker 记录不改写。
- B 的 `GenericModelInputs` 保持实际 ToolSpec 格式，由 Model provider adapter 转换原生工具 schema；A 不把输入 tools 改成另一个私有格式。

## 2. 执行租约公开 port

位置：`src/uaw/shared/ports.py` 的 `ExecutionLeasePort`。
实现：`src/uaw/run/leases.py` 的 `ExecutionLeaseService`。
组装：`Container.execution_leases`，只有配置真实 PostgreSQL 时创建。

holder 是由可信内部服务认证/组装提供的 Principal，必须为 service；不是用户或模型可填的 request 字段。记录按 ctx.principal 所属 Run 分区；holder 是执行者身份，与用户所有者分开。

本服务接受上游已经认证的内部Principal，不自行实现会话认证或撤销Reader；完整holder/session相等不能代替通道认证。当前只协调同一Run的根执行者，跨Run工作区写入租约、文件隔离和合并仍由后续Workspace规则处理。

| 方法 | 请求对象 | 返回 | 关键限制 |
| --- | --- | --- | --- |
| acquire(request, meta, ctx, holder=...) | ExecutionLeaseAcquireRequest | ExecutionLease | 初始 expected_revision=0；后续使用 state 的当前 revision；一个 Run 只有一个根 holder |
| renew(request, meta, ctx, holder=...) | ExecutionLeaseRenewRequest | ExecutionLease | Ref版本、fence、完整 holder/session 均相等；续约不改变 fence |
| release(request, meta, ctx, holder=...) | ExecutionLeaseReleaseRequest | ExecutionLeaseStateRecord | 同 holder CAS释放，Run取消/调用过期后允许原租约清理 |
| current(lease_ref, fencing_token, ctx, holder=...) | Ref、整数 fence、可信上下文 | ExecutionLease | 当前 Run、范围、取消、期限、版本、holder均复核；不能重放旧租约执行 |
| state(ctx, holder=...) | 内部服务＋拥有者上下文 | ExecutionLeaseStateRecord | 当前状态供接管/清理；可以观察其他内部holder，不授予使用它的权限 |

命名对象的全部字段见 [对象索引](../../../api/OBJECTS.md)。TTL 严格整数 **1–300000 ms**，实际 expires_at 取 TTL、调用 deadline、Run及根预算 deadline 的最小值。node lease 尚未实现，传 node_id 明确 unavailable。

## 3. 持久与恢复规则

存储为开发 PostgreSQL `execution.leases`，使用已有 RecordTransaction，无新迁移。记录 `ExecutionLeaseStateRecord{lease,state}`，行 revision 等于 lease.revision。

- 与 Run.control/预算使用同一 conversation 聚合事务锁，跨进程申请由数据库串行化。锁等待结束后重新取时钟，不用等待前的期限准入。
- 首次 fence=1。续约保留 fence；过期或释放后的新接管 fence+1、revision+1。没有删除旧行或把 fence 清零的接口。
- active / released / expired / revoked 是持久状态。current/state 观察到实际根租约过期或Run撤销后提交终态，再向调用方返回拒绝；异常不能把该终态回滚成活跃。
- 调用自己过期只返回 lease_context_expired，不能作废另一段仍有效的根租约。state 可在该调用过期后用于清理，不能用于执行。
- 同 request_id 的参数/ctx/holder必须一致；冲突拒绝。acquire/renew 的响应丢失重试通过请求账本取原结果，再检查当前 Ref/fence/holder，旧成功回执不重新授权。release 的历史重复回执仅证明原释放，不改变后来新holder。
- 当前查询失效时不会凭空接管。接管者先 state，按真实 revision 申请；活跃 holder 返回 busy，版本竞争返回 conflict。

## 4. 与 Runner 的关系

本轮新增了真实租约所有者，尚未把它作为生产 Runner authority 组装。没有已登记设备/通道归属、根/workspace、固定命令参数和可信 IPC 时，不能从 command 自报字段生成 authority。

lease 是执行协调，不证明角色、权限、审批、资源、开关、设备、签名或 executor 已满足。实际命令发送/执行必须消费当前 fence 并协调撤销；仅检查一次 lease 或本地 admission 不能保证跨服务原子授权。现有 Model 诊断入口仍独立运行，Agent执行驱动尚未创建，不能宣称所有操作都已受执行租约约束。

下一步 A 提供设备归属/已登记命令/租约消费的真实所有者后，再决定 D 的新工作包。本次不给 D 派完整 MS-R2；可信 IPC 和配对 V2 不由 D 自行补协议。

## 5. B 的实际输入路由

新增 `src/uaw/model/input_router.py` 的 `ContextModelInputs`，在 compose 的 ModelGateway 中使用：

1. 单次 SQL SELECT 查当前主体实际持久的 `context.bindings` / `context.generic.bindings`。
2. 没有 binding：missing；两种同时有：ambiguous 拒绝。Ref kind必须为 context。
3. legacy → 原 StoredModelInputs，保留诊断/understanding语义；generic → B 的 GenericModelInputs。
4. generic缺 Composer/Reader/authority、越权或来源变化时直接失败，不退回 legacy 或理解模板。

命名空间查找不是授权。各解析器继续核对绑定、当前权限、实际来源、版本/摘要、epoch和模型窗口；ModelGateway继续估算完整 native 请求、检查预算/取消/固定模型。默认通用 Composer仍缺真实 authority，GenericModelInputs(None)明确不可用；没有注入测试目录或空工具来凑通用能力。

## 6. 仍未满足项

完整 MS-I2、MS-T2、MS-R2、P1-02/03/04继续开发中。C 的 MS-T2b 仍使用 ms-i2c。B/D 暂无新包，保留干净交付边界。D01/D03/D06不决定，flags关闭，没有安装/写文件/exec、真实配对或Agent闭环。
