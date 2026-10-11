# MS-I2l：第六次本人只读授权回执

2026-10-11，运行源码 `4071f49ff462f313629050ca80d0b0df5e55fd83`（A6 元数据；生产授权实现同 `cb215bcffba8a9eff8aa55802b54854109f4a8e6`）。原开工和阶段标签不移动。

实际操作从 08:07:15.478793 UTC 至 08:09:19.523088 UTC：本人账号设备确认、目录选择、只读范围确认已完成。控制端核对 active 登记、实际 Windows 双进程握手、原 consumed root ticket、owning native decision、device Ed25519 选择签名、workspace、只读 capability 与 revision 0，输出 `native_root_bound`。原通道截止为 08:09:28.660210 UTC，没有延长。

该诊断在 grant 和签名核对成功后立即执行 finally 清理。子端仍在 bind_selection 的最终复查时收到自有关闭取消，私有诊断为 CancelledError/internal_error；因此本次证明真人选择及 grant 已核对，不证明子端 on_connected 已完整返回或后续文件命令成功。后续网页入口要等待该 callback 完成，再独立复查当前来源，不能只凭 grant 出现显示可用。

自有实例、通道、随机 OS 凭据和临时 Web session 已关闭；零用户文件正文读取，零新模型调用。关闭后的 key、通道及 grant 不提供生产权限。历史超时和第五次失败保留。网页 installed 生命周期、原 Tool/预算/Runner 文件链及交付仍在本轮继续；flags 保持关闭，未标整轮 accepted。

原始日志位于本机忽略目录 `tests/.artifacts/A/MS-I2l/m2-native-root-attempt-6.log`；可提交的原回执与日志 SHA256 见 [独立证据](evidence/ms-i2l-native-human-6.json)。
