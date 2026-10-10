# MS-R2g 真人临时根验收指南（pending）

本轮尚未有人实际点击批准，状态 **pending**；自动测试只实跑原生窗口取消/超时，肯定选择使用明确UI double。不要自动化点击“确定”并登记真人授权。窗口API来源：[微软目录选择](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shbrowseforfolderw)。

## 可复现步骤

在Windows本人解锁的Default交互桌面、Session D原目录/锁环境，用PowerShell：

```powershell
Set-Location E:/UAW/.worktrees/runner
$env:PYTHONIOENCODING = 'utf-8'
.venv/Scripts/python.exe -m tests.integration.runner.native_manual --run-human
```

该命令只能由本人显式执行；本文编写时没有运行 --run-human。harness只在ignored tests/.artifacts/D/MS-R2g创建随机临时根/凭据/管道/隐藏peer；账号u1/device d1的独立注册、Run权威和当前授权测试来源受控，不是生产账号登录或正式配对。输出唯一临时测试目录，没有code、私钥或凭据内容。选择树本人选择这个目录；点击“确定”进入第二个独立确认窗口，核对账号/设备、只读能力、期限、完整本机目录和挑战摘要；默认“取消”，本人再明确“确定”才批准。

不要选择用户项目；选错目录时harness拒绝绑定，不打开里面文件，随机凭据/管道仍清理。选择树或第二窗口点击取消，或者等待60秒期限关闭，应该不给批准或读取。native与IPC期限受原已登记challenge/connection约束，过期重跑需新challenge/new connection，不沿用旧权威。

批准后仅写fixture准备的临时file.txt（不是Runner写入能力），实际双进程Runner只读该UTF-8测试文件，真实OS device key签名journal传回，撤销该临时根并清理随机凭据/管道/helper/临时目录。只保留human-native-receipt.json的实际Ref/状态/撤销/cleaned回执，不保存绝对路径/正文/秘密。未实际点击时不可提前写actual_click_completed。

验收应分别记录：目录取消、最终取消、等待到期、本人实际选择确认+真实读取/撤销；本人的取消操作也不要用自动WM_CLOSE测试顶替。若桌面不可交互/锁屏返回capability_unavailable；如果实际批准未完成，报告not_passed并保留错误，不能编造成功。

## 仍独立的产品门槛

真实账号/OIDC、受保护控制挑战与owner/device关系、首次配对bootstrap、公共HTTP DTO/注册、配置/flags和Tool业务结果验收归A。这个harness仅证明本人操作临时选择窗口和组件只读链；没有授予写入、安装、exec，也不决定D03或把开发SQLite当D01决定。
