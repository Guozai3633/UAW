# A13：原文件命令的统一当前来源

2026-10-12，继续 MS-I2l-A9。父版本 `d72bd7c8ce13ad0a0f06c42fb87bb3c029cc212d`。
准确来源标签与 SHA 在 DISPATCH 发布；不是新共同 start，不移动历史标签。

## 为什么需要这一层

D 的一次 current 会分别读取原命令、拥有者、通道、目录和两次完整 authority。
其中多条路径再次展开同一组 Run、审批、角色、模型、预算和 lease。
A13 提供一个入口，把这些原来源完整检查后的结果一起返回。D 后续可以按效果边界
消费这份结果，避免在同一个检查点重新展开相同来源。当前 D 尚未消费，不能声称预算通过。

## 内部接口

位置：`src/uaw/workspace/ports.py`，实现：`src/uaw/run/runner_recheck.py`。
仅 Python 内部可信依赖，不能从 HTTP、IPC body、模型参数或用户配置传入实现。

```python
result = await current_source.current(
    original_command_ref,
    authenticated_principal=actual_channel_actor,
    channel_ref=original_channel_ref,
    deadline=original_response_deadline,
)
```

| 输入或输出 | 约束与用途 |
| --- | --- |
| command_ref | 原登记 command 的 content/version=1/hash；不允许 location/access_scope 或派生自回执的命令 |
| authenticated_principal | 原通道实际认证的完整 Principal，含 auth_session_id；来源不信任 body 自报 actor |
| channel_ref | 原 content 固定摘要或 connection/version=1；须与原设备来源一致 |
| deadline | 原单次回复的绝对 monotonic 期限，有限数字、非 bool、在当前时间后且最多 10 秒；后续调用沿用较早值，不重新加 10 秒 |
| RegisteredReadCurrent.command_ref | 已核对的原固定 Ref |
| source | RegisteredReceiptCommand：原签名命令、独立设备 ID、原用户 owner |
| authority | 原 RunnerAuthoritySnapshot：上下文、request_ref/parameters、policy_ref、required_scope_capability、root/actions、lease/fence、feature_enabled/connected/cancelled；角色、配置、模型、审批和预算由 collect 完整核验，不新增这些对象的输出字段 |
| channel | 实际 RunnerChannelSnapshot，原 actor/owner/device/channel |
| root | 实际 RunnerRootSnapshot，原 owner/device/workspace/handle/binding/actions，与登记版本一致 |

本入口只支持原 `file.read` 执行检查。保留 `recheck` 的 snapshot 调用形式，内部委托统一入口。
返回模型均为脱离来源的副本；外层 dataclass frozen 不代表嵌套模型不可变，消费者不得修改后当权威。
结果不是准入 CAS、目录授权或跨等待的允许缓存。

## 执行链与最终 SQL 比较

1. 冻结原 Ref、完整 actor 和原期限。
2. 读取原 active 命令并核对摘要。
3. 执行原 `RunnerCommands.collect`，保留其两次完整校验；本阶段没有删除其谓词。
4. 核对 command/actor/owner/device/channel/root/workspace/context/binding/actions 的交叉关系。
5. 重读原 command，检查版本、状态及原有效期。
6. 对本次读取的所有 SQL 输入执行一条新的 UNION ALL SELECT，比较完整记录。
7. 释放本次连接后再次检查原回复和 command 期限，返回脱离来源的投影。

`PostgresRecordStore.current_witness()` 单 task 有界观察本次读过的 current/history 地址，
总计最多 256 个。保存完整首次观察副本和不存在状态；当前行与历史版本共享最后一条
READ COMMITTED SQL 的视图。当前变更、历史 payload/schema/revision 变更、新增原缺失行或墓碑
均拒绝本次来源。失败、取消和子 task 不共享观察范围。

production 的 `checked_metadata=False` 保持不变，每次 get 仍 fresh SELECT。
观察器不启用 A12 的可选输入优化，也不保存允许结论；若可信调用方显式启用该优化，
它仍是独立模式，并同时接受完整最终 witness。

最终 SQL 比较不是 SQL、OS、原生授权和密钥存储之间的原子事务。连接清理也可能 await。
D 必须保留双方当前 key、native 根签名、OS 实例/句柄、CAS 内检查及关键等待后的复核。
不得把这个投影用于已经取消 Run 的旧回执恢复；恢复仍使用独立当前数据访问权限。

## 装配与 watch 的实际状态

`PairedInstalledFactory` 用原同一个 RunnerCommands 创建 RegisteredRunnerRechecks。
InstalledReadOnlyHelper 强制其 store、commands Reader、async authority、roots、registry
分别与原装配对象一致，保存为 `current_source`。D runtime/endpoint 暂无消费参数，未替换旧路径。

`wait_changed` 沿用原绝对 deadline，比对完整投影或因撤销、取消、期限拒绝而终止。
当前实现仍执行完整 current；50ms 是间隔，不是检查耗时或变化响应保证。
本阶段不以它替换 D 当前双方 key/实际断连监控；后续监控消费策略须先明确覆盖与期限。

## 验收边界

真实 SQL 验证包括最后 command lookup 等待期间 Run 取消、最终 witness 等待超时、
history/current/absence/tombstone 变化、task 隔离与清理。真实 Windows 工厂装配使用临时受控
native 决策，测试没有发送 file command 或打开文件，不代表真人授权或首次读取。
精确计数、原 Docker 中断与所有失败记录见 `docs/implementation/evidence/ms-i2l-a13.json`。
旧首次文件链失败、旧全量回执和模型费用保留；没有新增模型调用或读取用户材料。
