# MS-I2l A8：浏览器原实例到文件工具的来源装配

2026-10-11。继续当前 MS-I2l M3，不建立新包。A7 浏览器启动与停止入口保持；新增内部装配把当前 Web 拥有的原实例连接到 C 的 file.read 与原 Runner 控制端。

## 实际实现

- `InstalledLifecycle.owned_ready` 只返回当前进程中原会话拥有、回调已完成、工作区完全相符且仍有效的实例。历史 ready 记录、同账号新会话、另一个工作区均不能提供来源。
- `InstalledFileRoute` 从原实例与当前 RunnerDevices 取得设备版本和摘要；等待后再次复查根、设备和实例，没有请求传入的设备或目录映射。
- `RegisteredFileDataAccess` 消费原持久 Tool action/attempt、登记规格、完整会话、当前角色、固定用户模型、固定/当前配置和当前 provider。取消后可以检查已存在结果的数据权限；它不恢复执行许可，不递归调用桥接，不发送命令。
- `OriginalFileApprovalGate` 将 Runner 请求与原 Tool context 和完整参数逐项核对，再消费原 `ToolApprovalAdapter`。缺适配器、pending、declined、变更参数或批准后撤销都拒绝执行。
- `assemble_installed_file` 用原连接的 channel registry、session、OS control key、原 native journal/根与签名校验器组装 `RunnerCommands → RegisteredFileBridge → assemble_file_tool`。进程与密钥清理仍由原 lifecycle 拥有；组装不授予角色、发布 provider、开 flag 或启动 Run。

## 同一个文件开关

C 已固定 ToolSpec 的名称为 `file_access`，Runner 与管理员配置名称为 `local_files`。配置服务现在显式把前者映射到后者，固定和当前配置都必须允许；这不是第二个开关。`implemented=False` 仍不可用。管理员原 publication gate 不变，仍不能发布 enabled flag；本阶段没有开启产品文件能力。

## 验证与边界

最终 **86 个不同节点通过**（81 SQL/兼容，2 实际 Windows 来源，3 关闭竞态单元）；报告 SHA256 与失败历史见 [阶段证据](evidence/ms-i2l-a8.json)。原审批与数据来源使用实际 PostgreSQL；测试内 provider 连接元数据、初始 enabled 配置和根 Reader 是明确受控来源。测试先建立新配置版本，再提交新 Run，没有改写旧 Run 固定来源。Windows 双进程用真实 OS keys、IPC、native owning journal/签名和原 callback；其 native 输入是测试自身临时目录，不代表新的本人操作。没有用户文件正文或新模型调用。

测试准备中重复角色登记、重复创建审批、之前 optional-null/固定 attempt/fixture provider 的错误均保留；最终消费原 request ID 和记录，未降低业务校验。Mypy 启动器一次路径规范化失败也保留，使用同环境 `python -m mypy` 验证源码。

## A 后续接线

还需要管理员 file provider/availability gate、每个 Run 的精确目录范围与 file 角色、混合工具/审批读取的原来源路由、文件材料到 Context/模型/成果，以及真实 B 页面本人授权和交付验收。当前后台仍加载 A7，不能把本阶段内部装配或受控检查描述成产品文件整链已完成。默认 flags、写入安装 exec、子 Agent/DAG 保持关闭，旧全量来源不更新。
