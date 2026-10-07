# B / MS-C1：MS-I1 最小接线提案

- 当前基线：`70f2fcccb88650c616920a5630d2caa45d94ad45`（parallel-wave-1）。
- 状态：待 A 审阅；本提案未自行批准，B 未修改公共文件。
- 目标公共文件：`src/uaw/composition.py` 及 A 拥有的 Run/Model/Intent 公共 facade/adapter；准确文件由 A 按领域归属选择。
- 当前缺口：通用 Context 的来源读权、当前撤销/取消、可信规则发现/自然语言冲突评估和固定模型真实窗口尚无实际注入适配。现有 ContextPort.build 的输出必须是已持久快照，首包不伪造该结果。

## 最小改动和消费方

A 用 `ContextComponents(readers=..., cancellation=..., rules=..., models=...)` 注入 B 的 `ports.py`。这些是进程内 port/审计记录，公共 JSON DTO 不增加字段。B 没有把 topic/value/order/supersedes/assessment_complete 暴露给 HTTP 或模型工具，也没有把提案当作授权使用。

1. History/原文 Reader：通过来源所属 Runtime 的获准公共读取方法返回 `Reading(ref, text, kind, trust, required, requirement_ids)`，ref 固定实际版本、Location 和该片段 UTF-8 SHA256。读取前后 `check` 检查当前主体、作用域、删除及撤销。用户原文必须为 user_input/user，关键约束/未决状态由所属领域标为 required 或使用 PreservationSpec 绑定；不能改写/strip/换行归一化。
2. Cancellation：读取 Run 所有的取消状态，预览 operation 也须有定义。Reader/提供方 I/O 必须遵守 deadline、取消任务和 Run 取消；组件在 await 前后检查并在公开组件入口限制 deadline。
3. RuleProvider：只发现注册来源，校验目录祖先/目标路径、技能激活和用户纠正关系。平台/能力规则只能来自 platform Reader。按架构第14节提交 RulePlan；尚无真实自然语言冲突评估时 assessment_complete=False → capability_unavailable。topic/value/critical 是可信评估的结构化结果，不能从关键词伪造；supersedes 仅支持同层 user_current 的后续显式纠正。普通覆盖记录通过 RuleAssembly.overrides/manifest() 消费。
4. ModelWindowProvider：解析 `ctx.model_policy_ref` 的真实 context_limit/max_output_tokens/serialization_reserve，不更换模型。没有有效提供方元数据时返回依赖不可用。请求窗口必须和解析结果一致。默认 UTF-8 序列化字节估算会保守预留，实际 Model 发送前仍须重计整个请求。
5. Intent/Model：MS-I1 将 ContextRequest.preserve 显式传到 Selector.allocate(..., preserve)；关键 requirement_ids 必须有获准来源绑定。禁止只调用无 preserve 的组件接口后宣称所有 TaskFrame 要求已保护。
6. Composer/快照仓储：由 A 的 MS-I1 确定接线和 MS-C2 新基线，才发布真实 instruction_set_ref、capability_snapshot_ref、ContextSnapshot、epoch/CAS/幂等记录。当前 build 返回 capability_unavailable；禁止启用工具/Runner flags 来绕过缺依赖。

消费方为 A 的 composition、Intent、Model 和下一包 Context Composer；现有 Intent 专用 seed.py/intent.py 原有行为不受本包改变。没有新增公共 schema 字段、依赖包、迁移或事件类型。D01/D03/D06 保持待确认。

## 结果/失败示例

- sources 输入：`{"source_refs":[{"kind":"input","id":"source","version":"v1"}],"purpose":"understanding","source_revision_policy":"pinned"}`。
- 实际成功：来源输出携带读取所得 hash，SourceBundle.manifest 引用实际版本；精确回执见 B/MS-C1 examples.json。
- 权限撤销：`kind=denied, failure.code=permission_denied`，不返回正文/成功 payload。
- 来源变更：`kind=stale, failure.code=source_changed`。
- Reader 未注入：`kind=failed, failure.code=capability_unavailable`，不会把断开当空文件。
- 关键冲突：`kind=conflict, failure.code=rule_conflict, failure.evidence_refs=[已读规则来源]`。
- 相同固定版本/参数重复执行结果一致；读取没有持久写操作/副作用，不建立伪幂等账本。MS-I1 的快照持久请求 ID/CAS 仍归 A 接线，MS-C2 仓储另验。
- 多目标目录：当前返回 context.rules.multi_target_partition 不可用；A 逐目标获取独立规则集合并让 Tool 写前复核，不混成一个全局集合。

## 验证及回退

A 在发布集成 SHA 上执行 B unit 用例后，验证真实原文 Reader、撤权/删除/源版本、Run 取消、固定模型窗口、ContextRequest.preserve 接线及最后序列化预算，再做整条链路回归。没有真实模型配置时不宣称语义验收完成。

组件只读，无数据库迁移；A 的接线独立提交可 revert。A 的批准与新基线写 DISPATCH；MS-C2 必须等待 MS-I1 发布。
