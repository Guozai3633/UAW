# 本地Runner消息与执行约束

状态：协议0.1设计，设备/后端尚未实现。接口参数见[Runner分类](RUNNER.md)。本地Runner和云沙箱使用相同Workspace契约，执行边界分别落实。

## 1. 配对与连接

1. 本机Runner生成设备密钥和随机nonce，发pair.begin取得一次配对事务。
2. 用户在已登录账户页面确认设备和请求能力；服务器记录确认，验证码不是模型授权。
3. pair.complete校验事务、一次码、设备公钥和用户已确认状态，建立设备会话；失败不授予任何根访问权。
4. 设备通过受认证的TLS长连接接收命令和发送回执。首稿建议WebSocket传输，协议对象不依赖具体Web框架。
5. heartbeat报告实际进程与租约；凭据撤销立即停止接收新命令，服务标记设备离线/撤销。

配对通道是控制面专用入口。执行长连接可以规划为`/v1/runner/connect`；该路径和配对HTTP适配实现时单独纳入OpenAPI，当前Runner分类只承诺消息契约，不冒充已存在的HTTP路由。连接认证失败不会向用户聊天回显设备秘密。

## 2. 项目根来自可信本机选择

root.select只接受本机用户交互得到的Path，检查真实根后签发短期RootSelection。网页projects.bind提交selection_token，服务器验证主体、设备和有效期，返回ProjectBinding。输入框中的路径不作为授权凭据。

服务存root_handle和展示名；本机保存句柄到真实根的映射。每次读写重新校验真实路径、符号链接和绑定修订。exec并非只读目录操作，必须报告实际OS隔离或明确原生授权。Runner不使用模型可改的工作区文件保存自己的设备密钥。

## 3. 执行命令信封

[RunnerCommand](objects/RunnerCommand.md)包含command_id、关联operation_id、固定request_ref、内联[RunnerParameters](objects/RunnerParameters.md)、TrustedExecutionContext、fencing_token、expires_at和signature。

- parameters.action明确例如`process.exec`，parameters.parameters只能符合该方法的schema。
- request_ref保存服务侧已签发参数版本；Runner核对其摘要与内联参数一致，不能将它当任意远程文件路径。
- 签名覆盖信封全部业务内容和有效期，排除signature字段；使用设备会话约定的规范JSON编码。编码和签名算法是协议profile，双方必须一致，不能用普通字符串拼接算Hash。
- command_id在重复发送、网络超时和重连中不变；相同ID不同签名参数必须拒绝。attempt_id由真实执行产生。
- 信封的可信主体只是签发依据；设备还复核本机绑定、当前能力、租约栅栏、网络/进程策略和期限。

同一命令到期或失去fencing_token后不能启动；已经启动的进程按取消/停止策略管理，并保留实际输出与效果。Runner持久保存命令受理记录和进程句柄，服务重连查询原状态，不能重复启动同一逻辑命令。

## 4. 回执与日志

[RunnerReceipt](objects/RunnerReceipt.md)绑定command_id、实际attempt_id、状态、typed成功payload/等待Ref/Failure、实际usage和设备签名。成功payload由[RunnerSuccessPayload](objects/RunnerSuccessPayload.md)按action选择，不能用file.read结果回应process.exec。

`process.exec`成功只证明启动接口成功，返回ProcessRecord.status=running。`process.poll`读取实际exit_code、stdout/stderr引用和输出游标；输出按顺序限量传输，大输出持久化为blob。不能以空输出或丢失进程句柄推断测试通过。

进程终止后返回真实状态，shell命令改动也采集ChangeSet。输出以不可信文本保存，不能让日志里的指令改变权限。设备回执Hash/签名验证失败时暂停相关动作并提示诊断，不把回执喂给模型当可信结果。

## 5. 断线、停止、环境与回收

断线不表示进程停止。服务将相关节点等待/受阻，重连后根据本机执行账本和进程实际状态对账；进程已成功不能再次执行。丢失实际进程为lost，可能残留进程必须报告和处理。

process.stop先软终止后有界硬终止进程树；没有真实停止回执不宣称stopped。环境ensure按批准模板执行真实安装/版本检查，安装源和系统权限单独校验；Python venv不提供OS隔离。release先停止或显式移交后台进程、归档需要成果，再回收获准任务目录；不得递归清理用户项目根。

服务端的权限撤销、配置撤销及设备本机权限撤销同时收窄；安全撤销优先于旧固定配置。恢复节点必须重新核验设备、项目/环境版本、原始未提交修改和未决副作用。
