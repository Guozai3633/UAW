# A23：只读审批的 Run／角色／政策共同来源图

2026-10-13；源码以 `ms-i2l-a23-source` 与随后正式DISPATCH准确SHA为准。
沿用A的MS-I2l来源收尾，不修改C/D业务、公共DTO/ports/schema/IPC wire或worker分支。

## 原因及改动范围

A22的真实目录与审批括号内，通用ToolApprovalAuthority仍执行两次_policy和两次access.snapshot。
每次access.snapshot又执行两次Run.current，每次Run.current前后各解析权限。
这些完整图重复展开；这里只读审批，不执行工具、模型或用户确认。

A新增 `InstalledFileApprovalAuthority`，只在两实际本机file Gate的联合根回调中使用。
其原ledger、registry、configuration、access、permission实例必须同源，实际A类严格匹配。
仅接受完整原会话/任务/用户模型上下文及精确file_read_spec/provider、原固定call/spec/hash。
不支持该组合的custom源明确不可用，不能借另一来源授许可；其他工具和旧非联合路径保留通用authority。
继承原ToolApprovalAuthority.check核对原已存approval request，批准/拒绝仍由原ApprovalService负责。
原SQL用户决定、前后grant/binding/Run/预算锁内比较没有更改。

## 共同图的实际顺序

```text
原NativeRootSource owner/read前观察
  → 原审批SQL授权记录前检查
  → 实际file固定call/spec/ctx
  → RunToolAccessSources.checked_snapshot
      原binding/role
      → Run.current（权限前 → 固定用户模型/配置数据 → 权限后）
      → 原providers和产品flags
      → 单次metadata callback（既有require_snapshot/check_access/require_entry＋资源Reader）
      → fresh binding/role
      → fresh Run.current及完整来源比较
      → fresh providers＋最终scope/deadline检查
  → 原审批SQL授权记录后检查
  → 原NativeRootSource owner/read后观察及完整比较
  → Runner继续原预算、lease、配置、签名与原deadline
```

共同图没有持久保存allowed、模型决策或批准。输入只在同一次调用内，callback收到脱离引用的ToolAccess
和RunSourceSnapshot；callback修改输入不会改共享源。callback必须返回None，异常/取消/超时传播，
原ctx腐坏或任何来源变化拒绝；不会retry/fallback来寻找许可。
两个Run.current仍各独立重新读取，内含权限前后复查；角色、provider、配置和预算取消均在关键await后复查。
固定模型的原用户输入、model policy及实际配置没有被其他角色模型替换。

## 内部接口

`RunToolAccessSources.checked_snapshot(ctx, *, check: Callable[[ToolAccess, RunSourceSnapshot], Awaitable[None]]) -> ToolAccess`

- owning Run/角色来源执行callback及前后检查；它不是执行或data恢复port。
- check对象必须callable且恰好调用一次，结果非None报tool_check_protocol_invalid。
- 不把callback结果当权限，不绕过原caller的较早期限；效果/native UI/file内容/模型不属于callback。
- 原snapshot(ctx)仍执行原前后来源，没有新的自动能力或模型配置。

`InstalledFileApprovalAuthority.current(action_id, ctx) -> ApprovalCreateRequest`

- 实际来源：原SQL ToolLedger、精确登记spec/绑定、同一A RunExecutionSources/ExecutionPolicyResolver。
- 仅file.read，资源仍来自原InstalledFileResources，且全在原ctx.scope内。
- 返回原action_id/arguments_hash/resource_refs/effect/summary/expires_at，不创建grant或command。
- 不完整ctx/不同来源实例/缺Reader返回不可用或拒绝；校验失败无工具替换和重发。

## 真实验收与测量

53不同定向节点通过：46新旧来源SQL＋3缺原字段＋3真实native实例撤销＋1同实例测量。
567历史并集未全部重跑，旧1691全量与费用保持。214源码Mypy、6文件静态/格式通过，480源码摘要。
新旧authority生成完全相同原ApprovalCreateRequest；call-local服务不改共享原authority/resources。
SQL覆盖Reader await期间角色/provider/model/预算/配置变更、callback非法返回/取消/短期限、脱离引用。
真实installed两Gate在Web账号退出、原审批删除、provider撤销后都拒绝。

| 同一实例／同一实际根与原审批 | 通用审批图 | 新共同来源图 |
| --- | --- | --- |
| 控制端SQL | 212 | 137 |
| child类在parent图SQL | 212 | 137 |
| 两者各自root／owner／owning | 2／2／2 | 2／2／2 |
| 两者各自角色OS／当前key | 16／28 | 16／28 |

两策略在同一个installed实例内比较，完整root相同；generic使用既有类，joint用生产实际新入口。
SQL只计owning Task的uaw_records SELECT，未把其他监控/子进程查询混入。秒数只是样本，不报通用速度比例。
child类parent测量不替代真实子进程效果链。controlled native/approve_once/provider/模型元数据明确为fixture，
SQL/Web/current enrollment/签名/native证明/双OS key/双进程IPC是真实。

## 原首次链及失败保留

原成功断言独立跑一次：57.56秒，1 failed，command1、open调用计数1、执行占位1，signed_data0/ref0。
open计数在WindowsReadHandle构造开始前递增，不能单凭此证明句柄完整打开或正文读取成功。
最后runner current/composite等待被取消，原10秒exchange结束关闭；receipt签名阶段没有完成。
无journal不造恢复，unknown未重发，不推not_applied/零费用。所有诊断及shielded IPC取消错误保留。
聚合日志不足以认定每个内部节点的精确停止栈；读取、签名和发布仍未验收。

最初测量因Docker Linux engine管道缺失、数据库超时产生1 setup error，132.65秒；
恢复Docker Desktop及A自己55432库后继续。该失败实例未产生native授权，不拿它当测量基线。
初始类型/长行及格式失败保留，修正后通过。A未操作B/C/D库或用户进程。
五独立installed实例（同图1＋来源撤销3＋首次链1）随机凭据/key/child/proof清理核对通过。
原响应/启动/root/lease和更早期限不延长，无新模型调用、用户文件读取或本人确认/接受。
详细[原回执](../../../implementation/evidence/ms-i2l-a23.json)，失败节点与通过并集分开记录。

## 接下来

A继续当前检查点中的重复来源图以及原登记/发送边界。需要新的worker消费时先固定准确接口与来源，
当前不向BCD发等待包、不要求同步浮动integration。D A21组件已接受并停在原交付点。
只有真实内容读取、签名journal/固定Ref恢复通过后，才汇合材料→固定用户模型→准确引用/核验→本人页面/接受。
flags/checked_metadata/子Agent/DAG/写入安装exec保持关闭，不把组件通过记作整轮产品完成。
