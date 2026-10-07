# B / MS-C2：通用快照与引用的最小接线提案

- 基线标签/SHA：ms-i1 / `f33d16245619b6d446816a36b65bd5c1fc607593`。
- 状态：待 A 审阅；B 未改 composition、A 的 builder/adapter、公共 schema、shared、迁移或 flags。
- 目标：A 的 `src/uaw/composition.py` 及权威领域的公共适配器；继续使用已发布 PostgresRecordStore/TransactionalStore。
- 没有新依赖或迁移，D01/D03/D06 不作决定。

## 最小注入

```python
repository = ContextRepository(records, TransactionalStore(database))
components = ContextComponents(
    readers=approved_readers,
    cancellation=run_authority,
    rules=purpose_specific_rules,
    models=fixed_model_window,
    repository=repository,
    authority=composition_authority,
)
```

新增的 `CompositionAuthority.resolve(purpose, ctx) -> CompositionBinding` 与 `verify(binding, ctx)` 是 B 的进程内 port；不新增 HTTP/LLM 字段。绑定提供：

- epoch：当前权威上下文纪元；要求、规则、能力/flags 依赖变化时由真实状态所有者推进，B 不自设初始纪元。
- rules：现有 RulesRequest，来自真实目的/激活/目标路径；不能给 agent_step 默认套理解指令。
- capability_ref：实际可读 ModelToolSet 固定版本/hash。需要获准 Reader 返回其真实 JSON 文本、platform trust、material kind。空 tools 只能是实际当前发现/flag 过滤的结果，B 没有构造默认空集合。
- preserve：原文、重要要求/requirement 来源绑定及未决动作的真实保护集合；与 ContextRequest.preserve 合并。
- dependency_refs：额外实际来源依赖；由 Reader 固定版本/hash，不支持的 Reader 仍不可用。

verify 在构建、事务内写入前后、replay 和打开时执行，须复核当前源版本/授权/取消/政策/flags/epoch。B 的 SQL 事务只原子保存 Context 自有对象；外部资料或其他领域的撤权没有因 SQL 变为跨系统原子，打开必重新核对。若需要更强的源版本提交 fence，由 A 发布真实权威 port 后消费，不能用测试替身声称保证。

ContextComponents 构造增加两个可选参数，MS-I1 已有生产组装默认仍没有这些参数，因此原理解专用行为不变，通用 build 仍不可用；没有提前绑定 RuntimeBindings.context。

## 数据与调用

- `build(ContextRequest, ctx)` 沿用现有请求/结果 schema。ctx.operation_id 必须是当前逻辑构建的稳定 request_id，重试只换 attempt_id；不同模型调用/新快照用新 operation_id。请求不接收自行提供的权限或模型窗口。
- `read_snapshot(Ref, ctx)` 是内部辅助接口，返回现有 BuildResult 结构；A 决定如何接 Model 输入，不自行登记新 HTTP/工具。
- `resolve_reference({"ref": Ref}, ctx)` 沿用 RefRequest / RuntimeContextruntimeResolveReferenceResult。
- `components.references.handle` 支持已有私有 resolve/read 分支，read 使用精确 Unicode text_span；分页、任意 register 不可用。引用登记仅由 Composer 从实际读取结果在提交事务中完成；不生成 Citation 支持论断。
- 数据命名空间：context.generic.snapshots / instructions / bindings / scopes / requests / references，与 A 的理解专用 context.* 分开。
- 所有 Context 对象只创建 revision=1；新 operation/epoch 新建 ID，禁止覆写。expected_epoch 与 authority 对比。事务请求参数含原请求、Run、Scope、固定模型/能力政策；同键不同参数 idempotency_conflict。
- 快照 content_hash 覆盖非 manifest 的全部字段；Context Ref hash 再覆盖完整 snapshot（包含 manifest）。源 hash 对应精确实际片段。ReferenceRecord 不带本机绝对路径或推测网页 URL。
- 输出空间与工具/序列化余量保留，最终估算包含完整 manifest 和 escaped text。仍为保守 UTF-8 估算；Model 的实际原生请求发送前须沿用 ms-i1 的再次计数。

## 可复核例子与验证

B 的 `tests/unit/context/test_snapshots.py` 有成功、拒绝、重复/参数冲突、epoch、删除/撤权、取消（包括部分写入后取消回滚）与版本/hash 用例。内存存储明确是测试替身。

`tests/integration/context/test_snapshots_postgres.py` 提供 **9 个真实 PostgreSQL 用例**，原文/政策/取消/模型窗口使用 ms-i1 实际适配器；通用 epoch 和空能力集合仍为明确受控 fixture，未声称真实 Tool/Runner/LLM。B 无获准 SQL 配置，仅收集用例，A 在安排的环境执行：

```powershell
./.venv/Scripts/python.exe -m pytest tests/integration/context -q --require-postgres
```

A 不必给 B 复制凭据。使用已安排连接和随机主体清理；不启动第二套数据库、不迁移、不 truncate。合入后先跑 B 用例，再跑 MS-I1 理解回归及整条链路。成功/拒绝/repeat/conflict/stale 的实际组件 JSON 回执在 B/MS-C2/examples.json。

## 当前不能宣称

缺少通用 CompositionAuthority/能力 Reader/目的规则时 build 明确不可用。现有 Run Reader 仅允许活动且已受理 Run，引用也遵循这项边界；不扩大到预览或已完成 Run。Workspace/Board/Memory/真实 Runner、自然语言多规则评估、分页与 Citation 绑定保持未实现。

A 的决定/新基线写 DISPATCH；若采用接线，无公共 DTO 生成物变更。若另需公共修改，先发布真实基线，B 再消费。回退是 B 组件提交/独立 A 接线提交的普通 revert；不会自动删除已保存的不可变 Context 记录。
