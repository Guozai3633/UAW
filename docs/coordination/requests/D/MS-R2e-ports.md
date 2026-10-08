# MS-R2e 阶段接口、公共缺口与 A 接线

基线 ms-i2h-start / f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8。本页不发布公共协议或 flags。

```python
ReadOnlyRunner(*, protocol: RunnerProtocol, command_ref: Ref,
    journal: ReceiptJournal, executions: ReadExecutionJournal | None,
    currency: str, roots: RunnerRootSourcePort | None = None,
    channel: RunnerChannelSourcePort | None = None,
    channel_ref: Ref | None = None, signer: ProtectedSigner | None = None,
    device_key: DeviceSigningBinding | None = None)
async execute(command: RunnerCommand, *, authenticated_principal: Principal) -> RunnerReceipt
```

每个已登记固定 command 创建实例。command_ref/channel_ref 来自独立登记服务；输入必须与 Reader 的完整 command/device/owner 相同。authenticated_principal 来自可信适配器，不读取 body 自证。currency 由实际预算配置提供，Usage pending 仅填实际 wall_time_ms，不推断费用或 Tool applied。

```python
runner = ReadOnlyRunner(protocol=adapters.protocol, command_ref=registered_command_ref,
    journal=adapters.journal, executions=ReadExecutionJournal(development_reads_path),
    currency=actual_currency, roots=adapters.roots,
    channel=actual_channel_source, channel_ref=registered_channel_ref,
    signer=ProtectedSigner(current_key_directory, os_credentials),
    device_key=DeviceSigningBinding(actual_device_id, registered_device_key_id,
                                   protected_device_private_handle))
receipt = await runner.execute(registered_command, authenticated_principal=actor)
# 缺真实依赖/错误主体/来源变化：拒绝，不打开文件。
# 相同请求：恢复原签名；unknown/in_progress：不可用，不重新执行。
```

实际固定 Ref 保存在 ReadExecutionJournal，kind=content/version=1/hash=完整签名回执摘要，不新增 RefKind。A 独立核验/登记 FileContent 到 Tool，Runner ok 不等于 Tool 业务成功。

## 最小公共提案

当前 FileContent.text 引用 Text/maxLength=16384，ASCII 64KiB 违反契约。建议仅 FileContent.text 改 string/maxLength=65536，不扩大全局 Text；组件仍以 UTF-8 64KiB 为实际字节上限。消费方 Context/Tool Reader 继续按字节/模型预算有界，不自动整页加载。成功例65536 ASCII，拒绝65537 bytes。由 A 发布后消费。

本包同时遵守16384字符和64KiB，不静默截断；16384四字节字符可达64KiB。whole/text_span offset从0、end exclusive；不支持 cursor/其他 Location。全文实际 SHA256，片段不充当全文摘要。

## 来源、持久化与限制

实际 RunnerChannelSourcePort 完整 owner/actor/device/pairing/channel/key 固定 Ref、connected/期限；PrincipalMapping 独立校验关系。Reader 每次检查当前数据权限，包括 owner/device/key/root 撤销与 command 固定 hash/version；历史 cancelled 不授新准入。默认缺生产 IPC/确认；受控 fixture 不是实连。

新执行复查当前 authority/request/parameters/policy/workspace/root版本/lease/fence/flags。恢复复查 Reader/channel/mapping/根权限/实际设备签名，不再次 reserve/read，也不缓存许可。A 提供部署源及数据恢复策略。

Windows CreateFileW 持有根/目录/文件句柄并拒绝 write/delete sharing；实际 GetFinalPathNameByHandleW/FileIdInfo/Basic/StandardInfo 对照路径与登记根身份，拒绝 reparse/hardlink/特殊文件。OS 操作在线程，句柄保持至签名与提交。其他 OS 或缺 API/凭据不可用，无普通 open 降级。仅临时测试根，不决定 D03。

ReadExecutionJournal 显式开发 SQLite：claim 持久化先于打开；signed 持久化先于终态 publish。无签名未知中断不重读；有签名中断恢复原内容发布。日志不决定 D01，无跨服务权威事务；晚撤销可留下真实历史记录，但不能返回失权主体。A 接生产日志与产品入口；flags 不改。


## 最终组件补充（2026-10-08）

固定构造/execute 签名与阶段版本相同。新准入前 ProtectedSigner.check_private 实际读取当前 device-role 密钥的受保护句柄并证明公私钥一致；不签发测试或空执行回执来证明可用。真实设备签名后再次查询完整当前源；未知签名前取消保留 claim，传播 CancelledError/取消 Failure，不伪造 cancelled 回执或零费。

原 RunnerProtocol.verify_receipt 追加 file.read 的实际 UTF-8 encoding 与签名请求 Location 的精确比较；不能用设备签名把另一个读取范围替代原范围。既有签名、command/attempt/action/workspace/path/Usage 校验保留。

恢复只读取原始已签名 receipt：Reader、独立 owner/channel、当前 control/device key、grant owner/device/workspace/revision/read 权限和期限每次复核。恢复不需要原文件仍存在，也不再次调用 execution authority、reserve 或 OS 文件读取；原命令已过期或 Run 已取消仍可在当前数据权限有效时恢复。根期限/撤销或数据 Reader 拒绝即拒绝；A 必须为真实登记 Reader 提供相应当前数据访问策略，不把历史 receipt 当授权。

开发 SQLite 文件由可信组装指定三个独立路径：PersistentAdmissions(admissions_path)、ReadExecutionJournal(reads_path)、ReceiptJournal(receipts_path)。重启组装同一路径并重读实际登记源。跨进程 claim 唯一；同 command 不同完整 owner/session、原 attempt、签名内容、command Ref 发生冲突；unknown/in_progress 明确不可用，不自动重试。已 signed 但未发布的结果只能去重发布原 signature/Usage，不能读取新内容。完成后 Ref 内容摘要覆盖完整已签名 RunnerReceipt。

真实本轮检查覆盖431项（原326＋新增105），包括真实 Windows temp 文件/句柄/SQLite/Ed25519、随机 Windows vault 控制和设备私钥重开签名与清理。主回执 tests/.artifacts/D/MS-R2e/full-junit-1.xml、checks.json、windows-read-receipt.json；受控 registry/authority/channel/native confirmation 不代表生产 IPC/实际用户确认或 Tool 业务完成。没有运行 PG；本包仅本机组件日志，不需要 SQL 服务。

Windows 本地常规文件只读组件没有针对任意 hostile OS/管理员、驱动或预先建立的可写内存映射的隔离证明；当前分享模式拒绝普通现有/新 writer、delete/rename，并通过句柄身份/路径/时间/大小检查拒绝观察到的竞争。D03 生产隔离与其他 OS 读取仍未实现。不要据此开放 file_access 或通用网络入口。
