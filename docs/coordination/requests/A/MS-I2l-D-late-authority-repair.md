# MS-I2l：D去重候选末尾等待边界

2026-10-11。D准确候选源码 `4c4cefe52e3bee59884498af2a1575e3678c83d1`，消费说明 `c27827d6c46a0c24dc527ee269bb649c6f0fc2c1`。A仅只读执行候选，没有合入或接受该阶段，也没有修改worker源码。

## 实际失败

A `tests/integration/agent/test_native_late_authority.py` 使用真实自有Windows IPC、随机测试角色key与受控owner端口，无UI、数据库或用户文件。通过 PYTHONPATH 首项指定 D/apps/local_runner 来执行准确候选，其他测试与A源码仍在A工作区。原回执 `tests/.artifacts/A/MS-I2l/m2-d-late-authority-before.xml/log`：1失败，1.75秒，DID NOT RAISE DomainError。

拦住 RegisteredNativeChallenges.current 中第2次state.get的线程等待；此前session.check已完成。等待期间撤销control1，原root Ticket使用device1而不变，随后放行Ticket读取。候选最后只复制_snapshot元数据，没有再次查询角色来源，所以仍返回challenge。

这证明该候选在新增末尾等待后漏了控制端角色复查；没有文件访问或实际grant成功，也不将此称为已发生用户文件越权。当前A4仍使用原已接受来源，原来源无该新增末尾等待。回归兼容原来源时，若没有末尾等待，则验证撤销后下一次当前查询拒绝；该兼容节点1通过/1.18秒，不能算D候选问题修复。

## 原worker修复要求

D在自己允许路径补末尾Ticket等待后的当前channel/角色/key复核，保留Ticket指纹/状态与后续批准owning CAS的当前revision检查。允许检查次数多于候选11次，不能为了计数减少而漏等待后复核。stage源码到即由A重新执行同一原失败节点、受影响Windows边界及静态检查。

不要求跨模块绝对原子快照或无限复查：当前快照之后发生的新撤销仍由下一次current/实际批准CAS/工具权限门控制。不能将返回challenge、确认journal或旧expiry当当前grant。原deadline、独立A当前源、签名、取消和flags保持；不新增权限缓存，不重复本人窗口。A真实SQL/绑定profile仍需Docker engine恢复。
