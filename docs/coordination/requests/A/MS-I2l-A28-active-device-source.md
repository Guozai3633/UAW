# A28：有效设备状态的只读来源，保留到期封存

2026-10-13，继续 A27 integration 发布点；仅 A RunnerDevices 与 A 测试修改。
BCD原源码/分支/提交不操作；本轮没有新worker包，不要求自动同步。

## 问题与做法

RunnerDevices.current在查询设备binding时，前后各进入TransactionalStore.inspect，
即使绑定有效也取得runner-control聚合锁、创建独立事务/连接。该锁并没有跨越实际通道等待，
原语义是两次独立读取和完整比较；有效查询不写数据，只有到期状态需要持久封存。

新增内部 `_current_binding(device_id) -> Payload`：

1. 只有实际PostgresRecordStore使用fresh store.get；自定义/派生仓储继续原_load事务。
2. JSON脱离引用，完整RunnerDeviceBinding schema、device_id与row.revision一致性检查保持。
3. active且expires_at已到，立即原_load事务序列化封存；不能凭先前active状态继续授权。
4. current仍核对完整caller actor/owner/session，active状态和实际当前通道/connected/期限。
5. await通道之后，再fresh读取完整binding和再次schema/revision比较，最后期限到达仍_load封存后拒绝。

```text
fresh binding → schema/ID/revision/状态/原期限
  → 完整actor/owner/session → 实际channel/双方OS/key/native来源
  → fresh binding再读 → 完整通道/binding比较 → 最终expiry检查 → 返回原完整绑定
                 任何到期分支 → 原聚合锁/事务/CAS封存 → 拒绝继续
```

没有权限/allowance缓存，记录SELECT次数不减，原观察记录仍参与上层current_witness。
bind/revoke/到期写入和CAS/主体/幂等/转移拒绝不改；没有放宽版本或期限。
不宣称SQL与OS/native跨域原子授权，D效果前后current/key/native/handle guards仍必须执行。

## 真实组件验证

原Runner控制49节点与新增设备7节点首次56通过；新增custom-store边界后设备8节点复跑通过。
去重加4个实际installed节点共61定向通过，原失败/旧回执/费用保留，历史并集不当当前全量。
完整结果相同，独立设备current：记录读取2→2、实际通道source1→1、聚合锁SELECT2→0。
撤销/删除/expiry在通道await期间发生必须拒绝；到期封存revision2/expired，恢复旧时钟仍不可复活。
已返回观察脱离引用、后续调用重新读取；上层witness内撤销最终拒绝；custom-store保留_load两次。

同一已登记installed原命令，在实际Web/SQL/双key/OS/IPC/native来源下对照新旧路径：
record SELECT189→189，聚合锁SELECT16→4；root5/owning6/OS48/key89/Gate1不减。
剩余4次锁是其他原审批/租约等来源，不删除。完整结果必须相同。
样本0.705→0.552秒不作为生产通用速度比例，metadata试验不发送命令或打开文件。
另3实例真实账号退出、native根撤销、key撤销均拒绝，在发送前明确停止并清理。

## 原首次链的新停止点

原成功断言单独运行43.65秒仍失败。command1，打开、读取、receipt-domain签名各完成一次，
第六checkpoint（签名验证后、signed CAS前）完成，原一次使用记录中receipt_data已持久保存。
receipt.publish随后等待来源时CancelledError，原parent10秒先到期关闭；receipt_ref仍空。

**持久签名候选不等于已发布回执或任务交付成功。** 原字节对照和journal恢复断言未到。
unknown未重发，没有假not_applied、零费用或新receipt。截止仍是原总窗口，child窗口约晚0.290秒。
5独立临时installed实例（同图1＋撤销3＋首次链1）随机凭据移除、双方key撤销、child退出、proof关闭全核对。
仅受控临时材料/native/SQL决定和模型metadata，真实SQL/OS/key/IPC保持；无用户文件、新LLM或本人接受。

下一步A处理已持久原签名候选的发布/恢复来源以及剩余重复检查成本；不直接发送第二次命令。
完整首次链、产品MS-I2l与汇合全量仍pending，flags/checked_metadata/子Agent/DAG/写入安装exec保持关闭。
[A28完整实际回执](../../../implementation/evidence/ms-i2l-a28.json)。

## 人工体验准备并行项

已只读检查现有8000/5173，均不可达；默认apps/web/dist/index.html不存在。
这不能推断其他旧构建失效，也不能宣称网页已启动或本人体验通过。
[H01准备记录](../../../implementation/human-tests/H01-preparation.md)固定待办：准确前端dist/源码、
独立服务/数据和认证/固定模型/办公学术成果预跑。文本体验不以本机文件链成功为前置，
但必须先完成自己本版本真实预跑，不能借旧1691全量或过去接受回执直接宣布就绪。
