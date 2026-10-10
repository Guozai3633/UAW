# MS-R2i 本人验收与缺源指南

本页是可复现步骤，不是本人确认通过回执。D未点击批准、未运行 --run-human、未读取用户项目。仅真实 native 取消/超时自动测试；测试 affirmative 是明确 typed UI double。

## 本轮已经实测

D固定 helper 首次 start(first_start=original_policy,on_progress=observer) 等待原挑战；普通15秒、首次最长90秒，一次monotonic deadline，waiting仅进度。Windows隐藏进程初始化期间stop/EOF排空native自有窗口/worker、迟到helper和短读；只有本人窗口可见。实际临时根读取、OS设备签名journal、新连接/重启恢复原content Ref，不重发未知command。OS随机namespace只触碰本session临时凭据，finally删除后重新resolve为missing。

## A 完整 installed 来源的门槛

A已正式发布 ms-i2l-a1 /348df5ae3032f898def9bd72a1b7e22cc21fe8c4，提供固定安装模块及受保护 locator/configuration；应使用该实际来源：完整当前Web/CLI账号、原owner/session→device/control/device角色和OS实例关系，当前角色目录/OS protected handles、RunnerEnrollments原challenge与journal、EnrollmentProofClient受保护管道locator、实际paired factory、后续根Ticket/code/proof/current challenge、Root/Run/lease/fence/命令Reader与数据权限来源。它们不能从SID/PID、argv、网页path/approved或命令body推导。A当前root Ticket实际签发/交付、on_connected本人绑定和父端root/file authority仍缺；缺源503，D测试factory不是生产替代。

消费固定A1兼容阶段时，A先读D stage-interface/stage-cancel构造，复核固定来源，prepare只输出独立核对的identity；控制端独立登记原挑战，构造其policy，proof server与start并发且finally关闭。首次等待进度用于提示本人等待，不改变active/授权/ready。已有原active同实例普通启动；新PID/创建时间重新登记，不沿旧active伪装。

## 本人可复现操作顺序

1. A准备**本轮自己的临时测试目录**，本人核对可见账号、设备、只读范围、原挑战hash和期限，当前认证账号来源真实。除了本人窗口，后台helper隐藏。
2. 首次账号设备窗口由本人亲自确认或拒绝；确认只绑定身份，不授予根。取消/关闭/期限/当前来源撤销必须退出，A记录原公共错误。D stop不能自动点击Yes。
3. ready后通过真实登记连接，另一个本人目录选择窗口只选刚创建的本轮临时根；复核只读范围/期限再本人确认。绝对路径只留本机，控制面只得opaque根/签名凭据。
4. A登记原固定file.read（UTF8常规临时文件，总1MiB/返回64KiB界限），签名/当前authority/Root/key/channel/Run/lease/fence均齐后读一次，核验实际设备签名、原command/attempt/Usage和content Ref。
5. 有意丢回复只能recover原已登记命令；删临时文件/取消Run后重启新连接恢复原journal，不再次打开文件。unknown禁止重发；root/key/account撤销阻止新读，数据权限仍独立复查。
6. finally回收本轮自有helper、pipe、OS handles和随机凭据；记录每个新进程OS实例/通道Ref、公共receiptRef、cleanup和失败，不保存私钥、proof/code、完整路径/正文或DSN。禁止按名字杀其他进程。

记录应明确：actual_person_confirmed / refused / expired / cancelled / pending；若没有本人实际操作只能pending。通信、protected proof通过、controlled Yes、SQL通过、Runner ok均不能代替本人授权或Tool业务成功。

## 当前 D 临时根 native 单独手动入口

```powershell
.venv/Scripts/python.exe -m tests.integration.runner.helper_manual
# 默认仅打印pending；不启动窗口。
# 仅本人明确要验证D临时根UI时，由本人手动执行：
.venv/Scripts/python.exe -m tests.integration.runner.helper_manual --run-human
```

后者沿既有MS-R2h手动harness创建随机临时根、真实隐藏IPC/OS密钥/设备签名读取和撤销清理，但账号/owner/challenge/authority仍受控，不能证明本轮真实installed首次账号链；回执位置仍是MS-R2h harness自己的ignored目录，必须标其准确来源。本轮只运行默认pending并保存tests/.artifacts/D/MS-R2i/manual-default.log/human-pending.json。

不打开写入/安装/exec或flags、不代替用户选择模式、不决定D01/D03/D06。完整产品/本人/Tool/Model/HTTP整链由A接受，不把D组件回归当全量产品通过。
