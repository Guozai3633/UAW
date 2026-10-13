# A22：真实联合目录源集成与新鲜组合 SQL

发布于2026-10-13。实跑回执于2026-10-12产生，历史日期不改写。
准确源码以 `ms-i2l-a22-source` 与随后正式 DISPATCH 为准；不移动旧标签，不操作 worker 分支。

## 集成与接受范围

D最终源码7157883c5917c2f8127092ae6e6ecbc8e116d413及handoff
317549c1d0add6e1a2efa6d5ffda7283e9b40dda精确合入
9210a92e9be1932d825daf599b06d6d114203169。
A实跑36 D根来源边界＋10 A协议；真实installed两Gate消费、原完整root与审批结果一致。
D报告265组件节点独立保留，不与A计数相加。只接受该组件，完整MS-R2及产品未接受。

`NativeRootSource.checked_current` 已被A两真实file Gate及Runner实际消费：
原owner/read→call-local原SQL审批→原owner/read/完整比较。
剩余每组owner、native证明、双key、OS、撤销和期限检查保留，没有allowed缓存。
旧无此方法的源仍兼容；已提供能力但异常或非法结果不能fallback。

## A实现：把已知同主体输入合在一次 fresh SELECT

新增内部 `PostgresRecordStore.get_current_many(principal, addresses) -> tuple[Record, ...]`。
addresses是1–32个不重复(namespace, resource_id)，只读同一个已认证主体当前记录。
所有locator逐一验证。一次SELECT返回完整schema/revision/payload，按输入顺序返回脱离引用的Record。
缺失或tombstone返回StoreMissing；已存在和缺失依赖都登记到实际owning witness。
每次调用都重新查询，READ COMMITTED身份图强制刷新；不走_current_batch、历史版本或跨调用计划。
最终witness能拒绝调用期间的外部变更、删除和新增。不同主体/任务不共用会话或许可。

已接入两个A原来源：

1. ExecutionPolicyResolver._run：同一次取Run与预算账本；原_scope/status/cancel/deadline判据保留，
   policy遍历前后仍各执行一次，认证与政策链/deny/网络检查仍在。
2. RunExecutionSources._data：取Run/原admission一组；关键await后再取admission/原模型政策一组，
   完整记录比较保留。历史用户模型选择、模型配置和当前配置仍独立读取，不自动换模型。

没有修改C的ToolApprovalAuthority或D的执行源码，公共DTO/ports/schema/IPC wire不变。
不会把组读结果作为下一次current的执行许可。

## 实际测量与验证

107不同定向节点通过：46联合根边界/协议＋60实际SQL＋1 installed同图测量。
前后测量同一测试节点只计一次；549历史并集不是当前全量。原1691全量及费用记录保留。
213源码Mypy、4文件静态/格式、1362 schema/288接口/320否定例通过，477源码摘要。
初次测试长行与格式失败保留，修复后通过；所有原D失败与清理记录保留。

| 实际Gate | A改动前joint | A改动后joint | 保留的joint检查 |
| --- | --- | --- | --- |
| 控制端 | SQL244 | SQL212 | root2 / owner2 / owning2 / OS16 / key28 |
| child类在parent图 | SQL244 | SQL212 | root2 / owner2 / owning2 / OS16 / key28 |

before/after为独立临时installed实例；每个实例内部legacy/joint完整root与审批均一致。
秒数受各实例负载影响，不能报告通用生产速度提升。child类测量不替代实际child效果链。
组合SQL测试覆盖单查询、外部变更、完整payload脱离引用、tombstone、缺失后出现、其他主体及容量限制。
原政策/固定模型/审批/角色撤销和Runner兼容回归实际SQL通过。

## 原首次链：仍失败，保留unknown

原完整成功断言独立跑一次，65.80秒，1 failed；没有放宽断言、skip或延长期限。
command1/open0，实际file_read_attempts一行；signed_data0/published_ref0。
该行仅说明执行占位已落盘，不能证明OS打开、正文读取或签名成功，也不推not_applied/零费用。
原10秒回复窗口终止，IPC关闭/子执行取消日志保留，未知命令未重发。
执行checkpoint已返回至占位前，但汇总日志不足以确定占位后每个内部节点的精确耗时，需进一步定位。
两次runner current、5次composite、10次joint root的累计耗时含嵌套及monitor并行，不能与墙钟相加。

三独立installed实例（before、after、first链）各4随机凭据不存在、2role keys撤销、child退出、proof关闭，
所有清理已核对。仅临时测试文件，无用户文件、新模型调用或本人确认/接受。
native确认、approve_once、模型/provider/新Run可用配置为明确受控输入；SQL/Windows/双key/IPC是真实。
详细回执与first链失败见[证据](../../../implementation/evidence/ms-i2l-a22.json)。

## 下一步和会话状态

A继续原注册/发送、审批/Run/model/权限/owning图的重复成本及打开前停止点。
下一阶段来源具体后再派实际消费；不要求B/C/D同步浮动integration或重跑已接受组件。
B/C原交付保留，D A21组件完成并停止；没有新worker包。
首次签名/固定Ref恢复通过后才汇合材料→固定用户模型→准确引用→Artifact/Verification→本人页面/接受。
flags/checked_metadata/子Agent/DAG/写入安装exec保持关闭，原期限/CAS/撤销/取消保持，不代用户点击。
