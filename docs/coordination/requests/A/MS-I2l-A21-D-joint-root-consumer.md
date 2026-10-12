# D 原读取预算修复续项：联合目录消费 A21

开工须远端 `ms-i2l-a21-source` peeled SHA 与正式DISPATCH相同；本文件准备字样不覆盖随后正式记录。
保留D A20源码/handoff和失败；只合准确固定tag，不合浮动integration、不重写原提交。
这是已授权原A9/A15/A20预算修复的具体消费续项；A不代写D业务。

## 输入与输出

A已在 `installed_root_check.py`、两真实file Gate和Runner控制器提供
`checked_current(device_id, workspace_ref, ctx, *, check) -> JsonObject` 内部消费。
详细契约见[A算法](MS-I2l-A21-joint-root-approval.md)。没有公共DTO/构造器/IPC wire变更。
callback是同次原SQL审批元数据检查：完整前root传给它，必须await恰好一次并要求None返回，
不能执行工具、访问文件内容、启动确认/模型或借callback绕过D原owner/read验证。

## M1 实现原拥有源并立即报告阶段SHA

在D `NativeRootSource` 复用原current全部验证/绝对较早期限/owner与_read：
原owner→原完整_read→check(detached first root)→原owner→原完整_read→完整比较/期限→return second。
旧current保持兼容，可复用私有核心，但不得接受root/owner/path由请求自报，不能删_read中的SQLite、
原consumed ticket/grant/native确认/当前signature key/local OS root identity与最终复查。
callback变化输入、副作用失败、非法返回、取消、超时必须拒绝；不返回部分root/不fallback。
不延长原10秒reply/15或90秒启动/30秒lease/120秒root或任何更早期限，保留效果前后fresh检查。
M1定向测试涵盖callback前后owner/root/key/期限变更、取消、异常/非None结果、脱离引用与旧current。

## M2 实际A Gate消费与测量

使用D自有55435库与随机临时根，真实installed/control及child原Gate消费这个同一source，
比较同完整root、同审批结果的legacy两current与joint一组前后观察；分别记录owning/root/SQL/OS/key
实际次数及嵌套并行口径。不要以受控root协议测试或纯函数样本报告native生产成功。
role/provider/审批拒绝/撤销、原取消/较早deadline仍拒绝，原journal数据恢复权限独立保持。

## M3 原首次链与交接

原 `test_installed_file_chain.py --require-postgres` 完整成功断言跑一次：
Tool→原审批/预算→真实只读helper→claim/open/read→签名journal→固定Ref恢复。
unknown先对账不重发；失败记原command/open/claim/signed/ref、停止点与实际成本，不能造journal或假零费用。
不为固定失败反复重跑；根据具体缺陷定向修复，所有失败/费用保留。阶段SHA到即报A，不等最后文档。
不访问用户文件或触发真人；测试用随机native输入必须明确受控。核对临时凭据/key/child/proof/pipe清理，
物理实例去重别名。只改D允许路径，不操作A/其他worker源码、服务或库。独立handoff后停止。

本续项无需B/C同步，flags/checked_metadata/子Agent/DAG/写入安装exec保持关闭。
