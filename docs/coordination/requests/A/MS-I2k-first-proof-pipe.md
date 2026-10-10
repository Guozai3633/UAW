# MS-I2k 原首次证明管道：A 内部接线

2026-10-10；本包内阶段实现，不新增 HTTP、共享 DTO 或默认权限。

## 固定入口和来源

控制端 `EnrollmentProofServer(provider, owner=original_web_principal, enrollment_id=original_id)`；provider 是原 `WindowsEnrollmentControlProof`，由当前登记服务、角色目录及 OS 凭据构造。`await prepare()` 返回随机本机 pipe 名；`await serve_once()` 只发送该登记的控制签名证明；`await close()` 释放自有句柄。

设备端 `EnrollmentProofClient(service, directory, owner=original_web_principal, enrollment_id=original_id, pipe_name=trusted_name)` 实现 `CurrentEnrollmentControlProofPort.current`，可注入 `FirstEnrollmentDeviceFactory.proofs`。原服务、账号和 pipe 名来自可信安装/启动组装；不能从模型、网页正文或任意命令接纳这些绑定。名字只能定位通道，不能证明账号或授权。

管道仅处理 `protocol=uaw-enrollment-proof-v1` 和原 enrollment_id；响应只含协议、原 ID、原文档 hash 和控制签名。请求与响应最多4096字节，拒绝重复字段、额外字段和错误原文档。不会传私钥、目录路径、文件正文、approved 或可执行命令。只有双方原登记当前 OS 实例和角色签名能通过。

## 顺序和资源生命周期

1. A 独立观察已准备 helper 的真实设备进程，核对账号/角色/OS实例后登记 pending。
2. 原控制进程复查服务保存的完整挑战及双方当前角色，创建仅允许当前登录 SID 的一次 pipe；取消时排空线程里晚生成的句柄并关闭。prepare/serve/client分别有10秒上界。
3. 设备端从当前服务读原挑战，先核对自身 OS 实例，再连接并核对控制端实际 PID/创建时间/SID/登录实例。
4. 控制端先读有界消息，随后核对实际设备实例及线程令牌。Windows 的服务端令牌复核要求先接收一条消息；解释请求、读私钥和发签名之前身份必须通过。不能用消息声称的 PID 替代内核观察。
5. 控制端只给原挑战签名，等待后再查原账号/挑战/角色和设备实例；设备端核对原文档 hash、当前控制角色签名、当前服务/OS/角色。不符即拒绝。一次服务结束关闭原 listener，不能复用发第二份证明。
6. 签名只满足 FirstEnrollmentDeviceFactory 的控制证明输入。真实 native 决定、owning journal、两角色签名和原登记 active 后才能创建已配对 helper。目录选择与只读根授权仍是之后的独立真人操作。

## 已验证和未完成

9不同定向节点最终通过：3个真实 Windows 双进程/SQL节点（成功、错误请求、错误进程）、4个有界/歧义消息拒绝、原 owner 拒绝、取消后实际句柄清理。父端原Web/SQL/角色/OS保护私钥与真实 pipe 实跑；子端挑战 Reader/账号是明确受控夹具，不是生产安装组装。测试不打开真人窗口，登记仍 pending，随机凭据删除后404复查。

首轮 venv 启动器 PID 与实际 Python 子进程不同；改用固定基础 Python 和已安装依赖测试环境，保持原 PID 断言。测试 stdin 代码页导致中文临时路径无法定位，改为 ASCII JSON 编码路径，不改测试身份/期限断言；原失败、超时、未创建凭据的清理异常均保留。服务器令牌检查顺序及异步晚句柄取消已修，最终9节点和189源码类型检查通过。

仍需：实际安装模块提供原认证账号、角色目录/保护凭据、此 locator 的可信交付、完整 paired factory 与当前通道/命令/根来源。D原 `HelperProcess.start` 等ready为15秒，而首次native窗口可等待60秒，不能直接拿它当完成接线；需A明确第一阶段启动/等待边界或提交D接口提案。当前不启动真人helper，不把 pipe通过标为首次配对/文件Model整链accepted。
