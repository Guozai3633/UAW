# A：Q1–Q8架构与计划修订回执

2026-10-14，文档修订基线：`855bfcacd6917e5960e104f892f65b4001ac5ef7` / integration。状态：**设计检查通过，新能力尚未实现**。

## 修改范围

- [ADR-001](../../../decisions/ADR-001-conversation-and-delivery.md)记录用户已接受的八项决策；架构更新到v0.11，计划更新到v0.2。
- [对话执行设计](../../../design/CONVERSATION_EXECUTION.md)细化首次调用、消息/正式成果完成、原Run澄清/纠正、四种时钟和独立事实评测。
- [拟修订接口](../../../api/CONVERSATION_REVISION.md)列输入/输出/约束与旧数据兼容。没有修改现行schema或假称新端点可用。
- [H02计划](../../../plan/H02_CONVERSATION.md)新增P1-12～17，均planned；生成器支持显式阶段门槛，P2-07解除Join/本机依赖，完整代码/协作/搜索目标仍保留。
- 主架构、分层图及HTML、节点策略、阶段/模块/轮次、技术轮次映射、全局指引与人工体验计划同步。

## 检查与实际限制

| 检查 | 结果 |
| --- | --- |
| architecture/build_atlas.py | 115节点、17视图、162联系；ID/引用/归属检查通过 |
| design/build_design.py | 115节点策略/文档映射、链接检查通过；[报告](../../../design-check.json) |
| planning/build_plan.py | 56轮、288现有接口关联、4551本地链接；依赖无环、完整目标覆盖、可选范围与独立文本门槛通过；[报告](../../../plan/plan-check.json) |
| technology/build_stack.py | 技术轮次映射同步到56轮；[报告](../../../technology/technology-check.json)；本次未重新核对外部库资料或兼容性，既有运行字段来自历史回执 |
| 改动文档及源码边界 | 本地链接/围栏/Python生成源语法检查通过；原始未改行字节与换行保留 |
| Runtime/真实模型 | 本次未运行行为测试，新模型调用0；文档检查不能当运行验收 |

没有改src/、apps/、tests/、contracts/、uv.lock、pyproject.toml、worker会话/交接、implementation历史回执或费用。恢复了原审批页的实际实施说明，并让生成器保留这类前缀，避免重建丢失历史。

## 下一步

A先实现并发布P1-12的精确契约、迁移及最小消费源，再给B等原owner发布准确开工SHA与允许路径。此轮没有新worker标签/任务派发，不要求B/C/D同步；也没有启动新体验版或修改H01-v4。

H02须经真实快通路、原Run接续、计时/取消/授权复查、人工正确性评测和单Agent文本成果后，实际启动给本人体验。原文件签名发布链、协作链独立继续；旧失败/pending费用/取消和last_full不变。
