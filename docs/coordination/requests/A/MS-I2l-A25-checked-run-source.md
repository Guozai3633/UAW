# A25：逐检查点诊断与同源 Run 元数据括号

2026-10-13，继续 integration 的 A24 发布点，不移动 worker 基线、旧标签或提交。
本轮只修改 A 的 Run/Tool 来源与 A 测试；没有修改 B/C/D 业务源码。

## 真实问题

原首次文件读取需在打开、读取、签名和落盘前后检查当前权限。每个检查点又递归展开
审批、角色、Run、固定模型及配置来源。在原 10 秒回复期限内，这些工作累计超时。
此前的 open 调用计数和签名总次数不足以证明打开完成或具体回执签名完成。

A 新增测试专用 `installed_read_trace`，包装原 D 的受控临时 assembly，记录具体检查点、
剩余回复期限、各来源耗时、打开/读取是否返回、签名 domain 和完成状态。
不记录身份、目录、正文、参数、凭据、密钥或原始 SQL。检查点内没有新增 trace 文件 I/O，
只在原 exchange 结束后保存。原真实 SQL、Windows/IPC/key 操作、期限和 D fixture 约束保持。
测试直接调用原首次读取及原 journal 恢复成功断言，不替换失败断言，不重发 unknown。

## 内部接口与实际链路

`RunExecutionSources.checked_current(ctx, *, check) -> RunSourceSnapshot`

只支持实际同一 PostgresRecordStore 上的 RunExecutionSources、ConfigurationService 和
ExecutionPolicyResolver。回调仅做元数据检查，必须返回 None，不允许执行工具或等待用户。

1. 固定完整 ctx、store/config/policy 对象及认证回调。
2. 当前完整权限检查，包括当前账号、Run、预算取消、原期限和政策链。
3. 当前完整固定模型数据：Run/admission、用户原模型选择、模型政策、配置及 provider。
4. 向回调传递脱离引用的观察结果；回调错误、取消或非 None 返回直接传播或拒绝。
5. 再完整读取固定模型数据，再完整检查权限；前后完整结果必须相同。
6. 最终 fresh SQL witness 检查所有观察的当前/历史/absence/tombstone 完整记录。
   原对象和 ctx 在关闭等待后仍须一致，原较早期限仍有效。

`RunToolAccessSources.checked_snapshot(ctx, *, check)` 的实际同源分支接上述接口：

```text
原角色 binding/profile
  → 当前权限 → 固定模型数据
    → 当前 provider/flags → 脱离引用的元数据回调
    → 原角色 binding/profile 再查 → provider 再查
  → 固定模型数据再查 → 当前权限再查
  → 最终完整 SQL witness → 对象/认证/环境/配置身份再查 → 返回观察
```

由一个外层前后权限括号替代两个递归括号，完整权限调用 4→2，固定模型仍读取两次。
角色、provider、flags、Resource Reader 和 stored approval request/grant 判据保持。
默认 `snapshot/current` 和 custom/非同源 `checked_snapshot` 保留旧路径。
checked_metadata 未启用，未新增 allowance 缓存、跨检查点复用、locator 计划或公开接口。
嵌套 witness 必须由最外层完成；外层关闭后检查嵌套 Run/policy/认证对象不能被替换。
这不是 SQL/OS 的跨域原子授权，D 关键操作前后 current、native/key 和 handle guards 不变。

## 检查、失败和修复

- 初次 SQL：47 通过，1 测试夹具失败；测试用的 Container.database 为 None，改用实际 store.database。
- 初次类型检查：None 回调声明不能检查返回值；改为 Awaitable[object] 并运行时严格要求 None。
- 初次格式检查失败已格式化；原失败记录保留。
- 关闭边界补测：7 通过、1 真实失败。嵌套 Run 的对象身份检查发生在外层 witness 完成前，
  外层 SQL 等待后替换 policy 对象漏拒绝。A 在最外层补齐完整 source/认证引用检查后，全部相关节点复跑。
- 最终 50 个不同 SQL 节点通过；4 个实际 installed 节点通过（同命令比较、账号退出、根撤销、key 撤销）。
  214 源码类型与 6 文件 Ruff/格式通过。历史并集不是当前全量；旧 last_full/费用不覆盖。

同一个实际已登记命令，最终输出完全一致：

| 观察 | 原登记来源＋旧角色括号 | 新角色外层括号 |
| --- | --- | --- |
| SQL SELECT | 231 | 221 |
| 原 Gate 审批 | 1 | 1 |
| native root / owning enrollment | 5 / 6 | 5 / 6 |
| OS / 当前 key | 48 / 89 | 48 / 89 |

独立 SQL 角色图 SELECT 43→36，完整权限调用 4→2，元数据回调都是一次。
实际登记样本耗时 0.985→0.999 秒，没有证明耗时改善，不能把查询减少当整链提速。

## 首次链仍未通过

初次诊断 53.68 秒失败：打开和读取返回，读取后的第四检查点取消；未调用 receipt 签名。
修复后原成功断言 47.53 秒仍失败：打开/读取各完成一次，receipt domain 签名完成一次，
第五检查点（签名后）开始时仅剩约 0.815 秒，在其第一个 fresh current 中取消。
完整 Gate 图仍是主要累计耗时，不能将跨轮负载不同的总耗时当优化比例。

两次链均 command 1、原一次使用占位 1、持久 receipt_data/ref 0，unknown 未重发。
原字节对照及 journal 恢复断言尚未到达；内存签名完成不等于可交付/可恢复回执。
四个元数据 installed 实例未发送/open，加两次首次链共六个独立临时实例，
随机凭据移除、双方 key 撤销、子进程退出及 proof pipe 关闭全部核对。
仅受控临时材料与 native/SQL 审批；没有用户文件、新模型请求或真人确认/接受。

详细计数、测试回执摘要、前后 trace 与清理见 [A25 证据](../../../implementation/evidence/ms-i2l-a25.json)。
flags、子 Agent/DAG、写入/安装/exec 保持关闭。完整首次读取及 MS-I2l 产品验收未 accepted。
BCD 保留原交付点，本轮没有新消费接口或 worker 包；A 下一步继续审批来源展开及签名后持久链。
