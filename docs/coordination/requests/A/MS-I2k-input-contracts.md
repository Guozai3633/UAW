# MS-I2k 固定输入与接线协议 v1

本文件与正式 ms-i2k-start 同时发布。以下区分已实现入口和仍需实现的来源；缺来源必须不可用，不能用夹具登记生产权限。

## B：已有 A2 HTTP

沿用 [A stage-api](MS-I2j-stage-api.md) 的六个本人读取/接受入口和四个 Web 身份入口，精确对象由标签内 schema/OpenAPI 生成，不新增猜测路径。B 默认 host 消费实际列表、原请求恢复和 RunDeliveryView；A2 不提供 SSE、本机目录授权或项目绑定 HTTP。

实际后台配置：`ops/browser-development.toml` + 同一文件复制到 A 私有配置，仅 A 将 agent_execution_enabled=true；数据库 URL 与 OS Credential Manager 来源由 A 保持，不能复制给 worker。三种办公工具要求管理员已登记 builtin-office-v1，默认固定 deepseek-flash。localhost 8000/5173，精确 Origin、HttpOnly cookie、内存 CSRF；只有 launch fragment 是限时一次码，不能公开到日志/PR/永久回执。

## C：已实现桥接及原资料 Reader

源码 `src/uaw/run/file_bridge.py`：

```python
@dataclass(frozen=True)
class FileDeviceRoute:
    device_ref: Ref       # kind=device，完整当前版本/摘要
    workspace_ref: Ref    # 准确 workspace pin

class FileDeviceRoutePort(Protocol):
    async def current(self, workspace: Ref, ctx: TrustedExecutionContext) -> FileDeviceRoute: ...

RegisteredFileBridge(*, commands: RunnerCommands, pipe: RunnerPipeClient | None,
    routes: FileDeviceRoutePort | None, access: ToolRecoveryAccessPort | None,
    provider_ref: Ref, provider: Principal, signatures: SignaturePort | None)
```

实现 C 的原 `ready/resolve/execute/recover`。原 call/spec/ctx 完整固定，command 的 tool_call pin 是原 ValidatedCall 摘要。预算从原 ToolLedger dispatch/reserved/dispatched 读取，禁止给原 ctx 添加预算字段。当前实际 whole/≤16384 字符及64KiB UTF-8；lines/text_span/cursor 在桥入口明确 unavailable，完整快照只从原签名 whole 回执获取。首次发送只由 C ToolInvocation 的 CAS 持有者调用 execute；已有 command 时只能 recover，缺原回执不重发。

FileDeviceRoutePort 是当前独立拥有者关系，**现在生产实现仍缺**。ToolRecoveryAccessPort 必须复查完整原用户/session、固定模型/角色/提供方和当前 native root；它是数据 Reader，不要求新执行成功，取消后是否可读按当前数据许可判断。项目绑定尚未实现，非空 project_id 保持拒绝。

C 导出资料沿原 FileReceiptStore.read_observation(action_id,ctx) / read_raw(ref,ctx)，由 owning Reader 复核来源后将实际 FileContent/准确观察 Ref 交 A。A 负责 Context recipe、正文低信任资料分区与 Artifact 引用；C 不改 Context 模块。新增资料适配签名在 M1 交接，至少包含原 FileContent、原 observation_ref，正文/位置不能另造。

## D：既有注册与本机授权 Protocol（先实现适配，不改 HTTP）

固定使用已经合入的原接口：

1. `uaw_runner.ipc.sessions.PeerRegistrationPort.current(identity: OsIdentity, *, role: str) -> RegisteredPeer`。RegisteredPeer 含完整 OS 实例、完整 owner/actor Principal、device_id、role、key_id/key_ref、pairing_ref、expires_at。
2. `uaw.shared.ports.RunnerChannelSourcePort.read(channel_ref, *, device_id) -> RunnerChannelSnapshot`。A 从独立设备登记和真实活连接读取，字段含 owner/actor/pairing/channel/key/connected/expires_at，不回显模型 body。
3. `uaw_runner.native_confirmation.NativeChallengeSourcePort.current(ticket_id: str) -> NativeChallenge`。NativeChallenge 为原 Ticket、完整 owner/actor、实际 channel_ref/OS identity/当前 expiry；原 Ticket.document 字段与签名域见固定 state.py，不自设 public pair.complete v2。
4. `uaw.workspace.ports.RunnerPrincipalMappingPort.owner(*, authenticated_principal, device_id) -> Principal`。A 已有 RegisteredRunnerPrincipalMapping，仍要求独立实际 devices/channels，不能只用 SID/PID推账号。
5. `uaw.shared.ports.RunnerRootSourcePort.current(device_id,workspace_ref,ctx) -> RunnerRootSnapshot`；D 的 NativeRootSource 与原 NativeReadAuthorization.select/bind/revoke 实现本机当前根检查，不含公开绝对路径。

D 可立即编写组合以上 ports 的 helper runtime，构造参数显式传入 registration/challenges/mapping/keys/signer/roots/authority/journal。**首次账号设备 bootstrap 来源由 A 在本轮 M1/M2 实现**；D M1 先列出准确构造/启动输出和缺依赖错误，M2 提供可被 A 来源注入的运行入口。不要为等待 A 端点停止自身装配和组件验证。

账号首次登记责任：A 经独立当前 Web 会话验证用户，以一次受保护控制挑战绑定 D 实际 OS 进程实例和双方当前 role keys；验证双方 key 持有证明，记录原 pairing_ref 与短期期限，撤销/退出/源变化重新拒绝。OS 身份、public_key、HTTP principal/path 都不是单独授权。D 仅镜像验证后的挑战和原 code/proof，显示真实 readonly 目录确认；绝对目录仅本机 LocalRoots。**此过程当前尚未实现/接受**，需要 A 源码和真实回执后才能注入生产。

现阶段不发布新公网认证或自造 pair.complete 字段；如实际 HTTP 传输必须新增 DTO，由 A 统一生成、发布固定阶段标签，D 消费阶段版。既有本机入口是内部 Python port，不声称已是公开配对协议。

## 独立验证和汇合

worker 可以用明确受控输入证明组件行为，但缺真实来源的产品入口要返回503。A 验收顺序：B 页面不依赖文件授权，先接现有 A2；C 文件资料和 D runtime 可并行；A 当前来源到达即做对应跨模块链，真人实际点击在最后独立留回执。全量只在组件/装配汇合后执行。旧1691完整回执不覆盖新代码。
