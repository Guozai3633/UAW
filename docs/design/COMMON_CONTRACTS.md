# 公共开发契约

状态：v0.10 实验设计，2026-10-07。以下是Python Runtime的目标接口，不是已发布协议。各节点专属字段见组件文档；技术主选见[技术栈](../../TECHNOLOGY_STACK.md)，当前已实施范围见[实施记录](../implementation/README.md)。

逐字段的准确结构现在统一在[接口规则](../api/CONVENTIONS.md)、[对象字典](../api/OBJECTS.md)与[JSON Schema](../../contracts/uaw.schema.json)。本文保留概念协议和状态所有权；展示的概念类型不作为第二份可独立变化的schema。

## 1. 共同请求、可信上下文与结果

```python
# 概念类型：真正实现时采用 dataclass / 类型验证器，库选型另议。
RequestMeta = {
    "request_id": ID,              # 同一个逻辑请求重试不变
    "expected_revision": int | None,
    "schema_version": Version,
}
TrustedExecutionContext = {
    "principal": Principal,       # 服务端/Runner确认，模型不能填写
    "scope": Scope,
    "conversation_id": ID,
    "task_id": ID | None,
    "operation_id": ID,            # 受理/草稿等尚未有Run的操作也可关联
    "run_id": ID | None,           # 正式执行必需；预览/受理阶段可尚未创建
    "agent_id": ID | None,
    "node_id": ID | None,
    "trace_id": ID,
    "attempt_id": ID,             # 每个真实尝试不同
    "deadline": Timestamp,
    "model_policy_ref": Ref,
    "capability_policy_ref": Ref,
    "budget_reservation_ref": Ref | None,
}
ComponentResult[T] = {
    "kind": "ok|waiting|missing|denied|conflict|stale|failed|cancelled",
    "payload": T | None,
    "output_refs": list[Ref],
    "revision": Version | None,
    "failure": Failure | None,
    "usage_ref": Ref | None,
}
```

这些结构是接口说明，不是可直接运行的 Python 定义。各组件不必在模型工具 schema 中暴露全部字段。模型只看到其业务参数；Tool 注入 RequestMeta/TrustedExecutionContext，调用所属 facade。字段缺失/未知类型由机器检查，语义要求由模型加真实证据判断。

`kind=ok` 表示组件本次操作完成，不自动代表整个任务成功。工具 `side_effect_state=confirmed/pending/unknown`、Run outcome、检查结果 passed/failed/not_run/blocked、用户接受状态分别使用自己的类型，不能合成一个“success”布尔值。

## 2. Ref、版本与访问

Ref 至少包含 kind/id/version/location/hash/access_scope；实际正文按身份读取。引用不等于永久访问权。资源删除、账号撤销或本地断开会令旧引用不可读取，resolver返回明确状态。签名下载地址是临时读取结果，不是长期引用ID。

写入请求须使用所属领域 expected_revision；读取记录实际取得版本。用于源版本固定的参数与用于防覆盖的CAS版本不同，不混用。跨领域参数用Ref连接，不导入邻域私有Repository或对象直接写状态。

## 3. 幂等与副作用

配置创建等内部写入以 principal+scope+request_id+稳定项键保持幂等。重发必须同参数，若同键不同参数返回 idempotency_conflict。更新使用定义/资源版本CAS。幂等记录不按普通缓存TTL淘汰；保留策略需覆盖有效重试窗口。

外部写入：Tool先持久执行意图，再发送；action_id/business_key是逻辑动作，attempt_id是尝试。未知结果先查询提供方，不能换新动作键重试。同一调用两个回执只结算一次。提供方不支持查询/幂等时，如实保留unknown并阻止依赖成功，不宣称exactly-once。

## 4. 错误与事件

Failure 字段：code、category、failed_phase、retryable、recover_hint、evidence_refs、side_effect_state?。标准类别至少参数、授权、政策、依赖、冲突、模型协议、工具业务、基础设施、限额、超时、取消、未知效果。恢复建议不授予新权限，也不允许覆盖用户模型意图。

每个facade开始/结束发关联span；实际状态提交后再发业务事件。关键事件由Run持久保存，Trace可采样。组件不直接向前端打印“已完成”；UI从InteractionItem/Run/Review状态展示。事件包含event_id、stream_seq、schema_version、关联IDs、payload_ref、实际revision。

## 5. 事务、等待、取消和恢复

单进程先以本地事务/锁/CAS维护唯一写入。跨执行器分配使用持久意图和回执，补偿与恢复步骤明确；不靠一把进程锁假称跨外部系统原子。lease保护执行权，fencing版本阻止过期执行者提交；权限仍独立检查。

deadline向下传剩余时间；模型、工具、子Agent和评审预算共用父Run账本。等待不自动更新完整时限；延长是用户或已授权策略的明确修订。取消先阻止新动作，再查询执行器实际停止，不能把结束等待当作外部动作已停止。

checkpoint保存领域版本/游标，恢复读取当前撤销、核对Tool效果和Workspace实际版本。replay不执行工具；resume继续旧Run；rerun建立新Run。变化只使实际依赖失效，保留用户修改与未受影响成果。

## 6. 目录与依赖规约

Runtime 对外只暴露 facade/contracts/ports。子模块经ports访问其他Runtime；composition根负责接线，禁止各模块自己创建全局单例。工具控制行为经过Tool facade；内部Runtime协调可以走可信公共port，不能以此形成模型绕过策略的执行入口。

服务Runtime、本地Runner、任务代码环境分别运行；标准库、数据验证、Web框架等选择在实施时确定。权限/路径/网络/进程边界按真实后端能力描述，不将工作目录或venv当OS沙箱。

## 7. 验证口径

所有节点文档中的测试是开发验收计划。当前只验证文档映射、引用和图谱交互，尚无Runtime实现或模型能力测试。真实任务验收分别看：实际成果、真实执行/状态、语义目标、用户接受和包括失败的总成本；开放任务允许多种合理路径，不僵硬匹配唯一工具序列。
