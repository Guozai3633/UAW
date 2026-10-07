# 接口0.1与早期实验字段对齐

当前准确字段入口：[统一对象字典](OBJECTS.md)、[uaw.schema.json](../../contracts/uaw.schema.json)。架构仍为v0.10，接口契约单独从0.1开始编号。这里不承诺兼容已有生产客户端，因为尚无后端实现。

## 1. 执行评估统一

早期execution_assessment.schema.json同时封装understanding/execution/next_action。现在分为TaskFrame、ExecutionAssessment与AgentStepResult，分别由对应状态所有者管理。原schema已保存到contracts/legacy/，当前同名文件只引用统一ExecutionAssessment。

| 早期字段 | 当前结构 | 原因 |
| --- | --- | --- |
| understanding | TaskFrame | 原文/修订版本与执行建议分离 |
| execution.planning_level | ExecutionAssessment.planning | 保留none/steps/dag三个独立选择 |
| execution.delegation | ExecutionAssessment.delegation | 定义存在不表示必须委派 |
| execution.parallel_scope | ExecutionAssessment.parallel_scope | 区分工具并发与Agent并发 |
| information_status=sufficient | information_state=ready | 可以开始 |
| information_status=probe_needed | information_state=read_materials | 先读资料 |
| information_status=clarification_needed | information_state=clarify | 先澄清 |
| suggested_delegates | suggested_delegations | 有类型候选；不直接启动 |
| evidence_refs字符串 | Ref对象与source_frame_ref | 固定类型、版本、定位与范围 |
| next_action | AgentStepResult / 主循环ToolCall | 评估不兼任工具执行协议 |

当前评估模板见[execution_assessment.current.md](../../prompts/execution_assessment.current.md)，早期模板标记为历史材料。模型输出按统一schema校验；不能先验旧格式再静默当新对象。

## 2. 多动作组件

早期组件常写read/write/exec或remember/recall/forget一组概念入口，字段也合并展示。接口0.1用action+parameters互斥分支：读文件不需要写内容，召回记忆不需要MemoryCandidate，恢复不会强制同时有事件订阅参数。

公共HTTP、LLM工具、Runner协议和Runtime Facade各自有DTO；路径ID从HTTP路径合成，可信身份/上下文作为独立参数。旧的owner、scope、trusted_context概念字段只有内部可信上下文可以携带；模型工具参数不能沿用它们。

## 3. 统一错误与结果

ComponentResult各接口实例强制ok有完整payload、waiting有wait_ref、其他状态有Failure；不能省略字段却声称成功。旧空字典/布尔success/字符串路径示例只作概念说明，不再作为正式输入输出。

ToolResult是ToolRuntime的完整执行账本结果；模型工具目录描述其可见结果投影ComponentResult。适配器把领域结果与执行记录关联：实际succeeded→ok；需要用户/进程→waiting；业务失败→failed；未知效果→waiting并指向EffectRecord，或failed且Failure.side_effect_state=unknown。错误投影不能丢失unknown状态或伪造成功。领域payload由固定output_schema验证，不把HTTP成功等同工具业务成功。

Run恢复租约使用ExecutionLease；Agent对话控制权用ControlLease。两者分别归Run和Agent，不共用可任意写的控制对象。

## 4. 维护原则

contracts/interface_catalog.py维护字段/操作/硬结构规则，design/catalog.py维护算法策略。每个策略页和图节点链接到准确接口。新增字段先审阅含义和状态所有权，再修改两个源并生成/检查；不直接手改机器产物。结构校验不替代实际权限、引用、DAG、CAS、OS边界和外部副作用验收。
