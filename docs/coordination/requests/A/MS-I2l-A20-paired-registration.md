# A20：双角色联合登记复查

2026-10-12，Session A / E:/UAW / integration，父版本
`ms-i2l-a19 / 8ebdb3620437d19c82beb4ba994ca1bbfb9f8c9d`。
准确源码由后续 DISPATCH 的 `ms-i2l-a20-source` SHA 固定；不移动旧 start 或标签。

## 重复节点

原 IPC session check 连续向同一 EnrolledPeerRegistry 调用 control/device 两次 current。
每次 _checked_peer 都调用 recheck_owned，重复展开同一 Web 账号、launcher candidate、
双角色进程/key、native owning SQL journal 与双签名。
这不是“两角色不需要分别检查”，而是两角色共享的原登记关系被完整展开两遍。

## 内部调用契约

```python
async def current_pair(
    control: OsIdentity, device: OsIdentity,
) -> tuple[RegisteredPeer, RegisteredPeer]: ...

control_peer, device_peer = await actual_enrolled_registry.current_pair(
    actual_control_os_identity, actual_device_os_identity,
)
```

实现位于 `src/uaw/infrastructure/enrollment_peers.py` 的 EnrolledPeerRegistry。
参数严格按 control、device 排列，来自原 IPC 实际 OS 连接/握手，不来自 frame/body/模型。
返回严格 tuple 长度2，索引0 control、索引1 device；完整身份、owner、actor、device、key/pairing Ref、
expires_at 与旧 current 返回结构相同。不是新 DTO/HTTP/tool 或 IPC wire。
无 capabilities/path/approved 参数；不注册、确认、签名、dispatch 或创建读取。

## 实际处理顺序

1. 原账号与 enrollment 完整 metadata snapshot，核对 schema/revision/immutable 原字节。
2. 分别观察 control、device 的实际 OS 实例和当前 role key，与原登记比较。
3. 一次原 recheck_owned：当前 owner、候选双方 OS/key、真实 native journal、原双方签名、
   原 enrollment 状态/revision/期限与等待后账号/行复查。
4. 两个角色再次分别实际观察；结果必须与前置完整 peer 相同。
5. 重新读账号/enrollment snapshot，与原完整内容比较；当前 SQL 输入结束时做 fresh witness。
6. SQL witness/连接 cleanup 后再次实际观察双方 OS/key，并检查原 expiry，才返回两个 peer。

owning-task witness 在嵌套外层 source 中共享时，由原最外层执行 fresh 比较；这不是跨 SQL/OS 原子快照。
D 效果边界、live pipe、私钥、实际目录/文件句柄、原 nonce/frame/签名和版本/期限复查仍必要。
每次调用都重新做步骤3；没有同会话 allowed、旧 RegisteredPeer 或 native 决定缓存。
短10秒防悬挂，仍由 D 原更早 absolute deadline 约束，不重置/增加原reply期限。

旧 current 与 owner 兼容；_observed_peer 为私有比较辅助，不是可替代完整 owning 检查的准入入口。
缺目录/候选/native/key/账号、身份或版本变化、撤销、删除、到期均原拒绝。
失败/取消不能回退旧 peer；同次失败不自动改为两个单独读取获取另一许可。
checked_metadata 默认 False，权限/flags/模型/依赖/公共 ports/schema 不变。

## 实跑

- 28真实SQL/签名节点：11新pair +17原单角色/owner 回归，18.00秒，全通过。
- 1取消/清理追加用例：1.42秒通过；后续调用重新检查，无残留owning scope。
- 1实际Windows双进程测量：34.49秒通过，原完整peer结果相同，command0/open0。
- 3追加真实SQL节点：双方OS实例等待后变化与owning journal删除，2.41秒通过。
- Mypy212源码、Ruff/格式3受影响文件通过。共33不同节点，测试无失败/错误/跳过。
  追加测试的初次Ruff import排序错误保留，修复后静态复跑，不混为测试失败。

实际Windows测量：owning recheck2→1、OS8→8、key8→8、SQL22→14。
组件墙钟单样本0.115→0.084秒；不是生产整链同比或质量门槛。
受控OS/native的SQL比较样本14→10单独记录，不混为真实Windows数值。
真实实例4随机凭据不存在、2role keys撤销、child退出、proof pipe关闭均核对。
无新用户文件/本人确认/模型调用，原所有首次链失败保留。

## 接线与下一步

D需在原 AuthenticatedPipeSession 消费 optional paired source，验证完整返回与原角色，再保留
独立directory/live pipe/expiry/私钥检查。无 paired 源时保留旧 current；paired 存在但失败时不得fallback。
[D具体续项/目录/验收](MS-I2l-A20-D-paired-registration.md)。
此阶段只交付A source和测量，D尚未消费，未重跑原首次链，不能报原超时解决。
A继续原root/authority重复节点与接线，D阶段到即审阅；不等最终全部完成。
B/C无新包，保留交付点。准确代码/回执/阶段版本见DISPATCH及ms-i2l-a20.json。
原固定用户模型、取消/撤销/版本/签名/效果CAS及10秒reply/30秒lease/120秒root保持。
子Agent/DAG/写入安装exec仍关闭；材料→模型→准确引用/成果/核验/本人接受/汇合全量pending。
