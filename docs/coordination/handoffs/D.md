# Session D：MS-R1 交接记录

日期：2026-10-07（Asia/Shanghai）。状态：组件实现与必要验证完成，待 A 审阅/合入；P1-04 未 accepted，MS-R2 未开工。

## 基线与位置

- Session / 包 / 原轮：D / MS-R1 / P1-04。
- 实际 worktree：`E:/UAW/.worktrees/runner`；实际分支：`dev/runner`。
- 首次开工真实 HEAD = `parallel-wave-1^{commit}` = `70f2fcccb88650c616920a5630d2caa45d94ad45`，工作区干净。沙箱初查 Git 不可工作树/标签返回异常，提升访问后在指定目录重新核对并取得一致真实值，再开始写入。
- 派发：读取本分支 DISPATCH 的 MS-00 / dispatch_ready=true / MS-R1 分配；不编辑 DISPATCH。没有自行创建/启动其他 session。
- schema 版本：0.1；canonical schema SHA256 `c9737069f74331ee5f519eabc1a8bf5c2527389da0e922d46ba892557b522a2c`；uv.lock SHA256 `e048aafdcfdd0949b7234a8d381fa0dd1d13450ee70f13b5e01c70b79156f9f4`。最终 canonical/package schema 一致性测试通过，公共 schema/锁/flags/Run/Model/原文与提示词未修改。
- 已批准的公共提案：无。新提案 [D-R1-001](../requests/D/R1-001-adapters-and-pairing.md) 待 A 决定，未假定获准。

## 实际提交与文件

- 实现、测试及提案提交：`d77bf3595c717c36bcd47b13a220a635134ad858`（dev/runner）。本 handoff 随后单独提交，供 A 取得实际代码 SHA，避免自引用 SHA。
- 允许范围内的改动：
  - `src/uaw/workspace/binding.py`：可信选择 port、read 根绑定、真实路径/根身份/撤销检查。
  - `src/uaw/workspace/contracts.py`：RunnerCommand / RunnerReceipt / RootSelection DTO，消费现有权威 schema。
  - `src/uaw/workspace/ports.py`：可信签名、选择、当前授权、根与 admission 仓储 ports；内部状态不对外扩展 DTO。
  - `src/uaw/workspace/repository.py`：显式 Memory 仓储与 CAS/并发去重，仅组件环境。
  - `apps/local_runner/uaw_runner/protocol.py`：admit、verify_receipt、明确不可用的 dispatch。
  - `tests/unit/runner/{__init__,conftest,test_binding,test_protocol}.py`：测试替身与协议/取消/幂等/权限/版本边界用例。
  - `tests/integration/runner/test_local_paths.py`：真实临时 Windows junction 与根替换验证。
  - `docs/coordination/requests/D/R1-001-adapters-and-pairing.md`；本 handoff。
- 无公共修改、依赖增加、数据库迁移、真实服务/IPC启动或远端推送。只在自己的分支提交。

## 公开组件接口和实际语义

- `RootBindings.bind(selection, principal_id, device_id, workspace_ref, capabilities, now) -> RootGrant`：没有本机可信消费 port 就不可用；期限、主体/设备/句柄、授权交集与真实根核对；本包只允许 read。不接收聊天路径、不自己生成 RootSelection。
- `RootBindings.check_scope(root_handle, principal_id, device_id, workspace_ref, expected_revision, relative_path) -> Path`：核对本机绑定与版本、撤销、Windows/相对路径、真实链接边界和根文件身份。仅检查路径，不打开/读文件。
- `RootBindings.revoke(root_handle, expected_revision) -> RootGrant`：内部可信适配器入口，CAS 撤销；没有绑定 HTTP/model route。
- `RunnerProtocol.admit(data: str|bytes, now) -> Admission`：严格 JSON/DTO，完整签名 port、期限、独立可信 context/原模型/预算引用、request_ref 内容、policy、实时 flag/取消/连接、租约/fence、根与 scope 交集。可检查 file.read / file.list；其他 action 依赖不可用。Admission 是内部准入状态，绝不是成功任务回执。
- `RunnerProtocol.verify_receipt(data, command) -> RunnerReceipt`：回执验签 port、原 command/原 attempt/usage/action、结果分支互斥；file.read workspace_ref/version/path 对应原命令；cancelled 须携取消 failure。消费方必须从可信原命令账本读取 command（重试仍用原执行 attempt），验证通过不表示成果验收或用户接受。
- `RunnerProtocol.dispatch(data, now)`：执行器未实现，始终以 `CapabilityUnavailable('runner.executor')` 明确失败，不伪造 usage、签名或 ok 回执。
- 完整 port 及内部参数定义见 `workspace/ports.py`；HTTP/Runner wire 不私加字段；真实签名算法与传输版本待 A ADR。

## 数据状态、CAS、取消和幂等

- Root 由本机 Workspace 授权组件保存；根句柄不复用，设备/主体/workspace 版本精确匹配。撤销先使新操作和重试失效，revocation revision 单调增加。
- admission 仓储 key 为 `(principal_id, device_id, command_id)`；锁内原子 reserve。逻辑 fingerprint 包含原参数、上下文的原模型/预算与 scope、request/policy 版本、fence、获准 root_handle 和绑定 revision；仅 retry attempt/trace/deadline/短期 signature/expiry 可变化且仍须符合当前期限闸门。
- 同逻辑命令重试返回原 attempt/状态，不产生第二次执行。参数、模型、版本或根映射变化复用 ID 冲突。当前撤销/flag/租约/取消每次仍复核；Memory 的取消 tombstone 不被重试恢复。
- Run 仍唯一拥有取消/租约与任务状态，本包不替 Run 写事件，不启动模型。Memory 状态不耐重启，不能启用真实执行。

## 三组可执行对接例子

在指定 worktree 的 .venv 中执行：

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_protocol.py -q -k list_admission_preserves_workspace_version
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_binding.py -q -k revocation_cas_and_retry
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_protocol.py -q -k "admission_retries_keep_original or command_identity_cannot_change"
```

- 成功：file.list 准入 → state=admitted（仅协议状态，不读取文件）。
- 拒绝：撤销后同命令 → permission_denied；旧 CAS revision → revision_conflict。
- 重复/冲突：新 attempt 返回原 admission；参数/request版本/模型变化但复用 command_id → revision_conflict。全部签名、选择和授权 port 为明确 TEST DOUBLE。

## 验证命令、环境与回执

- 环境：本 worktree 独立 .venv；Python 3.14.6；依赖沿用 uv.lock，无数据库，无真实 LLM/Runner。pytest tmp 根限制在本 session `tests/.artifacts/D/MS-R1/`。
- 最终验证是在实现提交前的相同代码上执行；实现提交只记录已验证文件，handoff 追加不改变代码。

```powershell
.venv/Scripts/python.exe -m ruff check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py --basetemp tests/.artifacts/D/MS-R1/tmp-final -q --junitxml tests/.artifacts/D/MS-R1/junit.xml
git diff --check
```

- 最终结果：ruff / format / mypy / diff-check 均 exit 0；pytest **60 passed，0 failed，0 skipped，无 warning**。其中47项本包用例和13项公共契约消费回归；真实 Windows junction 根内/根外、真实根替换均已运行。
- 原始本地回执（忽略文件）：`tests/.artifacts/D/MS-R1/checks.json`、`ruff.log`、`format.log`、`mypy.log`、`pytest.log`、`junit.xml`、`diff-check.log`；checks 包含真实命令/退出码/环境/锁与 schema 摘要。
- 首轮临时目录不存在、fixture Ref kind不合法、测试载荷共享引用等问题已修复；最终无待修失败。签名覆盖的 port 参数传递得到验证，密码学验签本身未验证。

## 未通过的正式验收与 A 接线要求

- 未实现/未运行：真实用户设备配对及公钥持有证明、可信 IPC、真实签名/密钥存储与撤销、持久授权与一次消费/重启幂等、真实文件读取/安装/写入/exec、OS 隔离、真实 LLM、SQL与整条链路。**P1-04 不可标 accepted；D01/D03/D06 保持未决定。**
- D-R1-001 提供 nonce/一次码和 RootSelection 的可信来源、主体/设备绑定、期限到点失效、一次消费、重试/CAS/撤销设计；当前没有可冒充真实配对的默认适配器。
- A 先批准/实现可信 ports，固定 workspace 版本到根/绑定 revision 的不可变映射，并明确 capability/flag 命名、签名序列化/版本、配对与一次消费存储、打包方式；必要公共契约/依赖/迁移只由 A 合入后发布。
- 签名/authority/native-selection 缺失必须维持不可用，Memory仓储不得接成正式执行账本。实际 IO 要在打开与使用句柄时复核路径与撤销，不能把本包 realpath 检查称为 TOCTOU 防护或 OS 隔离。
- A 在真实集成 SHA 审阅并合入本包、处理公共冲突、运行组合与整链回归；未接受与发布 MS-I2 前 D 不开始 MS-R2。交接后保持干净工作区，下一包按 A 发布基线 merge 同步，不重写已交接历史。
- 本包不自动改变已合入基线的任何入口；可由 A revert 实现提交回退组件，再处理独立公共接线。真实凭据/副作用须由其状态所有者撤销，不能靠 Git 回退伪装撤销。


# Session D：MS-R2a 交接（追加；MS-R1 历史保留）

状态：MS-R2a 组件源码及必要验证完成，待 A 审阅与合入。完整 MS-R2 未开工，P1-04 未 accepted；真实配对/IPC/文件执行仍不可用。

## 实际工作位置、同步和基线

- `E:/UAW/.worktrees/runner` / `dev/runner`。开工工作区干净，原 HEAD `300bdf530e425acf044629aee3d4b7a745eb29be`。
- 实际执行 `git fetch origin --tags`、`git merge --ff-only ms-i2a`，快进成功；核对 HEAD 和 `ms-i2a^{commit}` 均为 `ac9bf621e3caebf060300b3a628b77dee36f7ab0`。没有 reset 或重写旧历史。
- 阅读新版 Session D、DISPATCH、A 的 `MS-I2a-ports.md`，范围只为 MS-R2a。未修改其他 session、DISPATCH 或公共文件；没有自行创建其他 session。
- 实际执行 `UV_CACHE_DIR=E:/UAW/.worktrees/runner/.cache/uv` 下的 `uv sync --frozen --extra agent-engine --link-mode copy`，成功：cryptography 50.0.2、cffi 2.1.1、pycparser 3.0；editable来源为本worktree，独立 .venv / .cache，不复制 .data/凭据或改 A 缓存。
- schema仍0.1，SHA256 `e4195d1f89fb82bbc7cf5bd32e1cafdc04f44ba70a87703fc38ff65f45025b0d`；uv.lock SHA256 `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`。canonical/package一致性检查通过，公共schema/锁无改动。

## 实际提交和修改文件

- MS-R2a实现/测试/提案提交：`2049c3dac936d4df9b618ee622143524f7132eff`，实际分支 `dev/runner`，父基线 `ac9bf621e3caebf060300b3a628b77dee36f7ab0`。
- 本追加handoff随后单独提交，供A读取实际实现SHA；前一包 `d77bf35` / `300bdf5` 保留。
- 改动（均在D允许范围）：
  - `apps/local_runner/uaw_runner/__init__.py`：Runner源码包入口；没有安装/executor入口。
  - `apps/local_runner/uaw_runner/keys.py`：Ed25519SignatureAdapter、ProtectedSigner。
  - `apps/local_runner/uaw_runner/state.py`：显式开发LocalState SQLite当前公钥目录和一次ticket持久CAS。
  - `apps/local_runner/uaw_runner/pairing.py`：挑战+独立本机确认核对、native路径目录、RootSelection签字和一次消费。
  - `src/uaw/workspace/ports.py`：CurrentKeyDirectory、NativeConfirmation/Port，可信内部注入，不接受model/HTTP body构造。
  - `tests/unit/runner/test_real_keys.py`：真实密码学适配与保护凭据接口边界。
  - `tests/integration/runner/conftest.py`：只将源码Runner路径加入本包测试导入路径。
  - `tests/integration/runner/test_persistent_pairing.py`：真实SQLite/restart、多连接/多进程、证明/确认/撤销/期限与RootSelection。
  - `docs/coordination/requests/D/R2a-001-authority-ipc-dtos.md`；本handoff追加。
- 没有依赖/公共契约/生成物/迁移/flags/原文/用户模型/Run代码改动；没有启动系统服务、共享DB、真实用户项目或推送远端。

## 组件方法与接口

- `Ed25519SignatureAdapter(CurrentKeyDirectory)` 实现现有 SignaturePort：先验证Runner DTO，命令公钥由每次当前目录lookup得到，核对device/key role/revoked，消费公共真实Ed25519原语和v1签字字节。command=control；receipt/pairing-proof/root-selection=device。签字全覆盖、域区分、文字不归一化，目录不读取命令自报公钥。
- `ProtectedSigner(directory, CredentialStorePort|None)`：`provision_private(credential_handle) -> public_bytes`、`sign_document(document, device_id,key_id,domain,credential_handle) -> signature`。私钥只经受保护port取用，不回传/保存普通DTO、数据库、日志或上下文。检查匹配当前public和role/revoke，await后再查key；缺保护后端无明文fallback。已有handle拒绝覆盖；真实跨进程create-only仍待新port/单一可信发行所有者，未假称原子凭据发行。
- `LocalState(path)`：当前public-only目录 `register_key/lookup/revoke_key(expected_revision)`；ticket `issue(request_id,kind,principal,device,key,public_bytes,expires_at,now,root...)`、`get(now)`、内部 `approve(expected_revision,code,confirmation_hash/expiry,now)`、`consume(expected_revision,now)`、`revoke(expected_revision,now)`。SQLite是显式临时开发适配器，**未决定D01、未接控制面SQL或公开DTO**。
- `PairingVerifier(state,native|None,clock,roots|None).approve(...)`：固定ticket里的nonce/challenge/key/主体/device/hash/期限接受真实pairing-proof签名；独立NativeConfirmationPort必须返回同ticket/主体/device/document_hash和有效期。root额外要求可信本机path。缺IPC或签名、旧proof、错一次码、到点期限、CAS或撤销拒绝。
- `complete_legacy()` 明确不可用：旧 `RunnerPairCompleteRequest` 没内联挑战证明，不能自认已验证。
- `PairingVerifier.root_selection(ticket, ProtectedSigner,credential_handle)` 只为approved root内部签字，重新核对await期间状态；`PersistentRootSelection.consume` 实现RootSelectionPort，验当前device key/签字/完整selection身份和准确期限文字、local根身份，再持久一次consume。
- `Ticket.document()` 及当前token签字statement是**内部开发测试profile**，未当成新公共Runner DTO/网络协议发布。A必须先批准发布正式命名挑战/根证明/持久DTO和字节profile，再启用产品接线；旧pair.complete不扩字段。现有RunnerProtocol仍为同步协议，async authority只提案、未以阻塞async SQL伪接线。

## 持久所有者与CAS/取消/版本规则

- 显式control目录保存公钥/role/revoke/revision及ticket（无private/raw一次码/path）；单独native目录保存选根path与文件身份。目录来自可信组装配置，不凭模型/命令自报key建立信任；生产ACL/认证所有者仍需真实adapter。
- issuance幂等键 `(principal,device,request_id)`，稳定ticket/nonce/challenge；重试不再回传raw一次码、不换挑战、不延期，不同key/参数/根/期限 conflict。一次码256-bit随机，普通持久记录只有salted摘要，repr隐藏一次码。
- pending → approved → consumed；expired/revoked/consumed均终态。CAS核对state及revision，SQLite BEGIN IMMEDIATE跨连接/进程串行化。期限和confirmation期限任一到点即持久expired；失败重试或回退时钟不能恢复终态。
- key_id不可复用，key角色/device/public不可原地覆盖；撤钥还撤未消费tickets。消费root在同一事务再次核对当前device key。pair消费仅更新ticket，**没有设备注册/会话凭据/真实配对成功**。
- 本机root记录与control CAS不是跨库原子事务；失败只可能留无授权孤儿，consume后崩溃不能再消费。真实配对注册/根绑定journal与恢复要求见提案，A须接线后验证。
- Run取消/lease/fence、权限/flag和固定model/budget边界仍由原owner负责；本包没有真实发命令/开文件/executor。MS-R1重试/scope/取消/幂等用例继续通过，D不自行决定D01/D03/D06。

## 三组可执行对接例子

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_real_keys.py -q -k real_command_adapter
.venv/Scripts/python.exe -m pytest tests/integration/runner/test_persistent_pairing.py -q -k "missing_ipc_legacy or native_confirmation_is_exact"
.venv/Scripts/python.exe -m pytest tests/integration/runner/test_persistent_pairing.py -q -k "pairing_consume_cas_across_real_python_processes or reissue_is_idempotent"
```

- 成功：真实control密钥签字的file.read经当前目录验签准入；内部ticket在真实proof＋明确NativeFixture测试确认下approved，再单次consumed（不表示产品配对）。
- 拒绝：IPC port=None或legacy complete→capability_unavailable；错proof/主体/期限/confirmation摘要/角色/撤钥拒绝。
- 重复/冲突：同request原ticket/nonce且code=None；6实际进程同revision只一个消费，其他conflict；16连接批准/消费及撤销竞态仅一个终态胜者。

## 真实环境、验证命令和回执

本worktree独立Python 3.14.6/.venv，锁定cryptography 50.0.2；所有数据库/根/链接/测试文件均在 `tests/.artifacts/D/MS-R2a/` 的独立tmp目录。没有OS Credential Manager写入或真实IPC/用户项目。

```powershell
.venv/Scripts/python.exe -m ruff check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py --basetemp tests/.artifacts/D/MS-R2a/tmp-final -q --junitxml tests/.artifacts/D/MS-R2a/junit.xml
git diff --check
```

- 最终：**100 passed，0 failed/error/skip，无warning**；其中72项D组件/真实本机临时持久用例，13项shared契约与15项公共签字原语回归。Ruff/format/mypy/diff-check均exit0；Mypy9源码文件。
- 实际验证：真实Ed25519（新建key、命令篡改、错误device/key/role/domain、实时撤钥重启、保护port签字）、真实SQLite持久重启/幂等/CAS/一次码摘要、16连接并发、6独立Python进程一次consume、确认/根token/过期/撤销，以及原真实临时junction/根替换用例。
- 本地忽略回执：`tests/.artifacts/D/MS-R2a/{checks.json,ruff.log,format.log,mypy.log,pytest.log,junit.xml,diff-check.log}`，checks含真实命令/退出码、基线、环境、schema/锁摘要。代码验证后只提交源码与文档；测试输出不进入Git。
- 曾遇到测试新导入/单独Runner测试导入路径与格式问题，已修复；当前无未通过组件检查。
- NativeFixture与CredentialFixture为**明确TEST adapter**，无布尔量替代密码学证明。真实设备proof密码学成立也不证明用户确认/IPC身份；测试不冒充真实用户配对/OS凭据实连/LLM或执行。

## 未满足项与A接线要求

- [D-R2a-001](../requests/D/R2a-001-authority-ipc-dtos.md)：async authority结果参数、当前key async reader、可信IPC确认、公钥持有/new证明DTO、持久DTO/SQL聚合与注册/选根journal、private create-only/保护后端的最小公共提案；待A决定和发布，D未假定获准。
- 未运行/未通过正式验收：真实本机用户/账户确认、可信IPC/peer身份、公钥登记来源和OS目录ACL、OS凭据实连、控制面真实SQL/持久DTO/迁移、真实配对注册与凭据发行、async当前Run authority/lease/fence/取消/权限汇合、文件句柄使用时复核/TOCTOU、隔离/安装/write/exec、真实LLM。P1-04不能accepted，完整MS-R2未开始。
- A先发布新命名挑战证明/根签字statement/持久DTO，禁止把新字段偷偷加进旧pair.complete；私钥原语与role沿用已发布公共版本。flags保持关闭，没有可信确认或持钥证明就不批准。
- 真实签字adapter需要current目录适配器及受保护CredentialStore组装；临时SQLite不是部署选择，Memory与fixture不能注册成真实用户能力。A接async authority不能阻塞async SQL或用缓存当当前授权。
- A审阅并合入本包，再在集成SHA做组合/整链验收；D只提交自有文件，不处理公共冲突或自行进入后续包。下一包工作区干净后按A发布基线同步，不重写本包历史。
- 回退由A移除新公共接线并保持flags禁用，再revert `2049c3d`；凭据/外部效果另由owner撤销，Git回退不能代替。
