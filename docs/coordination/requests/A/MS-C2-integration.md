# A 对 MS-C2 提案的接收决定

日期：2026-10-07。[B 原提案](../B/MS-C2-storage-wiring.md)与原 handoff 保留；本记录不改写 B 当时尚未执行 SQL 的报告。

## 采用的部分

- 采用 `ContextComponents(repository=..., authority=...)` 的可选注入、`build` / `read_snapshot` / `resolve_reference`、私有 References.resolve/read 与现有严格结果 DTO。
- 采用 `CompositionBinding` / `PreparedSnapshot` / `CompositionAuthority` 作为 B 模块内的进程内接口；它们不进入模型或 HTTP 请求，`ContextRequest` Python DTO 对齐现有权威 schema，无新公共字段。
- 采用 `context.generic.*` 独立命名空间、现有 PostgresRecordStore/TransactionalStore、固定 revision=1 与 scope/Run 绑定。不同逻辑 operation 使用不同 operation_id，attempt 改变不生成新的快照；同键异参拒绝。
- 引用只登记 Composer 实际读取、选中的材料，已登记片段不能扩大，空 citations 不冒充论断证据。当前 Reader 复核不因快照保存而关闭。
- 保守序列化估算只说明上下文有界，不是实际提供方 Token 用量；最后 Model 原生请求检查继续保留。

## 本次不绑定的部分

生产组装继续缺少通用 CompositionAuthority 和真实能力来源 Reader；本次仅合入和接受组件，不启用 RuntimeBindings.context、不修改理解专用 builder/Model 输入格式，也不将测试空 ModelToolSet 登记为产品来源。

A 后续必须从真实 Run 要求/规则/Tool 发现结果取得当前 epoch、保护集合与 capability_ref；明确每种 purpose 所用规则以及实际 source/权限的复核责任。涉及生产状态或公共 DTO 的变化另发独立实现和固定版本，禁止以 fixture 代替。

SQL 事务只保证 Context 自有对象原子性，不承诺与外部资料撤权的跨系统原子提交。读/重放必需当前授权，实际发送前仍由 Tool/Runner 复核 lease/fence/撤销；快照不是执行授权。

## 状态和兼容

B 的 9 项 PostgreSQL 用例及原 8 项 A Context 接线检查已在 `ms-i2a` 之后的合入源码实际通过。与审批公共 ports/RunnerReceipt 新约束兼容，无合并冲突；全量回执见 [接受记录](../../../implementation/MS-C2-acceptance.md)。

MS-C2 组件接受，P1-02 保持开发中；B 没有新的已派发包，保留干净交付边界。C/D 的当前开工版本仍是 `ms-i2a`，本次不要求切换，也不改写 worker 分支。
