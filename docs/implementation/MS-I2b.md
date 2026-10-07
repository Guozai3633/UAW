# MS-I2b：统一实时父子权限检查

日期：2026-10-07。范围：A 的公共权限接线；完整 MS-I2 仍待 Tool/Runner 的实际权威和执行依赖。

## 本轮实现

新增 `src/uaw/run/permissions.py`，统一从真实 PostgreSQL 的 `execution.policies` 读取当前主体拥有的叶政策及父政策。Context、Model、Approval 共用 `ExecutionPolicyPort`；组装根注入同一 `ExecutionPolicyResolver` 实例。

1. 检查已受理 Run、会话/任务作用域、取消、状态和 Run/账本/上下文期限；不接受项目作用域或没有 Run 的预览权限。
2. 沿固定 parent_policy_ref 逐级读取当前记录，校验 schema、身份、实际 revision 和可选内容摘要。缺记录、已删除、换版本、循环或超过八级都拒绝，不能回到平台默认政策。
3. 子政策的 allowed_capabilities、网络域、资源 Ref 和身份范围必须在父政策内。禁止隐式扩大、路径继承或网络通配；资源 Ref 按完整字段精确比较。
4. 允许能力与网络域取交集，显式禁止取并集；结果只包含可信 Scope 实际申请且获准的能力，不把父政策其他能力复制给调用方。
5. 遍历后再读取版本/摘要与 Run 状态，发现期间变化就拒绝。它是当前权限读取，不是与实际派发原子提交的租约/fence。
6. 输出 `ExecutionPolicySnapshot`，记录当前 Scope、Run 和叶到根 Ref/hash。消费者再次校验结构、Run/Scope/能力绑定，禁止转用或扩大该对象。对象不进入模型业务参数，也不作为后续调用的授权凭据。

Context 保留其活动 Run/原文来源规则；Model 仍通过真实用户原始选择和固定目录解析模型/提供方，不切换模型。Approval 仍需真实动作权限 adapter 和用户决定；现在支持经过完整检查的父政策链，不再笼统拒绝所有继承政策。

共享 gate 提前发现 Run 过期/取消时，Intent 入口映射为已有 `intent_*` 生命周期错误；保持先检查当前权限再读取原文，不以调整测试预期来掩盖接口变化。

Model 在发送前及进行中的轮询都检查完整父链。父政策变化时取消本次 adapter 工作，已发出的调用不重发；未知 Token/费用继续保留待核算，不能因为停止本地等待就宣称供应商没有执行或没有收费。

## 公共契约与未完成项

- 新公开依赖 port：`ExecutionPolicyPort.resolve(ctx) -> ExecutionPolicySnapshot`。输入仅为服务端可信上下文；结构、错误、消费要求见 [接口说明](../coordination/requests/A/MS-I2b-permissions.md)。它是内部依赖服务，不新增 HTTP、LLM 工具或七 Runtime 公共操作。
- 新命名 schema：`ExecutionPolicySnapshot`；policy_refs 限一至八个，必须包含实际 policy hash，不能带 location/access_scope。现有 DTO/Port 签名保持兼容；构造函数增加可选依赖参数。
- 使用现有 RecordStore，无新迁移、依赖锁、默认授权或能力 flag。配置/角色/提供方实际能力、资源 Reader、用户审批、模型政策、预算 reservation、设备/根、租约/fence 和执行器仍由各所有者复核。
- 当前非空 policy.feature_flag_refs 明确不可用，不能拿未解析的开关当允许。配置里的实际产品 flags 保持关闭。
- 自动/辅助审批、审批规则评估、持续授权、生产通用 Context、Agent 身份/委派、真实 Runner authority/IPC/执行仍未完成。D01/D03/D06 保留。

## 验证与接续

新增真实 SQL 验证覆盖有效继承、祖先 deny、当前版本变化、能力/网络/范围扩大、缺父政策、循环/深度、hash/资源/flag、读取期间变更、审批批准后父政策撤销、Context/Model 同源权限、调用中撤销、快照转用、Run 取消/期限及组装实例。

```powershell
./ops/check.ps1 -WithPostgres
.venv/Scripts/python.exe ops/capture_environment.py
.venv/Scripts/python.exe contracts/check_interfaces.py
```

最终 **300 passed，0 failure/error/skip**，新增 15 项真实 SQL / 跨模块检查；Ruff/格式通过，Mypy 检查 81 个源码文件。组合回执及源码匹配见 [JUnit](evidence/p0-tests.xml) 和 [环境/源码摘要](evidence/environment.json)。首次全量检查发现 Intent 过期错误码兼容问题，修正入口映射后重跑全部通过，没有改旧测试预期。受控 HTTP 和 SQL 证明这些协议行为，不代表真实 LLM 语义质量、用户项目执行或供应商取消接口已验收。

本次集成版本使用固定标签 `ms-i2b`；C/D 当前包继续使用 `ms-i2a`，不在开发中途换公共文件。需要新 port 时在包边界同步，A 合入时负责版本兼容。B 保留已接受的 MS-C2 交付边界。完整 MS-I2 仍等待相应交付与权威接线。
