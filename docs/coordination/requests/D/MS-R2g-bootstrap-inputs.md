# MS-R2g：A可信挑战登记与首次配对输入缺口

基线ms-i2j-start/abb4590f2bfe53c601e0f6a4a3b65447ba4ec502；D只消费现有public ports，未修改schema/锁/HTTP或发布配对V2。

本包RegisteredNativeChallenges可用于**已独立登记账号/设备/当前角色key +真实IPC连接**的root Ticket确认。它从LocalState原挑战和当前registry/mapping读完整身份；UI成功与Windows SID/PID都不能生成UAW账号。WindowsNativeConfirmation仍需当前device角色key与固定challenge公钥一致，不能用客户端public_key/approved绕过。

首次账号配对的bootstrap尚无真实A来源：旧pair.complete DTO没有内联挑战证明，也没有独立认证映射凭据，D继续返回不可用。不能从内部Ticket.document签名推断已经有公开协议。A须决定并发布确切受保护挑战登记来源/版本（若需公共DTO由A统一发布），D不自设。

A最小输入接线：

- 原准确challenge/Ticket登记（nonce/一次码/版本/期限/账号/设备/current role key/根handle），由可信账号会话与设备登记来源发出和固定，不能根据HTTP路径/模型声明产生；D local state仅镜像已校验原登记，不自行注册生产账号。
- 当前实际owner/actor完整Principal和auth_session_id、device关系以及精确OS实例/本机login/SID+creation、current key Ref/撤销与pairing Ref/期限，通过现有IPC PeerRegistrationPort读取；缺任何来源不可用。
- 将已登记ticket_id与原code/真实key持有proof送给受保护本机native入口，仅触发本人选择窗口；主体/path/capabilities/approved不是输入授权。native期限和签名证明在返回后再次核验，opaque RootSelection按原RootSelectionPort一次消费。
- 原selection/Ticket/device/owner资料由A守护来源进行恢复，确切Ref与本机实际根记录分开；绝对路径只留D本机LocalRoots/grants，HTTP/控制面不返回。

消费方：A认证/控制端/组装与Root绑定入口，C只消费A桥接/原command和receipt，B仅显示已登记项目/本机决定状态，不向D私有类传路径授权。当前D没有改A源码，也不导入其他worker开发分支；生产bootstrap缺失不妨碍独立组件验证，但用户项目/完整配对验收保持pending/unavailable。
