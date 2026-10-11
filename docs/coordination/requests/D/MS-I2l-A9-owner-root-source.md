# A9 D：真实原链的 owner/root 接线拒绝

基线225f5006，D阶段7395eb7f。stage-chain.xml/log：原成功期望节点
1 failed / 89.83s；command1/open0，真实SQL/Web/Windows双角色keys与双进程。
native/审批/初始配置均受控临时fixture，不是本人授权。
4随机凭据不存在、2key撤销、原child退出、proof pipe关闭。

D新检查点测量显示 endpoint_dispatch 2.606s、runner_execute 1.512s、
runner_current 0.886s、root_source 0.023s 均在首次根查询处返回
`enrolled_actor_denied`；authority尚未进入（不可写为0成本）。父端输出ipc_broken。
原完整记录在tests/.artifacts/D/MS-I2l-A9/stage-chain-temp/*/metadata.json。

NativeRootSource.current(device,workspace,ctx)既有契约以ctx.principal（user）向
RunnerPrincipalMappingPort.owner查询独立owner，查询前后两次，真实本机根/选择/key仍检查。
A PairedInstalledFactory给此roots.mapping注入EnrolledPeerRegistry；该owner方法只匹配
enrollment.proof_document.control/device.actor，两者为登记的通道actor，故本轮实链用户未匹配。
D未把ctx用户自报当权限，也未把owner改成body或绕过mapping。

A应提供同一实际登记来源的owner映射适配：原真实认证owner会话必须与当前enrollment.owner、
双角色登记/OS实例/当前角色keys、当前原连接及device真实关系一致；
既支持原authenticated通道actor的Runner调用，也支持RootSource既有可信context owner查询。
可单独为RootSource提供A owning映射，同时bootstrap/AsyncAdmission保持原actor映射；
具体策略由A发布。不得将同名user.id或ctx.principal复制为owner，不接受caller approved/path。
缺源或错owner仍403/503；更改任何真实关系/会话/撤销/期限必须在await后拒绝。

这是一项已实跑的A装配冲突；不是证明其它SQL成本问题已解决。
原watch/完整authority继续保留；有界current与变更port提案见MS-I2l-A9-stage-read-budget.md。
A发布准确修复源码后D消费，当前不改A映射/公共RootSource签名或旧Run固定来源。
