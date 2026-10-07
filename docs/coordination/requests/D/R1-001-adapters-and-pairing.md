# D-R1-001：真实 Runner 适配器与公共接线提案

- Session / 包：D / MS-R1（对应 P1-04 的协议组件子包）。
- 基线：`70f2fcccb88650c616920a5630d2caa45d94ad45`，固定 `parallel-wave-1`。
- 状态：待 A 决定、合入并发布新基线；本文不批准依赖、签名算法、D01/D03/D06或权限。

## 已有契约能完成什么

`workspace/contracts.py` 的 RunnerCommand / RunnerReceipt / RootSelection 严格消费现有 0.1 schema，不新增 wire 字段。`workspace/ports.py` 的 dataclass 是可信适配器间的内部状态，不是第二套 HTTP/Runner DTO。当前 only admission，无真实配对、签名、IPC、读文件、写入、安装、exec、OS 隔离。Memory 仓储只有进程寿命，不能作为持久执行账本。

## A 需要修改或分配的公共文件

- `composition.py` / `application.py` / API 路由：在真实适配器就绪后注入 D 的 ports；当前不注册对外成功入口、不启用 flags。
- `shared/` / `run/` 的公开适配器：提供当前主体、完整可信上下文、固定 request_ref 内容、当前租约/fencing、取消、固定模型/预算引用、固定与当前 policy/flag 的有效交集。只能消费已合入基线，D 不读取 B/C 未交接实现。
- `contracts/interface_catalog.py`、生成 schema/API、实现清单：确认下面的最小契约澄清；生成只由 A 执行。
- 持久仓储/迁移、依赖锁、Runner 打包入口：由 A 在 D01/签名决策后统一处理。`apps/local_runner` 当前未进入 pyproject wheel；测试临时添加该目录到 sys.path，不能把测试可 import 当成安装完成。

## 最小变更与消费方影响

1. **签名与版本规则（ADR + port adapter）**：确认命令/回执签名序列化、域分离、0.1 协议版本协商、会话密钥/设备密钥用途、轮换与撤销。必须覆盖全部嵌套参数/context/Ref/期限/fence，不能只签 command_id。SignaturePort 收到保持省略语义的完整 DTO；内部幂等 SHA256 只作比较，不是签名算法。当前不选算法、不引入包。消费方：服务签发器、IPC、Runner、回执消费者；现有 DTO 字段不变。
2. **RootSelection 原子消费 port**：只有认证本机用户 UI/可信 IPC 产生证明。对 `(selection_token, principal, device, root_handle, capabilities, expires_at)` 验签并检查来源，消费一次且与根绑定原子落账。明文 native_path 只存在 Runner 本地仓储。当前 MemoryRootRepository 与 SelectionDouble 不提供生产级跨存储原子性。消费方：Workspace bind、本机选择器；失效/重复为拒绝，期限到点即失效，无默认 TTL。
3. **Workspace 与本机根映射**：当前 schema 没有可公开消费的绑定修订对象。优先由 A 提供 AuthorityPort 适配器，用已固定 workspace_ref.version 解析不可变的 `(device_id, root_handle, binding_revision)`；改根/能力需新 workspace 版本，旧版本不得指向新根。若需要公开返回绑定，新增 RootBinding 最小字段建议 `workspace_ref:Ref, device_id:ID, root_handle:ID, revision:Revision, capabilities:array[ID], revoked:Bool`（全部必填；不包含 native_path），作为新命名对象，旧 DTO 不私加字段。D 当前不依赖该未批准 schema。
4. **RunnerReceipt 分支互斥**：在现有 RunnerReceipt schema 的条件分支增加禁止另外两个结果字段：ok 仅 payload，waiting 仅 wait_ref，failed/cancelled 仅 failure；usage.attempt_id 对应原执行 attempt；cancelled.failure.category=cancelled。D 的消费者已做这些语义拒绝，无新 wire 字段；A 可将规则统一到 schema。消费方：所有回执签发者/消费者；混合分支旧样例应拒绝，合法现有样例不变。
5. **能力标签和 current authority port**：由 A 明确动作到现有 capability/flag 的映射，返回 `required_scope_capability` 与 `allowed_actions`，本地 root 只允许 read，scope 必须含固定 workspace Ref。测试标签 fixture_read 不作为公共名称。CommandAuthority.context 必须独立从 Run/认证状态重建，包含原模型/预算/agent/node/scope 等引用，不得直接复制未验证命令 context。调用和重试均重查；lease/fence 必须关联相同 Run/node。

以上除可选新增 RootBinding 外，均可通过文档规则与真实适配器完成，不需要改变 RunnerCommand 0.1 字段。任何新算法依赖和迁移先由 A 提供真实提交，再由 D 同步；不能在本分支私改锁文件。

## 配对 nonce / 一次码设计（未实现）

- 本机可信入口生成高熵 device_nonce；用户账户页面完成认证和明确设备确认。聊天文本、模型参数、code 知识本身均不授予授权。
- 配对状态所有者维护 pending → approved → consumed / expired / revoked。关联 nonce、pairing_id、设备公钥摘要、认证 principal、原请求摘要、期限、状态修订；一次码仅保存验证摘要，绝不进入模型/诊断。
- `pair.begin` 同 nonce 同参数返回同一 pending 事务；不同参数 conflict。重试不延长期限、不换一次码。TTL、尝试上限、退避来自确认配置，D 不设默认值。
- `pair.complete` 必须核对账户 approval、设备 nonce、公钥持有证明与期限；仅提交公钥不能证明持有私钥。可通过可信 IPC challenge port 补足证明；若走网络需要新增 proof/challenge 字段，由 A 先发布新协议版本，不能在 0.1 偷加字段。
- 通过 CAS 一次消费；并发仅一个成功。相同逻辑请求的完成重试可返回原设备注册结果，但不能再次生成凭据；更换主体/设备/key/nonce conflict。取消或撤销使未消费事务失效，已发生外部效果不伪装撤销。
- RootSelection 与设备配对是不同的一次凭据；配对不隐含项目读权，选择根不隐含 write/exec/install。原子持久化位置和恢复方式待 D01/部署方案。

## 对接示例与错误语义

可执行 fixture 见 D 的 tests（全部签名/配对适配器为 TEST DOUBLE）：

- 成功校验：`RunnerProtocol.admit(file.read)` → `Admission(state='admitted', command_id='cmd1', attempt_id='a1')`；这不生成 RunnerReceipt，不读取文件，不表示任务完成。
- 失效：撤销 r1 后同一命令 → DomainError `permission_denied` / authorization；当前 feature 关闭 → `feature_disabled`；缺 signature/authority/executor → `capability_unavailable` / dependency，HTTP 503 由公共层映射。
- 重试：同 command_id 仅换 attempt/trace/短期签名/期限 → 原 admission；主体/模型/request版本/参数/授权根映射/fence 改变 → `revision_conflict` 或当前授权拒绝。再次执行不得使用返回的 admission 直接跳过闸门。
- 回执：核对原 command/原 attempt/action/usage；file.read 的 workspace_ref/version/path 必须匹配。验证回执签名只证明协议身份，不证明成果质量或用户接受。

## 权限、取消、CAS、路径与恢复边界

- 所有 port 仅可信 composition 注入；禁止由 model/HTTP body 填内部 dataclass，RootBindings.bind 不接受聊天路径。
- MemoryAdmissionRepository 按 `(principal, device, command_id)` 原子去重；RootRepository 按 root_handle 保存不可复用句柄并 CAS 撤销。正式仓储须保持 tombstone、原命令/回执、状态修订，重启不得丢去重后盲重试。
- 本包解析真实路径、Windows junction、根文件身份；不声明抵抗检查后链接替换的 OS 保证。实际 IO 必须取得目录/文件句柄并在使用时复核授权与 final path；检查和打开间的 TOCTOU 需 MS-R2 可信执行器处理。
- 原文不重写；完整固定 model_policy_ref 和 budget_ref 参与上下文比对及命令身份，不选/切模型。所有执行类动作在本包返回不可用。
- 必要验证：真实签名篡改/旧密钥、可信 IPC 来源、认证账户 approval、公钥持有、并发一次消费、重启幂等与取消、固定/当前 flag、旧 workspace 映射、实际 IO 句柄路径与撤销。A 在集成 SHA 运行整条链路；本包替身测试不能代替。
- 回退：移除 composition 的新接线且 flags 保持关闭；由 A revert 相应公共提交。凭据撤销与已发生效果另由状态所有者处理，不能靠源码 revert 撤销。

## A：决定和发布

待 A 填写采用/调整/暂缓结论、真实公共提交 SHA、生成物和依赖锁回执、必须同步 session 与新基线。D 未假定本提案获准。
