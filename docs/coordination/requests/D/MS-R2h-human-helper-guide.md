# MS-R2h 本人选择与隐藏 helper 验收指南

**状态 pending：开发过程中没有执行 --run-human，没有自动点击批准。** A 生产认证账号/首次设备挑战尚缺，以下是独立临时根真实 Windows/native/OS key/隐藏 helper/IPC/read/journal 的可复现实验；账号 u1/s1、设备 d1/owner/Run authority 和首次 Ticket 来源为明示测试 ports。真人点击即使成功也不能计为生产 bootstrap 完成。

在 E:/UAW/.worktrees/runner 的交互 Windows Default 桌面，用本工作区冻结环境：

```powershell
.venv/Scripts/python.exe -m tests.integration.runner.helper_manual
# 默认仅pending；不启动窗口，不批准。
.venv/Scripts/python.exe -m tests.integration.runner.helper_manual --run-human
# 本人主动执行；保持窗口可见，其他进程CREATE_NO_WINDOW。
```

先检查控制台显示的新建 `tests/.artifacts/D/MS-R2h/human-*/selected-project` 路径。仅选择这一根：Windows原生目录树由本人操作，随后窗口展示账号u1、设备d1、只读范围、准确期限、挑战和目录；默认取消。本人审阅后点击确定，或取消/关闭。不得自动键鼠批准，不选用户项目/已有资料。当前活连接最多60秒，指南等待55秒；超时失败不自动重试。

helper 的实际OS创建时间与随机namespace内当前角色key、独立owner、原challenge/code/proof均复查。原Ticket批准→一次RootSelection bind→只读自身UTF-8/保留原换行→实际device Ed25519签名journal→新连接复查并revoke→finally清理随机OS凭据/管道/子进程/临时目录。选择其他目录时，在bind/read前拒绝；不会读取该目录内容。没有新增Runner写入动作，文件仅测试夹具预置。

回执 `tests/.artifacts/D/MS-R2h/human-helper-receipt.json` 记录 pending或actual_person_confirmed、content固定Ref、kind、revoked与cleaned，不记秘密/正文/绝对根。取消失败可以留下已真人确认的本机记录但没有成功读取，实际字段如实记录；不把Runner ok映射Tool applied/零费用。生产首次认证/挑战字段始终pending。

A生产接线：安装时可信HelperAssemblyPort.create(actual_identity)->HelperApplication；明确真实受保护Web full session→设备/当前role key/双方持有证明→OS instance→原 Ticket/code/proof/短期期限/当前活channel。D BootstrapConsumer/NativeReadAuthorization交叉复查；缺这些源不能用此测试工厂替换并挂HTTP。原native inputs提案MS-R2h-bootstrap-inputs.md，构造MS-R2h-stage-helper.md。A生产实际本人流程验收另留回执，不能复用本测试账号的肯定UI结果。
