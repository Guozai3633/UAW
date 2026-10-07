# ExecutionPolicyPort：实时权限接口与消费规则

日期：2026-10-07。Owner：Run；位置 `src/uaw/run/permissions.py` / `src/uaw/shared/ports.py`。依赖 port 不接收模型/HTTP 自报审批或授权。

## 输入、输出

```python
snapshot = await execution_permissions.resolve(trusted_context)
```

输入是已有 TrustedExecutionContext，来自可信组装/调度，必须有实际 Run 和非空 Scope.capabilities；principal、Run、会话和任务需匹配。Run 只允许 preparing/running/verifying/waiting_for_user；Context 的理解读取仍有自身更窄状态限制。

| 输出字段 | 含义与约束 |
| --- | --- |
| run_id / scope | 当前 Run 与可信 Scope 完整绑定；不能换主体/任务/资源/能力 |
| policy_refs | 叶到根一至八个当前 policy Ref，revision 数字字符串＋内容 hash；不是权限来源请求参数 |
| allowed_capabilities | 当前 Scope 申请且全部父政策允许的集合，显式 deny 不能进入 |
| denied_capabilities | 叶和祖先显式 deny 的并集 |
| network_allowlist | 精确登记域的交集，无自动通配、URL 转域或补默认网络 |
| feature_flag_refs | 当前仅空集合；非空政策引用缺实际解析器，返回不可用 |

完整字段 schema 见 [ExecutionPolicySnapshot](../../../api/objects/ExecutionPolicySnapshot.md)。没有快照缓存命中、有效期延长、账号凭据、路径授权或实际执行回执。

## 硬规则

- 各级政策均从当前 principal 的持久命名空间读取；不查询别的用户或平台政策来补权限。叶必须明确绑定当前会话。父 identity selector 缺字段表示该身份维度未收窄；resource_refs 空集合表示无额外资源 Ref，不能被理解为所有路径。
- 子 allowed/network 集合必须为父的子集。父限制 conversation/task/project 时，子也必须绑定同一值；子资源集合不能超父。当前项目作用域不可用；资源比较不做 hash/Location/path 的推测兼容。
- parent_ref 必须指向当前版本，不能读历史政策绕过撤销。循环按政策身份拒绝，超过八条拒绝；读前后核对 Run 取消与三个期限。
- 不注册/修改 CapabilityPolicy，不确认 Agent/角色身份，不为用户设置模型，不消耗预算。模型输出或上传的 snapshot 没有取得权限的入口。
- 未解析 feature_flag_refs 不放行。实际配置 flags、role_categories、adapter/provider状态及每个资源 Reader 仍由 Tool/Workspace 服务核验。

## 错误

| 条件 | 错误 |
| --- | --- |
| 无 Run / 无开关解析器 | capability_unavailable / dependency |
| 所属记录删除或父不存在 | resource_missing |
| 政策 revision/hash/身份或遍历期间变化 | execution_policy_stale，412 |
| Scope 不属于 Run / 当前能力被 deny | execution_scope_denied / execution_policy_denied，403 |
| 子政策扩大父范围 | execution_policy_escalation，403 |
| 非法 Ref / 循环 / 深度 | execution_policy_invalid / cycle / depth，403 |
| 取消 / 到期 / 非活动 Run | execution_cancelled / deadline_expired / run_unavailable |
| 注入 port 输出换 Run/Scope/能力 | execution_snapshot_scope_denied，403 |

现有 Context/Model/Approval 将政策版本变化分别映射为 `context_capability_stale` / `model_capability_stale` / `approval_permission_stale`，保留旧消费方的错误语义；其他明确失败不降级到默认授权。

## C / D 需要遵守的消费方式

- C 的 ToolAccess/ApprovalAuthority 可以在包边界消费此 port，随后求角色、父 Agent、配置 flags、工具版本/真实资源与执行环境的更窄交集；port 成功不等于 Tool.invoke 成功。审批、reserve、调用意图、dispatch、settle 仍是独立协议。
- D 的 Runner 当前权限层应异步 `await resolve`，再从独立可信存储重建 request/context、设备/根、lease/fence、当前撤销和签名 key。禁止同步 `asyncio.run`/阻塞桥接 SQL，不将收到的 RunnerCommand.context 当权威来源。
- 任何执行前都重新检查当前权限；不能保存 ExecutionPolicySnapshot 后跳过撤销检查。SQL 多次读取不能承诺与外部源或实际派发跨系统原子；需要真实租约/fencing/执行器复核。
- 私有依赖缺口继续提交本 session 提案；本次不修改 C/D 业务文件或 worker 分支。当前 MS-T2a/MS-R2a 的固定基线依然是 `ms-i2a`，本包不强制中途同步。

[本轮实施记录](../../../implementation/MS-I2b.md) · [权威派发表](../../DISPATCH.md)
