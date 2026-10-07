# 框架职责与接入边界

[技术总览](../../TECHNOLOGY_STACK.md) · [Agent技术设计](modules/agent.md) · [Run技术设计](modules/run.md)

## 1. 三种图分开处理

| 图 | 管理者 | 用途 |
| --- | --- | --- |
| 架构职责图 | 设计文档/节点映射 | 展示模块联系，可有反馈环，不直接作为执行计划 |
| TaskGraph | UAW Planner/Scheduler | 用户任务节点、前后依赖、资源、版本、就绪/失效 |
| Agent局部执行图 | AgentEnginePort的LangGraph adapter | 某个实例的上下文、LLM动作、工具/委派/等待与完成提案循环 |

父子Agent关系是实例树，也独立于上述三种图。子Agent拥有自己的实例图，父节点用结果Ref和Join接收成果。不能把全部用户任务编译成固定七Runtime流水线。

LangGraph支持在图中组合确定的程序操作与模型决策，这与上述局部执行方式相容。[官方说明](https://docs.langchain.com/oss/python/langgraph/overview)

## 2. 公开扩展接口与UAW ports

| 自有边界 | 框架组件 | 接入方式 |
| --- | --- | --- |
| AgentEnginePort | StateGraph | 由engines/langgraph.py构建/驱动，外部只消费UAW事件与结果 |
| ContextBuildPort | 普通图节点 | 调Context facade取完整输入，不再由框架自动附加独立history/memory |
| ModelGeneratePort | 提供方SDK或LangChain adapter | 用ModelGateway解析固定政策和预算，再转换框架Message |
| ToolInvokePort | 自有ToolBridgeNode | 所有普通/控制/MCP工具都经过Tool Runtime |
| DelegationPort | 普通图节点/异步等待 | 调UAW Factory，创建独立实例；预算/权限/定义版本由UAW处理 |
| ApprovalWaitPort | interrupt/resume | interrupt只等待，批准事实/期限/复核在Run；进入恢复图之前查当前状态 |
| GraphCheckpointPort | PostgreSQL checkpointer适配 | 返回局部检查点Ref；Run发布整体检查点并掌管续跑入口 |

这里的port名字表示待实现代码接口，不新增一套wire DTO。实际输入/输出沿用contracts源，代码port在对应目录的ports.py定义。

LangGraph的interrupt需要checkpointer及实例thread_id，因此P1就接入PostgreSQL局部保存，支持审批暂停与当前执行的继续；P5才补复合RunCheckpoint和进程重启后的完整安全恢复。P1不直接暴露绕过Run的框架resume入口，尚未实现完整恢复时，重启后的未完任务保持待核验。[中断要求](https://docs.langchain.com/oss/python/langgraph/interrupts)

## 3. 自有状态和框架状态

### UAW唯一管理的事实

原文、TaskFrame、TaskGraph、定义/实例、Board、权限/批准、预算/用量、效果、Workspace、成果、引用、用户接受和Run终态。

### LangGraph状态允许保存的内容

当前实例循环位置、不可变输入/结果Ref、所用版本、待消费动作标识、执行纪元，以及严格受schema约束的JSON原语。

原始完整内容归History/Context/BlobStore，图只按需要引用。任何保存的消息片段属于已批准快照，不能成为另一套可自行修改的会话历史。凭据、Python客户端、任意对象和Pickle均不进入检查点。

LangGraph检查点保存图状态，这可以作为恢复组件；UAW跨模块一致性和外部效果仍要自己落实。[持久化说明](https://docs.langchain.com/oss/python/langgraph/persistence)

## 4. 不确定写效果的完整例子

1. Agent提出写操作，Tool生成并持久化operation_id及参数版本。
2. Run完成所需批准，Tool执行前重查，再持久登记dispatch意图。
3. Runner/提供方实际写入；此时网络断开，工具结果暂为unknown。
4. LangGraph保存或未保存这一步都有可能，Run不会因此把unknown变成成功。
5. 恢复先取得Run租约，再由Tool查询原operation/command真实状态。
6. 已成功则补登记回执并继续；能安全重试才重试；无法查询则等待/受阻。

operation_id必须在首次派发前保存，并在图节点重入中复用。只在函数内临时生成UUID，会让框架重入产生第二次写动作。

## 5. LangChain使用范围

LangChain提供模型抽象、工具组件与可配置Agent循环；按需适配可以减少接入工作。[官方说明](https://docs.langchain.com/oss/python/langchain/overview)

本方案的主模型路径是批准官方SDK。某个LangChain集成确有价值且不丢协议/usage时，用LangChainProviderAdapter接入。检索/解析组件也可按同原则接到Context port。

LangGraph自身可能带入langchain-core等基础依赖，具体以冻结的发行版依赖为准。基础包存在不等于启用LangChain的create_agent、memory或全部provider集成；后者仍按UAW接口逐项接入。[官方依赖源](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/pyproject.toml)

工具schema、重试、审批、上下文、模型路由与完成提交不得被默认配置重新接管。不能同时让框架middleware、SDK和UAW自动重试同一次调用而不记录attempt。

## 6. 兼容失败与替换

若LangGraph版本无法满足关键边界，先用验证案例证明失败并写ADR。AgentEnginePort允许采用自有asyncio循环，但需实际实现与相同场景验收；接口预留不等于已经有可用回退。

正式升级以库/serializer/checkpointer组合为单位，带图状态协议版本和必要迁移。未经迁移不能用新框架反序列化旧任意对象，也不能把LangGraph自身thread_id与UAW会话ID简单等同。
