# MS-C5 接线反馈：当前来源的重复读取

日期2026-10-08，A。这是阶段版接线发现的问题，不把它改写成B已完成的新任务或公共接口变更。

## 实际观察

A组合一个CSV材料的 register_material→register_recipe→Context.build→GenericModelInputs→撤销复查。诊断中，在 build.prepare 结束前已经累计 **12,000次实际 PostgresRecordStore.get**，其中 runs约2530、budget.ledgers约2092、execution.policies约1739、run.bindings约1309、model.policies约871、配置pointer/configurations约1310。阈值由ignored诊断wrapper主动停止，只用于定位，不是成功回执，也不是生产限制。

正式链路命令及最终成功回执见MS-I2g-A1。没有模型网络请求，耗时主要在反复展开Context当前来源/配方/authority及A的Run/固定模型检查。12,000不是完整任务总数，也不是已证明所有慢耗时都来自单个方法。

A已经移除 RegisteredRunContextSources.authorize 中先调base gate再调current gate的重复；current仍做实际Run/期限/取消、固定模型和政策链复查。未缓存权限、原材料授权、取消或提供方状态。

## 后续调整边界

- B在自己的领域代码统计 register/read/recipe/resolve/verify/build/ModelInput 每个边界的Reader调用次数和耗时，明确嵌套来源。
- 避免通过 read→current→recipe→read 再次完整装配同一来源；可复用一次操作中的实际读取内容，并在关键边界独立复查当前revision/hash与权限。复用内容不代表复用授权。
- 材料/配方相关SQL可以短事务批量读取；若需RecordStore新方法，由B先提确切输入输出与一致性语义，A维护公共port/存储实现，不能导入测试fixture或自行改shared。
- 保留完整身份/session、范围、固定模型、政策、材料/规则/tool版本、撤销/取消/期限、提交前后和await后的检查。删除/撤销与修订必须继续使旧结果失效。
- 纯计算缓存与当前权限查询分开；禁止把当前授权结果做跨请求TTL缓存来减少调用。

验证用真实SQL＋至少一条实际材料到模型输入链比较相同结果/拒绝行为及查询次数。首先消除重复展开，具体延迟目标再按运行环境测量，当前不虚构目标或宣称已完成优化。
