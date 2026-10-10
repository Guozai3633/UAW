# MS-R2h bootstrap 输入与装配提案

固定基线 ms-i2k-start / b7b79b150470a80f37b28fd52a2177f6de5b3124，dev/runner。消费已发布 MS-I2k-input-contracts.md 的 PeerRegistrationPort / NativeChallengeSourcePort / RunnerPrincipalMappingPort / RunnerChannelSourcePort；不新增公开 DTO 或修改 pair.complete。

A 首次认证/挑战生产来源在本基线尚未实现。D BootstrapConsumer 逐次验原完整 owner/actor/auth_session_id、实际 PID/创建时间/登录 SID、当前 key role/key Ref/撤销及私钥持有；BootstrapNativeChallenges 取 local original Ticket+活 registry 与 A 独立 challenge 的完整交集。SID/PID 不推 UAW owner，path/approved 不作为输入。

A 最小输入：

1. PeerRegistrationPort.current(actual_identity,role) 必须来自当前已认证 Web 会话/独立账号设备登记，含固定 pairing_ref、双方角色 key Ref 和短期 expires_at；logout/revoke/OS 创建时间变化失效。A 必须验证双方原挑战签名及当前私钥持有，不把公钥上传当证明。
2. NativeChallengeSourcePort.current(original_ticket_id) 必须绑定同 owner/actor/auth_session_id、实际 device OS instance、当前 connection Ref 和原 Ticket/document/proof/key/期限；保持原修订/状态。D 只读取本机已存在的原 Ticket，不从网页载荷自行 issue/mirror。请 A 明确受保护本机 Ticket/code/proof 交付方式、一次挑战消费/当前状态同步以及重连 challenge Ref 的拥有者。绝对路径不传 A。
3. 当前 mapping、registered command Reader、authority、Root 和数据恢复权限必须是真实服务。构造函数注入缺任一项时 capability_unavailable；不能提供夹具作为产品登记。

D 阶段接口 BootstrapConsumer(registration,challenges,mapping,directory,signer,device_key)，local(actual_os_identity)->RegisteredPeer、connected(actual_session)->None；BootstrapNativeChallenges 继承已有来源签名。生产来源到达后 A 用同一对象注入 helper，不需要改变旧公开 HTTP。

若 HTTP 必须新 wire，A 统一发布有版本的契约及阶段标签；D 等实际版本，不扩私有公共协议。消费者影响：A 控制注册/挑战适配及本机 factory，D runtime；C/Tool/schema/锁无变更。成功为已有受保护登记且 current challenge 一致；缺源503，错配403，过期/撤销拒绝；重复原 Ticket 消费由原 SQLite CAS 拒绝，不重发 unknown。
