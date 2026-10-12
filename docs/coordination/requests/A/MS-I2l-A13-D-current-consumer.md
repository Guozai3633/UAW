# D 原只读预算修复：消费 A13 统一来源

本文件是原 MS-I2l-A9-D-original-read-budget 的具体续项，沿用用户直接发给 D 的授权。
只有 DISPATCH 正式记录准确来源 SHA 后开工；读取文档不能替代正式发布。
不新开共同包，不同步浮动 integration，不改写 D 原历史、handoff 或失败记录。

## 输入与允许目录

固定代码由 `ms-i2l-a13-source` 提供，完整 SHA 以远端 DISPATCH 正式记录为准。
先核对 tag peeled commit 和记录相同，再由 D 在原 dev/runner 自行合入准确来源。
接口与边界见 `MS-I2l-A13-current-source.md`；A 的 installed helper 已保存绑定一致的 current_source，
尚未传给 D runtime/endpoint。A 负责之后的 production factory 接线，不代写 D 源码。

只改 D 原允许 `apps/local_runner/uaw_runner/`、D tests 和 `docs/coordination/requests/D/`、D handoff。
不得改 A Run/SQL/installed helper、公共契约/依赖锁、B/C 源码。公共需求先提案交 A。

## D 两个交付点

### M1：检查点与独立消费接口

1. 列出 endpoint.dispatch/watch、ReadOnlyRunner.current/execute、AsyncAdmission 的每个等待、
   效果和恢复边界。说明哪些来源由 composite 覆盖，哪些 native/key/OS/CAS 必须独立复核。
2. 给 ReadOnlyHelper/HelperReadAssembly/ReadOnlyPipeEndpoint/ReadOnlyRunner 添加显式可选
   RunnerReadCurrentPort 消费入口，保持未注入的旧调用兼容；不能把模型或 IPC 传来的对象当实现。
3. 消费入口验证完整返回类型、原 command/hash、完整 actor/owner/device/channel/root/context
   与原 runtime 对象一致。禁止省略“刚刚 current 过”之后关键 await 的检查。
4. 回复 deadline 在原 serve_once owning 边界固定，传到实际消费；保留所有更早的 command、
   lease、root 和 key 期限，不能每次调用重新生成 now+10。
5. 按同一检查点消除已被统一来源完整覆盖的递归展开，而不是再独立调用完整 authority
   重做同一组检查。新增等待后是否需要 fresh current 应按效果边界明确，不缓存 allowed。

提交阶段源码及检查点表，立即报告完整 SHA、构造/调用示例与所需 A 参数。
然后继续本续项后半段；A 可以据阶段 SHA 接线，不必等待最终全部完成。

### M2：执行、监控、回执及预算验收

1. 原签名命令核对、native 目录授权签名/当前状态、双方角色 key/OS 实例、实际 live pipe、
   原 admission/执行一次使用 CAS、OS 根/文件句柄身份与读后/签名前复核保留。
2. wait_changed 当前仍全量读取，没有廉价通知承诺。监控避免和 dispatch 高频重做同一图；
   先提出明确的当前变化/断连/双方 key 覆盖方案，不能以测试 Event 或长时间睡眠替代生产撤销。
   若 A 尚缺必要的廉价来源，交具体提案并保留该门槛 pending，不以耗时为由删除检查。
3. recover 和已有 journal 数据读取继续走原独立 Reader/数据权限。取消/过期阻止新执行，
   不直接否认本来可访问的旧签名回执；不要把它们改用 active execution composite。
4. 回归原 command 一次发送、实际一次打开、原 signed journal 发布与丢回复恢复。
   original unknown 不重发；不扩大 10 秒回复、30 秒 lease、120 秒根或启动期限。
5. 注入或原受控测试覆盖等待期间的 Run/角色/配置/provider/预算/lease/fence、双方 key、
   目录/owner/通道变化；真实 Windows 原文件链测试使用临时材料和明确受控 native 决策，
   不操作真人窗口。保留所有失败、次数、来源耗时、cleanup 和缺失依赖。

最终提交与独立 handoff；flags 保持关闭。不证明模型文件交付、原浏览器本人接受或整轮完成。
如果尚无实际一次读，将组件交付和完整首次链失败分别报告。

## A 后续

A 接收阶段接口后，在 A installed factory 向 D 新消费参数传入原同对象来源，核对实际
账号/设备/目录/模型/provider/Run 准入与 HTTP owning service。真实汇合通过后才进入原文件
低信任 Context、固定用户模型、准确引用、成果核验、本人页面及接受；最后一次汇合全量。
