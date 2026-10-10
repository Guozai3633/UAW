# MS-R2h M1 固定接口

dev/runner，ms-i2k-start / b7b79b150470a80f37b28fd52a2177f6de5b3124。原 MS-R2g 提交/失败/清理记录保留。

BootstrapConsumer(*,registration,challenges,mapping,directory,signer,device_key) 组合原 A ports；local(actual OsIdentity)->RegisteredPeer，connected(AuthenticatedPipeSession)->None。BootstrapNativeChallenges(*,bootstrap,state,registry,channel_ref,device_id,mapping,clock).current(ticket_id)->原 NativeChallenge。没有首次 issue/enroll/mirror API；精确原 Ticket/document/state/revision、完整 owner/actor/session、OS实例、当前key/角色/摘要/期限必须交集相等。

当前没有 A 生产首次认证/设备/挑战 adapter，缺来源 capability_unavailable，见 MS-R2h-bootstrap-inputs.md。原签名/nonce/一次使用/CAS不变，不改 pair.complete。来源await后复查完整 owner/角色key/期限定时和实际连接；取消原 CancelledError 传播。

M2固定装配 ReadOnlyHelper(*,bootstrap,protocol,commands,journal,executions,roots,registry,currency)，同一 device ProtectedSigner/current目录/owner mapping/root/admission/journal/registry；start()->HelperAddress(name,actual identity)，accept()->新content channel_ref，authorization()->NativeReadAuthorization，serve_once()->真实原receipt_ref，disconnect()/close()异步幂等。A负责生产 factory 和输入；D下一阶段交实际启动和双进程回执。

M1实际Windows当前 key/OS/pipe/账号会话交集测试22不同节点；首轮21通过/1 fixture revoke_key 参数错误，失败XML保留，修正后完整复跑。肯定UI和A来源是独立明确double，没有真人确认；没有开flags/写入安装exec。阶段源码提交后继续M2-M4。
