# A21 D M2：真实来源的联合 Gate 消费阶段

固定source 88e7078cc0b7aee66136ebd44ec0d057e184b209，dev/runner。
M1源码3a2e145a08043686837ac7d2e43d2317e5ec53f2，阶段文档1f55eb7。
M2源码 **7157883c5917c2f8127092ae6e6ecbc8e116d413**。
原 NativeRootSource 构造不变；A两Gate/check_root可直接消费，不新增公共port/DTO或wire。

D55435实际Web账号/SQL enrollment、当前OS双角色keys/真实双进程IPC、已消费SQLite native ticket/grant
及临时目录，native输入/SQL approve_once/provider/新Run可用flags为明确fixture；无本人窗口或模型调用。
两个Gate类使用同一parent实际owning图测量；child类此处在parent图运行，不宣称实际child读取成功。
后续原首次链才实际经过原隐藏child Gate；完整成功结果尚未运行，不能预称通过。

| 同图原root及审批结果 | root _read | owner | owning enrollment | SQL SELECT | A角色OS观察 | 全目录key lookup | 单样本秒 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control legacy | 4 | 4 | 4 | 276 | 32 | 56 | 1.9838584 |
| control joint | 2 | 2 | 2 | 244 | 16 | 28 | 1.5453325 |
| child类 parent图 legacy | 4 | 4 | 4 | 276 | 32 | 56 | 1.4539610 |
| child类 parent图 joint | 2 | 2 | 2 | 244 | 16 | 28 | 1.4293121 |

表为单次await owning Task的累计SELECT，root含实际SQLite/proof/current-device-role signature/OS根复查；
OS计数只含A enrollment角色观察，独立pipe及local根身份检查保留但不冒称是这里的OS总数。
按完整owner/native括号删去重复展开，每个剩余图仍有全部检查，无allowed或current缓存。
两Gate共享authority/resources原对象不变、完整root结果相同。单样本不作生产加速比例。

真实来源2项测量/取消/root撤销通过70.43秒；3项provider/approval/account来源撤销通过86.54秒，
role撤销在测量节点两Gate复核拒绝。全部command0/open0；5独立installed实例各4随机凭据消失、
2role keys撤销、child退出/proof关闭（按物理路径去重current别名）。

207受影响D回归通过142.95秒：新joint/native、async admission、真实签名receipt、Windows只读IPC、
原journal重启及取消恢复、helper native window生命周期和endpoint兼容。最终36新根边界通过10.13秒，
包括有效完整revision变化、callback不awaitable、首_read返回时已过期不得进入callback。
Ruff/格式及36源码Mypy通过，12公共/A/锁文件归一化摘要相对source不变。

主要回执ignored tests/.artifacts/D/MS-I2l-A21：native-final.xml、boundary-final.xml、joint.xml、
sources.xml、regression.xml及实际metadata/measurement/cleanup。原首轮测试准备与格式/类型失败保留。
接下来独立跑原 test_installed_file_chain.py --require-postgres 完整成功断言一次；unknown不重发，
保留所有阶段/停止点/费用状态及随机源清理，最终独立handoff后停止。
