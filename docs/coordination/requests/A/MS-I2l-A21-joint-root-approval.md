# A21：联合目录与原工具审批的内部接线

固定源码标签 `ms-i2l-a21-source`，准确 SHA 由随后正式 DISPATCH 发布。
沿用 MS-I2l 原范围；不回退 start、不移动旧标签、不操作 worker 分支。

## A20 接受范围

D handoff `9a419a943e3c385f4a4beb532fdb25dbe05be991` 已精确 merge
`1ca249b13de90ffd3db8387e96d1dc00e887189c`。A另实跑29单元＋11 Windows节点全部通过。
D报告106去重通过及同图SQL22→14；OS/key仍保留。不能将worker与A计数相加。
D原首次链80.78秒仍失败，command1/open0，无签名journal；unknown未重发。
按组件接受，不接受完整首次读取或整个MS-R2。补记D历史A15清理26目录名实际22物理实例，旧回执不覆盖。

## 重复图与算法

旧路径：Tool审批的 `InstalledFileResources.resolve` 调用一次 `NativeRootSource.current`，
随后Runner再独立调用current。每个current含owner/read前后两次；同次审批产生两组目录括号。

新路径：`RunnerCommands._collect_current` 发现真实Gate的 `check_root`，把原roots/device/workspace/ctx传入。
Gate经 `checked_file_root` 调用roots的可选内部 `checked_current`：

```text
原owner + 原完整root读取
  → 单次 callback(完整root前观察)
    → 原SQL审批/预算/Run/角色/provider/配置/政策复查
      （call-local ResourceReader只核对此次观察与实际call/spec/scope）
  → 原owner + 原完整root重新读取及比较
  → 返回后观察，Runner继续核对登记root/预算/lease/期限/签名
```

两Gate均已实现。控制端创建临时ApprovalService/ToolApprovalAuthority，复用原实际存储、配置、权限、
注册表与access，不改共享authority/resources。子进程沿用原已存审批，只读取/复核，不决定、登记或dispatch。
callback只能做元数据审批复查，无模型/确认/执行。没有allowed或跨current缓存。

## 内部接口与约束

`roots.checked_current(device_id: str, workspace_ref: Ref, ctx: TrustedExecutionContext,
*, check: Callable[[JsonObject], Awaitable[None]]) -> JsonObject`

- 返回及callback输入均为完整RunnerRootSnapshot，来源仍为D原NativeRootSource。
- callback恰好一次，await完成后再做owner/read/key/权限/期限复查；变化/撤销/取消立即拒绝。
- A严格核对完整owner/device/workspace/read动作、期限、返回与callback观察一致；传给审批的是脱离引用的副本。
- 方法不存在时严格沿用旧Gate.check＋roots.current；存在但不callable、异常、超时、取消、错误返回均拒绝，不能fallback。
- Gate没有check_root的旧适配器保留原逻辑；公开DTO/ports/schema/HTTP/IPC wire不变。
- D未实现checked_current前，生产NativeRootSource仍走旧路径，**尚无真实联合root提速或首次链通过证据**。

## 验证与未通过项

A当前61不同定向节点通过：40联合登记/Windows、10根协议、11原文件审批与Runner SQL。
其中联合Gate SQL节点追加子进程端后独立复跑通过，去重不多计。
原SQL用户决定/角色撤销仍有效；共享authority/resources保持原对象；协议覆盖变化、错误、过期、取消和旧路径。
213源码Mypy及6文件Ruff/格式通过。全部初次测试准备失败/中断/格式失败保留于A21证据。
受控root协议不是实际native授权；原1691全量不重写，本阶段未做新模型调用或读取用户文件。

下一步D按[A21续项](MS-I2l-A21-D-joint-root-consumer.md)实现原拥有目录源，阶段SHA到即审阅。
A随后验证实际source与同图查询/原首次链，再汇合材料→固定模型→准确引用→核验→本人页面及接受。
flags/checked_metadata/子Agent/DAG/写入安装exec保持关闭，不代用户确认或接受。
