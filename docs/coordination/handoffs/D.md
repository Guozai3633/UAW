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


# Session D：MS-R2b 交接（2026-10-08，追加保留历史）

状态：异步协议消费组件与必要验证完成，待A审阅合入。完整MS-R2继续等待；未挂载生产authority/映射/可信IPC，不开放实际执行。

## 真实位置与同步

- worktree `E:/UAW/.worktrees/runner`；分支 `dev/runner`。开工工作区干净，原HEAD `45e0f56cd15ff6fe13434cb6290267e422714bea`。
- 已执行 `git fetch origin --tags`、`git merge --ff-only ms-i2c`；快进成功，核对HEAD与 `ms-i2c^{commit}` 均为 `1411f6aa477b0d000bee871c0f324fbfd67b4ff5`。无reset/旧历史重写。
- 已读DISPATCH、Session D、新 `requests/A/MS-I2c-ports.md`，仅消费发布基线；不读取其他worker未交接源码，不写其他session/统一派发表，不创建session。
- 本worktree独立 `.cache/uv` 下 `uv sync --frozen --extra agent-engine --link-mode copy` 成功（91 packages检查），锁未修改；Python3.14.6，沿用cryptography50.0.2和独立.venv，没有复制私有配置/.data/凭据或使用A缓存。
- schema0.1 SHA256 `b5d7cdf9df23002e6e3d3965741cbcd82b7efa34ff438b09b236e3b0b886d583`；shared ports SHA256 `cce4db2349b92a6a2fca815917725cb7bb51fcb5ab9db86c2f456d3df2b679cd`；uv.lock SHA256 `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`。最终canonical/package schema一致且公共摘要未漂移。

## 实现提交与文件

- 实际实现/测试/提案提交：`5b9724730eb1d19a244a43305d364c7318f4b5eb` / `dev/runner`，父基线为上述ms-i2c。此handoff随后单独提交，避免自引用SHA。
- 允许范围内的改动：
  - `src/uaw/workspace/contracts.py`：严格RunnerAuthoritySnapshot wrapper，现有权威schema，15字段全部必填。
  - `src/uaw/workspace/ports.py`：独立可信设备/通道归属port与带锁内guard的admission仓储port。
  - `src/uaw/workspace/repository.py`：MemoryAdmissionRepository新增guarded CAS，旧reserve兼容。
  - `apps/local_runner/uaw_runner/protocol.py`：可选异步依赖/可信clock，新增admit_async，旧同步admit/dispatch/回执兼容。
  - `apps/local_runner/uaw_runner/async_admission.py`：公开async authority消费、完整声明比较、关键检查后再查询、时钟/取消与off-loop本机复核。
  - `apps/local_runner/uaw_runner/admissions.py`：显式临时SQLite持久admission去重/CAS/取消tombstone。
  - `tests/unit/runner/test_async_admission.py`：70项新增异步组件用例，全部使用真实Ed25519/临时key目录，authority/mapping明示组件来源。
  - `docs/coordination/requests/D/R2b-001-async-wiring.md`；本handoff追加。
- 无公共schema/ports/依赖锁/生成物/数据库迁移/flags/模型/原文/提示词/组装根/API修改。没有安装系统环境、启动服务或读写真实用户项目，无远端推送。

## 公开组件接口与实际边界

- `RunnerAuthoritySnapshot(ContractModel)`消费公共严格JSON schema：context、device_id、root_handle、workspace_ref、binding_revision、fencing_token、lease_expires_at、request_ref、request_parameters、policy_ref、required_scope_capability、allowed_actions、feature_enabled、connected、cancelled全部必填，严格类型/Ref/期限/RunnerParameters分支，extra/null/defaultgrant不接受。
- `RunnerProtocol(..., async_authority=None, principal_mapping=None, clock=None).admit_async(data, *, authenticated_principal:Principal)->Admission`；clock默认UTC实际时间，仅组装根可注入。缺async authority/mapping/signature/guardedCAS明确不可用，不回退同步authority。
- 认证Principal来自可信通道adapter，不能从command构造。`RunnerPrincipalMappingPort.owner(*,authenticated_principal,device_id)->Principal`必须真实查设备/用户/认证session关系，缺登记不可用；user必须实际拥有设备，runner关系由可信adapter验证，admin/service不默认取得项目读权。D没有生产关系reader，只检查内部port结果与声明。
- 调用共享 `AsyncRunnerAuthorityPort.current(command.wire(), *, authenticated_principal)`，与独立owner比较；返回wrapper严格验证。全部context字段与本次command精确匹配，包括principal/session、scope、operation/attempt/trace、deadline、Run/agent/node、原model/budget/policy引用。request/parameters/policy/fence与签字声明比较；workspace固定版本/scope能力/current actions/flags/connection/cancel核对，root/revision通过当前本机绑定。
- 流程：owner→current1→真实签名/key/root外部检查→owner2→current2→整个snapshot精确比较→线程再次查当前签名key/root并检查时钟→锁内期限/取消guard→admission CAS→await返回后clock检查。每次await后重取clock；重放也重新查询，未缓存许可。
- key/path/SQLite等同步阻塞操作通过 `asyncio.to_thread` 移出事件循环；没有asyncio.run桥接。CancelledError直接传播，取消Event阻止尚未写入的CAS；不把协作取消变成普通成功/失败包。
- 旧 `admit(data,now)` 行为保留；同步入口仍是原组件边界。现有SignaturePort继续真实Ed25519，pairing/RootSelection流程未重新解释。本轮没有dispatch_async/executor、文件读取或网络入口。

## 持久所有者、CAS、幂等与竞态

- PersistentAdmissions只是显式临时开发SQLite记录，不决定D01、不冒充控制面持久DTO/正式SQL。键 `(principal_id,device_id,command_id)`，字段attempt_id/fingerprint/state/revision；没有private/path/rawcode。
- fingerprint沿用原规则，含真实参数、原context模型/预算/政策/scope及fence/root/revision；逻辑重复返回原attempt/state，改参数同ID冲突。原admitted记录cancel(expected_revision)后保留tombstone，重启/重放不恢复；Run仍拥有真正取消/租约/任务状态。
- `reserve_checked(...,check)`在仓储锁/SQLite事务取得后执行clock/cancel guard，重放同样检查。SQLite插入后再guard，异常回滚。锁等待期间过期不会用await前的旧期限准入。
- 如果CAS已真实提交、协程返回前才发生期限/取消变化，保留原记录并返回失败/取消；不能说记录没发生，更不能把它当执行/签字成功receipt。
- 两次权威查询、本机复核、本地CAS不是跨域原子授权。最终snapshot之后权限/映射/flag/key/root仍可能变化，执行前必须A的租约/fence/动作消费与当前撤销协调；admission不能缓存作执行许可。本包不声明消除文件TOCTOU、跨服务竞态或OS隔离。

## 三组可执行对接示例

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_async_admission.py -q -k real_signed_async_admission
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_async_admission.py -q -k "wrong_authenticated_channel or missing_async_dependencies or changes_during_await"
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_async_admission.py -q -k persistent_concurrent_restart
```

- 成功：真实control Ed25519命令＋明示组件登记关系/authority＋临时read根→Admission(admitted)，没有文件IO或执行。
- 拒绝：错通道session/user、scope/上下文/model/version变化、flag/取消/lease/fence失效拒绝；缺生产authority/映射或未接可信通道不挂载产品入口。
- 重复/冲突：16并发相同cmd得到同一持久record；重新打开仓储后仍原attempt；取消tombstone保留；已签新参数复用原cmd冲突。不是第二次dispatch。

## 实际验证和回执

环境：本worktree独立.venv / Python3.14.6，全部临时根、key目录和SQLite在 `tests/.artifacts/D/MS-R2b/`。未运行共享数据库、OS密钥库或真实IPC/用户配对/LLM/项目任务。

```powershell
.venv/Scripts/python.exe -m ruff check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py --basetemp tests/.artifacts/D/MS-R2b/tmp-final -q --junitxml tests/.artifacts/D/MS-R2b/junit.xml
git diff --check
```

- 最终：**172 passed，0 failed/error/skip，无warning**；Ruff/format/mypy/diff-check均exit0，20文件格式检查、11源码Mypy。新增70项异步用例与旧同步/真实签字/跨进程ticket消费/本机路径/公共契约必要回归。
- 实际新验证：公开DTO15字段缺失及严格bool/null/time/extra、完整context声明、独立user/runner通道/关系、异步各阶段到点、第二份authority变化/key/root撤销、真实签字篡改、当前取消、等待authority/阻塞local check/排队CAS的协作取消、事件循环仍能响应、真实SQLite锁竞争clock复核、16并发及重启/冲突/取消重放、CAS后过期记录如实保留。
- 原始忽略回执：`tests/.artifacts/D/MS-R2b/{checks.json,ruff.log,format.log,mypy.log,pytest.log,junit.xml,diff-check.log}`，含命令/退出码、基线、环境、公共hash。验证后代码不再改动；提交只记录已验证代码和文档。
- ComponentAuthority/ComponentMapping是明确组件记录来源，忽略传入命令重建自己的fixture记录，**不是生产SQL/权限/IPC服务**；全部异步命令真实Ed25519。既有MS-R2a NativeFixture/CredentialFixture仍是替身，不冒充真实用户确认或OS保护后端实连。
- 初版格式检查提示已修复；当前无未通过组件检查。

## 未满足项、A接线与范围终止

- [D-R2b-001](../requests/D/R2b-001-async-wiring.md)列出了真实认证通道、当前设备/用户映射、生产AsyncRunnerAuthorityPort、current key/root、guarded持久admission和执行前跨域协调。A处理共享导出/组装/API/迁移/目录ACL，发布版本后D才消费；不假定这些reader已经实现。
- 没有可信生产IPC/关系/authority就不可用，不挂网络入口，不从command的principal或公钥自证；不使用缓存authority或asyncio.run桥接。真实SQL控制面/OS凭据库/配对/租约与执行协调尚未实连或验收。
- 不发布pairing V2，不改变或重解释内部Ticket.document的签字profile为公开协议；旧pair.complete仍不具挑战证明。D01/D03/D06不决定，flags保持关闭，不安装/写文件/exec，不标P1-04 accepted，**完整MS-R2继续等待**。
- A审阅合入并在实际集成SHA执行组合/整链回归；本包只交自有提交。下一包按A新固定基线在干净目录同步，不重写交接提交。
- 回退由A保持flags关闭、移除接线并revert实现提交 `5b97247`；凭据/已发生外部效果由owner处理，Git回退不能代替撤销。


## MS-R2c：签名终态回执持久 journal（2026-10-08）

- 实际目录 / 分支：`E:/UAW/.worktrees/runner` / `dev/runner`。
- 开工 HEAD：`76fbb36e4b2a283e928822700eb6740ee9a660a4`，工作区干净；`git fetch origin --tags` 和 `git merge --ff-only ms-i2e` 成功。
- 实际固定基线：`ms-i2e` / **ba2f3b0d9417e6d695eaa74c2f766217c98b01f1**，同步后 HEAD 与 `ms-i2e^{commit}` 完全一致。
- 环境：本目录 `.venv` Python 3.14.6；`UV_CACHE_DIR=E:/UAW/.worktrees/runner/.cache/uv`，`uv sync --frozen --extra agent-engine --link-mode copy` 成功，91 packages checked，锁未修改。
- 源码/测试/接线提案提交：**38ee8099129fd54571435faaeb8bd0b4f339a17c**。本节 handoff 单独提交，最终 SHA 由本分支 Git 历史及交付消息给出；不改写源码提交。
- 范围只到 MS-R2c 组件交付；**完整 MS-R2 / P1-04 未验收**，待 A 审阅、合入和组合回归。

### 实际修改文件

1. `apps/local_runner/uaw_runner/receipts.py`：可选 Reader 的异步 publish/read、开发 SQLite 唯一终态 CAS、原始数据保存与固定 Ref、当前源/key 复查、错误/中断/取消边界。
2. `src/uaw/workspace/contracts.py`：仅添加内部 frozen `RegisteredReceiptCommand(command, device_id, owner)`，没有公开 wire 扩展。
3. `src/uaw/workspace/ports.py`：添加 A 第4节批准的内部 `ReceiptCommandReaderPort`。
4. `tests/unit/runner/test_receipts.py`：73 项真实签名/SQLite 组件检查，独立受控登记源明确标识。
5. `tests/integration/runner/receipt_child.py`：独立测试进程，从单独受控 registry 读取实际 fixture 登记源，仅持公钥/已签数据。
6. `tests/integration/runner/test_receipt_journal_processes.py`：5 项实际进程并发/冲突/重建/撤销验证。
7. `docs/coordination/requests/D/R2c-001-journal-wiring.md`：Reader、持久化和 Ref 缺口；成功、默认失败、重复和冲突接线例子。
8. `docs/coordination/handoffs/D.md`：本节（单独提交）。

没有修改 shared/schema/锁/composition/API、授权根、flags、其他 worktree，未使用其他 worker 未交接源码。

### 内部公开消费接口与实际语义

```python
ReceiptCommandReaderPort.resolve(command_ref: Ref, *, authenticated_principal: Principal)
    -> RegisteredReceiptCommand
ReceiptJournal(path: Path, *, protocol: RunnerProtocol, reader: ReceiptCommandReaderPort | None = None)
ReceiptJournal.publish(command_ref: Ref, receipt_data: str | bytes, *, authenticated_principal: Principal)
    -> Ref
ReceiptJournal.read(receipt_ref: Ref, *, authenticated_principal: Principal) -> RunnerReceipt
```

认证主体仅由可信适配器传入。Reader 从独立登记源校验实际固定 command/device/user-owner 与当下通道/恢复数据权限；Journal 比较完整 owner、device 和固定命令摘要，并在关键外部校验/await 后重读源。缺 Reader 默认 unavailable 且不触碰 SQLite；缺签名 verifier、错误角色/域/device、当前key或来源撤销均拒绝。
复用 `RunnerProtocol.verify_receipt` 和真实 Ed25519 receipt domain；command_id、原 attempt、usage.attempt_id、action、既有 file.read 资源/版本/path 核对保留。仅 ok/failed/cancelled，waiting 明确 unavailable，不改既有协议方法。
开发 SQLite 按 owner kind/id、device、command、attempt 唯一，revision=1。同一已验证内容返回实际原 Ref，JSON 排版不影响去重；不同内容冲突、不覆盖历史，完整首个 JSON 原文和 Usage 保留。数据库不保存命令全文、私钥或认证凭据；完整 owner 仅存必要摘要与 kind/id 索引。
恢复不调用 admission、dispatch、reserve 或 executor，不要求历史执行期限/flag/lease 仍可新执行；取消/过期后的原回执可在当前数据和key权限有效时读取。不从 ok 推出 Tool applied，也不从 failed/cancelled 推出 not_applied/零费用。

**Ref 接线缺口：** ms-i2e 的 RefKind 没有 runner_receipt/runner_command。本组件用合法 `artifact` 容器及 `runner_receipt-<唯一身份SHA256>` ID 返回确实保存的 Ref，version="1"、content_hash 为完整 RunnerReceipt wire（含原签名）的 canonical JSON SHA256；不是非法新 kind。A须确认该封装用于生产，或先发布 RefKind 新值/摘要约定再交 D 消费；详见 R2c-001。command Ref 同样要求完整固定 wire 摘要，whole Ref 不带 location/access_scope，读取精确比较实际全部 Ref。

### 实际验证命令与回执

在 `E:/UAW/.worktrees/runner` 本目录实跑：

```powershell
.venv/Scripts/python.exe -m ruff check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py --basetemp tests/.artifacts/D/MS-R2c/tmp-final -q --junitxml tests/.artifacts/D/MS-R2c/junit.xml
git diff --check
```

结果：**250 passed，0 failure/error/skip，23.60s**；本包新增 **78**（73 unit＋5实际进程）。Ruff通过、格式24文件通过、Mypy12源码文件通过、diff检查通过，所有 exit_code=0。
真实验证包括 Ed25519 篡改/错误域/当前 device 角色/撤销、跨 owner/device/attempt、Usage/action/资源绑定、固定 Ref/摘要、同 Ref 变更、16并发实例、6个并发Python进程唯一提交、新进程恢复和冲突唯一赢家、当前来源/通道撤销、取消后恢复、实际SQLite锁下及时取消，以及插入后中断回滚/提交后拒绝返回但保留事实。
回执：`tests/.artifacts/D/MS-R2c/checks.json`、`static-checks.json`、`pytest-check.json`、`public-hashes.json`、`ruff.log`、`format.log`、`mypy.log`、`diff.log`、`pytest.log`、`junit.xml`。全部为本session忽略文件，临时SQLite仅在本session basetemp下。
开发首轮 fixture 缺必需 currency、basetemp父目录和计数检查曾失败，已修复；上述250项为修复后的实际最终回执。无最终失败/跳过项，没有实际 PostgreSQL 或生产 Reader/IPC 验收。

公共字节核对与 ms-i2e 完全一致：schema及资源副本 `45161b36f2e81622e73f86c23b048cda8d55686e7045248f0394ab51d13dbe6b`；shared ports `453cd9cd21b92a77c6e370fc6f0463072a3903a2c6b5beee56dec4f93b0c27a5`；shared contracts `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b`；uv.lock `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`；composition `816352f89dc15eb4fea88555b039d448f62c40cf084e3ba1bfc8055022f30bc4`。

### 故障、未满足项与 A 接线要求

- SQLite显式配置为开发组件 journal，构造无DB IO；异步服务将SQLite/当前key/验签移至线程，没有生产 asyncio.run 桥接。BEGIN IMMEDIATE、唯一键与最后验签/取消 guard 控制本地CAS；busy/IO/DB错误为 unavailable，不退回内存或假回执。
- 提交前异常关闭事务回滚；提交后取消/访问撤销保留真实记录但不给调用者旧权限。线程无法撤回已完成 commit，重试须复查当前源/key再去重。不宣称断电/磁盘损坏测试或跨服务原子撤销。
- A提供真实登记命令 Reader、可信通道及device-owner映射、当前device key目录、命令/回执固定 Ref 约定、生产私有目录ACL/保留/备份与持久化策略。journal与SQLite key目录使用独立文件，不复制其他session配置/凭据。SQLite不决定D01。
- Reader/key目录/journal不是共同事务；提交后的来源复查只能拒绝返回，不能证明整条执行链原子性。根ExecutionLease不是执行权限，journal不借它签发实际操作回执或新attempt。
- file.list的既有FilePage缺workspace/path签字字段，保持原verify_receipt边界，不从snapshot_revision推断资源；需要更强证明由A发布新版本。
- 接线成功/缺Reader拒绝/重复/冲突代码例子见 [R2c-001](../requests/D/R2c-001-journal-wiring.md)。生产Reader未提供，未挂载网络/API/IPC，也未接配对V2或真实OS凭据；测试签名均为受控协议fixture，不是真实Runner执行回执。
- 完整MS-R2、D01/D03/D06仍等待；没有安装、项目写入/exec、Tool outcome映射或flags开放。A负责审阅、合入、公共冲突和整链回归；本分支只提交D改动，不创建其他session。


## MS-R2d阶段版：里程碑1/2（2026-10-08）

- 实际目录/分支：E:/UAW/.worktrees/runner / dev/runner；开工干净，fetch tags与ff-only成功。
- 固定基线：ms-i2g-start / `0bd8e2b8387a46e16435dc033956c2b69bb1a859`，同步后HEAD精确一致；`uv sync --frozen`通过，锁未改，独立环境Python3.14.6。
- 阶段源码SHA：**92ddf118cf3005bfe32eea630ce950c6325bd76d**。本阶段handoff单独提交，不自动结束本包；继续里程碑3/4。
- 文件：control_signing.py、keys.py、test_control_signing.py、test_windows_control_keys.py、requests/D/R2d-001-adapter-wiring.md；全在D允许目录。
- 接口：`ControlKeyBinding(device_id,key_id,credential_handle)`；`ControlCommandSigner(bindings, *, directory, signer, clock=None)`；实现共享 `sign(draft, *, device_id)->RunnerCommand wire` / `verify(command, *, device_id)->None`。
- 独立构造固定control key/device/handle；只加signature，不改draft正文；当前key、control角色、撤销、deadline与await后的时钟再查，取消传播。ProtectedSigner深拷贝document，当前目录IO off-loop；无OS回退。恢复verify不以历史deadline拒绝，不授予admission/dispatch。
- 实际回执：27 passed，0 failure/error/skip，1.85s；Ruff/格式27文件与Mypy13源码文件通过。命令/构造例子见[R2d-001](../requests/D/R2d-001-adapter-wiring.md)，JUnit在tests/.artifacts/D/MS-R2d/stage-junit.xml。
- **真实OS用例1项通过**：WindowsCredentialStore直接WinVaultKeyring后端；随机namespace/handle生成、读取、签名、重建、再签、当前撤销，finally清理并证明missing，windows-control-receipt.json为passed/cleaned=true；没有输出secret或触碰既有凭据。其余原语+memoryvault测试明确fixture。
- 仍缺：生产control绑定生命周期/可信channel/native确认与正式OS部署；前两项不是完整MS-R2或实际Runner执行。未启动PG（本阶段不需要SQL），不实现IPC/配对V2/安装写入exec，不决定D03。


## MS-R2d最终交接：OS控制签名、授权根来源与装配（2026-10-08）

- 实际目录/分支：**E:/UAW/.worktrees/runner / dev/runner**；保持原worktree、原提交和旧handoff，不创建其他session。
- 实际固定基线：**ms-i2g-start / 0bd8e2b8387a46e16435dc033956c2b69bb1a859**；开工干净，fetch tags / merge --ff-only成功，HEAD与标签commit精确相同。
- 环境：独立`.venv` Python3.14.6，`UV_CACHE_DIR=E:/UAW/.worktrees/runner/.cache/uv`；`uv sync --frozen`成功，未改锁。按指令未选择agent-engine extra，移除了本工作区27个可选包；没有其他worktree环境变更。
- 阶段源码SHA：**92ddf118cf3005bfe32eea630ce950c6325bd76d**；阶段handoff：**1287a053da9e3963703091ccbfc9ff0f032c8dc1**。前两里程碑先交可审阅接口/OS回执后，连续完成后两里程碑，没有等待最终接受。
- 最终后半包源码SHA：**7d946de7a8aa2321e32ee1af5bdb18610a09ead1**。本节handoff独立提交；最终交接SHA由随后Git历史和交付消息给出，避免自引用改写源码提交。
- 本包四项组件目标完成，待A审阅/接线/接受；**完整MS-R2、P1-04及可信IPC/真实用户确认/实际文件执行仍未验收**。

### 实际文件清单

阶段源码5文件：`apps/local_runner/uaw_runner/control_signing.py`、`keys.py`；`tests/unit/runner/test_control_signing.py`；`tests/integration/runner/test_windows_control_keys.py`；`docs/coordination/requests/D/R2d-001-adapter-wiring.md`。
后半包12文件：`apps/local_runner/uaw_runner/assembly.py`、`root_source.py`、`async_admission.py`、`protocol.py`、`pairing.py`、`state.py`；`src/uaw/workspace/binding.py`、`ports.py`；`tests/unit/runner/test_async_admission.py`；`tests/integration/runner/test_native_root_source.py`、`root_source_child.py`；同一R2d-001接线文档。本handoff单独提交。
所有改动在D允许目录；shared/schema/锁/composition/API/公共迁移/其他worktree均未修改，不读取其他worker未交接代码。未启动PG：本包仅本机OS/SQLite/路径后端测试，不需要平台SQL，未宣称真实PostgreSQL接线验证。

### 可消费接口与构造样例

```python
ControlKeyBinding(device_id, key_id, credential_handle)
ControlCommandSigner(bindings, *, directory, signer, clock=None)
await signer.sign(draft, *, device_id) -> JsonObject  # RunnerCommand
await signer.verify(command, *, device_id) -> None
PersistentRootGrants(path)  # RootRepository + RootGrantLookup
NativeRootSource(bindings, *, grants, selections, native_roots, mapping,
                 directory=None, clock=None)
await roots.current(device_id, workspace_ref, ctx) -> JsonObject  # RunnerRootSnapshot
await roots.bind(selection, workspace_ref, *, device_id, authenticated_principal) -> None
RegisteredPrincipalMapping(devices)  # adapts RunnerDevices.owner(actor, device_id)
assemble_runner_adapters(*, device_id, control_bindings, directory, credentials,
    grants, admissions, selections, native_roots, mapping, authority,
    receipt_commands, journal_path, clock=None) -> RunnerAdapters
```

- control key→device→protected_handle仅由独立可信构造映射固定。严格RunnerCommandDraft，只新增signature、深拷贝且不改正文；当前key/control角色/撤销/实际Ed25519验签/异步OS读取后时钟与期限复查。取消传播；verify可恢复历史签名而不新准入。ProtectedSigner复制document并off-loop查key，无明文fallback。
- 根来源按独立owner/session与实际device映射找完整固定workspace的唯一持久grant；消费前检查独立当前device key。授权元数据来自真实已消费票据/确认hash/原root-selection域签名和有限期限、持久grant、真实dev/inode/native目录；签名/目录/映射/撤销查询后重查。旧缺owner/证明/有效期记录明确拒绝，无无限期限补值。
- Snapshot严格只含发布的owner/device/workspace/root_handle/revision/allowed_actions/expires_at，路径opaque；read能力映射file.read/file.list元数据，绝不执行这些动作。真实确认期限可比ticket更短，取最小值；到期检查触发持久撤销，clock rollback/重启不恢复旧grant。
- RootBindings同步兼容，新增可选owner与proof/期限字段是内部dataclass。既有sync和async admission都将当前时钟传入grant范围复查，最终CAS前原真实签名/取消/当前权限检查保持；没有asyncio.run生产桥接，SQLite/stat/key查询off-loop。
- 装配只连接已给定适配器，不挂载网络/API/IPC/Tool，不生成批准/选择/执行回执或flags。缺actual directory/mapping/native选择/authority/Reader/OSbackend时相应入口明确不可用。采用A已接受**content固定Ref**，无新RefKind、无artifact旧pin别名。

实际A装配示例：

```python
mapping = RegisteredPrincipalMapping(container.runner_devices)
parts = assemble_runner_adapters(
    device_id=actual_device_id,
    control_bindings=(ControlKeyBinding(actual_device_id, registered_control_key_id, protected_handle),),
    directory=current_key_directory,
    credentials=WindowsCredentialStore(private_service_namespace),
    grants=persistent_native_grants,
    admissions=actual_admissions,
    selections=actual_consumed_selection_state,
    native_roots=actual_native_root_directory,
    mapping=mapping,
    authority=container.runner_authority,
    receipt_commands=container.runner_receipt_commands,
    journal_path=private_native_dir / "terminal-receipts.sqlite",
)
# A在真实可信构造点接线，仍须真实channel/gate/Run/policy/model/lease/fence全部依赖。
container.runner_commands.signer = parts.control_signing
container.runner_commands.roots = parts.roots
snapshot = await parts.roots.current(actual_device_id, actual_workspace_ref, trusted_ctx)
command = await parts.control_signing.sign(actual_registered_draft, device_id=actual_device_id)
await parts.control_signing.verify(command, device_id=actual_device_id)
```

缺source/OS拒绝、版本/内容冲突、默认未挂载与真实收件后journal调用例子见[R2d-001](../requests/D/R2d-001-adapter-wiring.md)。示例里的真实来源参数不是本包fixture，不能从模型/command正文填充。受控装配测试另用明确登记源/authority/native确认fixture，无真实平台channel/source claim。

### 实际验证命令和回执

```powershell
.venv/Scripts/python.exe -m ruff check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check src/uaw/workspace apps/local_runner/uaw_runner tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py --basetemp tests/.artifacts/D/MS-R2d/tmp-final2 -q --junitxml tests/.artifacts/D/MS-R2d/junit.xml
git diff --check
```

**最终326 passed，0 failure/error/skip，45.05s**；新增76项（22控制签名、1实际OS、52native root后端/装配、1异步admission根期限），原250项journal/admission/公共签名与DTO回归完整保留。Ruff通过，格式31文件通过，Mypy15源码文件通过，所有退出码0。消费前全局key撤销改动单独复验root与原persistent pairing共73项通过，然后取得最终326项组合回执。

**OS实际实连：**WindowsCredentialStore直接使用`keyring.backends.Windows.WinVaultKeyring`，随机本包namespace/handle验证不存在→ProtectedSigner真实生成→OS写入/读取→Ed25519签名/verify→重建store及目录再签→当前key撤销拒绝→finally删除并再次证明missing。阶段和最终均passed/cleaned=true；没有打印/落盘private secret，没有操作已有用户凭据。OS不可用分支无fixture冒充成功，本机本次OS验证没有未通过项。

**本机授权根：**真实临时目录、SQLite消费/grant与dev/inode检查、有限确认期限、重启及新Python进程恢复、8线程revoke CAS唯一胜者、替换/Windows临时junction越界拒绝、clock rollback、主体/session/device/workspace跨界、缺证明/缺字段旧记录拒绝、当前key错误角色/域/撤销、await期间期限/源变更与协作取消。Native用户确认及owner/channel服务明确为受控fixture，不证明真正认证用户完成配对。

回执路径全部本session ignored：`tests/.artifacts/D/MS-R2d/checks.json`、`public-hashes.json`、`static-checks.json`、`pytest-check.json`、`ruff.log`、`format.log`、`mypy.log`、`diff.log`、`pytest.log`、`junit.xml`；阶段`stage-junit.xml`、`stage-windows-control-receipt.json`；最终`windows-control-receipt.json`（只含backend/status/随机namespace/handle/cleaned，无secret）。测试SQLite和根仅位于相应本session basetemp。早期开发阶段语法/fixture import/局部mypy调用范围等失败已修复，不计入最终成功回执；无最终失败/跳过项。

公共字节与ms-i2g-start完全一致：schema及资源副本`cc5dbc6ba7bdaba40529ed196fe1249176b49967f741ecf017e40275417a8c45`，shared ports`fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104`，shared contracts`08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b`，uv.lock`a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f`；composition摘要和完整核对见public-hashes.json。

### 仍缺真实来源和接线要求

- A提供真实control/device key登记与构造绑定生命周期、channel/device-owner关系、native用户选择/possession/确认回执及实际有限期限、固定workspace来源、当前role/resource/consent gate；默认生产channel/signer/root组合仍由A接线验收。实际OS后端成功不自动证明这些来源存在。
- 本机grant存具体字段的明确SQLite组件后端，选择control库/native目录/grant/journal各自私有文件，不决定D01；正式部署ACL/备份/保留/导入旧记录/根重新授权生命周期由A协调。多binding/无完整pin不自动挑选，旧缺证明记录不迁移成授权。
- 选择消费与grant写入不是共同事务，consume后中断可能丢可用性但不得重放；已commit后取消/源撤销保留真实状态，下一次current仍复查。worker线程无法撤回已完成的consume/commit；多次复查不能证明跨服务原子权限，也没有OS句柄TOCTOU隔离或断电/磁盘损坏验收。
- ProtectedSigner provisioning仍需可信单owner随机handle：公共CredentialStorePort缺create-only CAS，没有自行扩shared或覆盖已有handle。真正OS凭据生命周期/多实例provision协调交A处理。
- 原内部Ticket.document签名只服务既有组件proof，没有重解释为公开配对V2；可信IPC/真实本机用户确认尚缺。没有签发实际执行回执：装配测试收到的failed回执明确为协议fixture，admission不证明执行。
- 不从Runner ok推Tool applied，不从failed/cancelled推not_applied/零费用；journal恢复不重新准入。没有文件动作/安装/写入exec、产品flags/API开放或D03决策。完整MS-R2继续等待A发布后续依赖与任务。


## MS-R2e 阶段交接（2026-10-08，前两项）

- 实际目录/分支：E:/UAW/.worktrees/runner / dev/runner；干净后 fetch origin --tags、merge --ff-only ms-i2h-start 成功，HEAD/tag 同为 f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8；uv sync --frozen 成功，64 packages checked。
- 阶段源码：8d3fd1c9053ab9b02b85999ecd6dc0e5779b10cb。改动为 D 的 handle_read.py/read_executor.py/read_state.py、workspace/contracts.py typed snapshot wrappers、D 两个新测试和 requests/D/MS-R2e-ports.md；公共 schema/ports/锁/composition/API 未改。
- 固定构造、execute(command: RunnerCommand, *, authenticated_principal: Principal)->RunnerReceipt、独立 Ref/Reader/channel/authority/RootBindings/ProtectedSigner、成功/拒绝/重复例子见 requests/D/MS-R2e-ports.md。只 file.read/whole/text_span，UTF-8、1MiB 总量、64KiB/16384字符双上限；没有 list/IPC/写/安装/exec。
- 实际 Windows CreateFileW 根/各级目录/文件只读句柄 + GetFinalPathNameByHandleW/FileIdInfo/Basic/StandardInfo；拒绝链接/硬链接/特殊目标，持有无 write/delete share 句柄至签名和提交。OS 操作在线程；实际临时文件内容/完整 SHA256/片段范围进入现有签名终态 journal，未知一次使用不重读。
- 阶段验证：`.venv/Scripts/python.exe -m pytest tests/unit/runner/test_handle_read.py tests/integration/runner/test_read_executor.py -q --basetemp tests/.artifacts/D/MS-R2e/tmp-stage-4 --junitxml tests/.artifacts/D/MS-R2e/stage-junit-4.xml`：37 passed / 7.74s，0 fail/error/skip。Ruff check、format --check 20文件、Mypy workspace+runner 18源码、git diff --check 通过。
- 历史未通过：pytest.exe 直接入口缺 tests namespace 导入（stage-junit.xml），改 python -m pytest；stage-junit-2/3 各3失败，暴露 Text 16384字符约束和 Windows fixture 换行转换；组件保留双上限、fixture 用原始 UTF-8 bytes 后通过。一次修复脚本默认 GBK 读 UTF-8 失败，改显式 UTF-8。失败回执保留，不删除检查。
- 精确公共提案：仅 FileContent.text 的 maxLength 提升至65536，由 A 发布；当前不消费未发布更改。channel/owner/authority/登记源均为明示组件 fixture，真实密码学/SQLite/Windows句柄已验证，但本阶段不是可信 IPC/用户确认/生产 Runner 或 Tool applied。
- 接线：每个登记 command 使用实际固定 command_ref/channel_ref 构造，actor 来源可信入口；Reader 每次检查当前数据访问/root/key/device/owner，恢复独立于 Run 新准入。默认缺生产来源拒绝。开发 SQLite 不决定 D01，D03/D06 和 flags 不改。
- 下一步继续同包后两项：并发/新进程/重启/未知中断/已签名发布恢复、撤销/期限/协作取消、实际 OS 随机凭据回执及原 D 回归；此记录不宣称最终交付。


## MS-R2e 最终交接（2026-10-08）

### 实际版本与范围

- 工作区/分支：E:/UAW/.worktrees/runner / dev/runner。开工干净后 fetch origin --tags、merge --ff-only ms-i2h-start 成功，HEAD 与 tag commit 完全一致：f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8；uv sync --frozen 成功，Checked 64 packages。过程中未换基线、reset/rebase、修改其他 worktree 或 A 文件。
- 阶段源码 8d3fd1c9053ab9b02b85999ecd6dc0e5779b10cb；阶段 handoff 3957ea852f7a6f1ec6819ca590113281e26e44b8。
- 最终源码 ced41378d814b7bfbb641eb531fd875646050776；最终 handoff 为本记录的独立后续提交，实际 SHA 用 git rev-parse HEAD 查询。原包提交/记录保持。
- 全包源码/提案12文件：apps/local_runner/uaw_runner/{handle_read.py,read_executor.py,read_state.py,keys.py,protocol.py}；src/uaw/workspace/contracts.py；tests/unit/runner/test_handle_read.py；tests/integration/runner/{test_read_executor.py,read_child.py,test_windows_read_signing.py,test_native_root_source.py}；docs/coordination/requests/D/MS-R2e-ports.md。本记录第13文件，全部在 D 允许目录。
- 公共文件字节未变：contracts/uaw.schema.json 和资源副本 SHA256 595ebe8f9173b5a6c8608dfac9f339f1c4c7f8e7e5f0599687f04bf6511ef90d；shared ports fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104；shared contracts 08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b；uv.lock a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f。逐文件与 tag 比较回执 public-hashes.json。

### 固定入口、实际行为与取消

`ReadOnlyRunner.execute(command: RunnerCommand, *, authenticated_principal: Principal) -> RunnerReceipt`；固定 constructor 与可消费例子见 [MS-R2e-ports](../requests/D/MS-R2e-ports.md)。依赖 RunnerProtocol/AsyncAdmission、RootBindings/实际 RunnerRootSourcePort、独立 mapping/current authority/RunnerChannelSourcePort、固定 command_ref 的 ReceiptCommandReaderPort、ProtectedSigner/独立 DeviceSigningBinding、ReceiptJournal/ReadExecutionJournal 和实际预算 currency。

command_ref/channel_ref 来自可信组装实际登记；execute 严格复制输入，Reader 独立读固定原 command/device/owner，逐项比较，authenticated_principal 由独立可信入口提供。缺 channel/owner/authority/Reader/signature/private key/OS身份实现均拒绝；读取前实际 check_private 验证当前 device key 的 OS或注入 protected handle 持有，不用伪造 receipt 证明可用。

仅 file.read、whole/text_span UTF-8 常规文件；全文最大1MiB，返回最大64KiB且受当前16384字符公共上限，超限失败不截断；text_span 从0、end exclusive；其他定位/cursor/list 不可用。FileContent 使用实际原字节全文 SHA256、原 workspace/path/实际范围，payload 不泄露绝对路径或重写换行/Unicode。Usage pending，只保存实际测量 wall_time_ms 与明确提供的 currency；未知费用/其他维度省略。Runner ok 不推断 Tool applied，failed/cancelled 不推断 not_applied 或零费。

Windows 原子 CreateFileW 根/每级目录/目标句柄无 write/delete sharing；实际 GetFinalPathNameByHandleW、FileIdInfo、Basic/StandardInfo、路径身份与登记根身份复核，拒绝 junction/reparse/hardlink/特殊/ADS/绝对/越界/已观察替换或编辑。OS 操作在线程；句柄持有至签名和提交，异常/cancel 均关闭。普通现有/新 writer、rename/delete 被 OS sharing 拒绝；没有任意 hostile OS/管理员/驱动/预先可写内存映射隔离证明，不决定 D03。

关键 await、当前源返回后和提交前复查独立 owner/channel/authority/根版本/command 签名、取消、期限/request/parameters/policy/workspace、flags、lease/fence；关键外部检查后再次查询完整权威。设备签名完成后再次复查；changed/expired/cancelled 不提交签名结果。协作 CancelledError 传播；线程已打开/正在有界读取时等待其结束并关闭句柄，未完成签名的实际尝试留下 unknown，不编造 cancelled receipt。真实签名已持久化后的晚取消/撤销可保留真实历史结果，但失权调用不获得返回。

### 一次使用、终态和恢复例子

显式开发 SQLite 三个文件：PersistentAdmissions(admissions_path)、ReadExecutionJournal(reads_path)、ReceiptJournal(receipts_path)。组件日志不决定 D01，没有 PostgreSQL需求，本包未启动数据库或改任何数据库配置。ReadExecutionJournal 以完整 owner/device/command 声明绑定唯一稳定 command ID；claim 持久化先于打开，原 attempt/版本/主体/内容变化冲突；并发同命令仅一个进程获得新 claim。没有已签名结果时 unknown/in_progress 明确 unavailable，不自动重读。signed 持久化先于 publish；重启/新进程只验证和去重发布原 signature/Usage。实际 content Ref version=1/hash 覆盖完整签名 RunnerReceipt；不新加 RefKind、覆盖历史或从 admission 合成回执。

成功：实际源构造 runner、execute 已登记 file.read 返回真实设备签名 ok、journal 保存实际固定 Ref。拒绝：缺真实依赖/错误 actor、超限/二进制/定位不支持、来源撤销/期限/版本变化，明确 exception 或真实 observed failed terminal（无 payload）。重复：在当前数据访问仍有效时返回原 signed receipt，即使原文件已不存在/改变、原命令已过期或 Run 已取消，也不调用 admission/authority 或 OS 读取；根授权期限/撤销、control/device key、完整 owner/channel或 Reader 当前权限拒绝时拒绝恢复。A 的 Reader 必须提供真实数据权限策略，不能把 receipt 自身当授权。

### 实际验证回执

总回执目录 `tests/.artifacts/D/MS-R2e/`（ignored，仅本 session）。

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py -q --basetemp tests/.artifacts/D/MS-R2e/tmp-full-1 --junitxml tests/.artifacts/D/MS-R2e/full-junit-1.xml
.venv/Scripts/ruff.exe check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/ruff.exe format --check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/mypy.exe src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
git diff --check
```

- **431 passed / 108.44秒，0 failure/error/skip**；JUnit suite time108.021秒，节点431。原326完整重跑＋本包新增105不同节点，不累加阶段/重试次数。Ruff通过、格式38文件、Mypy18源码、diff通过；checks.json、full-junit-1.xml、full-1.log、ruff/format/mypy/diff.log、public-hashes.json。
- 阶段37 passed /7.74秒；新增完整定向97 passed /42.42秒（new-junit-4.xml/new-4.log），后续再增8项签名后来源变化/登记输入变化/明确currency检查并在431全回归验证。
- 真实验证：空/Unicode/原换行、UTF-8字节和字符范围、1MiB/64KiB边界、二进制/超限；实际 Windows 根/文件身份、junction内部/外部/打开前替换竞争、hardlink、同时编辑/rename/root替换共享冲突；await过期、读取后/签名后撤销/版本/主体/cancel、严格channel缺字段、错误通道、缺私钥、协作取消；多协程打开一次、5个新进程SQLite claim仅1胜者；新进程恢复原签名、unknown不重读、原Ref摘要/签名篡改、同command变更冲突、取消后原回执恢复及数据撤销拒绝。
- **实际 OS 回执** windows-read-receipt.json：WindowsCredentialStore/WinVaultKeyring，随机 namespace 的 control+device 私钥 provision/read/实际file.read receipt签名/重开密钥持有与签名/新进程恢复，status=passed、cleaned=true。windows-control-receipt.json 原随机 control key 回归同样 passed/cleaned=true。无既有用户凭据访问/修改、秘密输出或真实用户文件访问。
- 未通过历史保留：阶段导入/字符上限/fixture换行失败见阶段交接；后半包 new-junit-1/2/3 各有超大bytes自动节点名导致 Windows PYTEST_CURRENT_TEST超过32767字符的 setup/teardown error（无读取失败），修正显式短 ids 后通过 new-junit-4 与全量。首次修复匹配没命中，未删除检查；这些失败不算新增通过项。此前自动审批额度错误未执行 fixture 修改，用户继续后原流程重试通过，没有绕过审批。最终无失败项。

### A 接线要求与仍缺能力

- 精确公共提案仍待 A：仅 FileContent.text 的 maxLength从16384改65536，字节上限64KiB；不扩大 Text、不改其他 schema。当前组件遵守原上限，ASCII 64KiB尚不能按现有公共DTO返回；没有私加字段或消费未发布版本。
- 阶段/最终入口签名一致；A 用真实注册 command_ref/channel_ref、owner mapping/current authority/根来源、当前 key 目录、OS device private handle、实际数据权限 Reader 和独立持久路径构造。源变化不跨请求缓存许可。需要实际通道绑定/用户确认与部署日志策略后才能开放；默认生产 channel/确认仍缺，受控 fixture 不是可信 IPC、实际用户配对或完整产品执行验收。
- A负责 Runner→Tool 实际结果核验、引用登记和 composition/API/flags 接线；本包没有自动 Tool applied、IPC wire/配对V2/list/安装/写入/exec，没有决定 D01/D03/D06、开放flags或进入其他包。权威源与本机 SQLite 无跨服务事务，晚失败可能保留真实已签名历史记录；恢复必须仍有当前数据访问。
- 四个里程碑在本包范围完成；完整MS-R2/真实IPC/用户确认/产品任务验收继续等待。本包后停止，等待 A 审阅和后续派发；最终 handoff 提交后工作区应干净。


## MS-R2f M1/M2 阶段交付（2026-10-09）

分支 dev/runner，实际 ms-i2i-start 基线 d8023eb07e1460961782f297697da7428f6ad247，已 fetch/ff-only/tag等值/uv sync --frozen。源码 M1 81bc7cabf997447dd550e27de502e7462a1cb5ce；M2 ea16682101cc4c9a3e4d02398c5ccebbda6254a0。固定构造、关闭/错误语义、文件清单、39项阶段回执及 A 接线要求见 requests/D/MS-R2f-stage-ipc.md。真实 Windows 双进程/OS凭据/身份/角色签名与 registry 通过；账号/pairing/确认来源为独立临时 fixture。原始失败保留并已修复，当前阶段零失败。继续同包 M3/M4。


## MS-R2f 最终交接（2026-10-09）

- 实际工作区 E:/UAW/.worktrees/runner，分支 dev/runner；干净开工 fetch tags / ff-only ms-i2i-start，HEAD与tag一致 d8023eb07e1460961782f297697da7428f6ad247，uv sync --frozen成功（64包）。没有reset/rebase或覆盖公共文件。
- 源码：M1 81bc7cabf997447dd550e27de502e7462a1cb5ce；M2 ea16682101cc4c9a3e4d02398c5ccebbda6254a0；最终 d3f60771accca99832673820c8a43c4ec32f4cbd。阶段handoff36cb329保留，最终源码/本交接分开提交；原已接受历史保留。
- 文件：新增Runner ipc六模块；新增unit frame tests和integration ipc_fixture/ipc_child/test_windows_ipc/test_windows_read_ipc；native_root_source测试helper仅可选复用已provision的OS key。文档为D stage/final wiring和本handoff，workspace四文件无须改变。shared/schema/lock/composition/API/flags/其他session未修改。
- 公开内部接口：WindowsPipeListener/connect_pipe/PipeConnection、OsIdentity/PeerRegistrationPort/RegisteredPeer/IpcSigner/AuthenticatedPipeSession、ConnectionRegistry适配既有RunnerChannelSourcePort；ReadOnlyRunnerFactoryPort.create(ref,channel_ref=...)和ReadOnlyPipeEndpoint.serve_once()->实际content receipt Ref。命令body仅原固定Ref，Reader从独立登记恢复原签名命令/设备/owner，actor由registry真实连接提供；recover仅已有签名journal，不新准入/不重发未知。
- **505 passed /160.20秒，0失败/错误/跳过**（基线432＋新增73，非重试累加）。Ruff通过、格式49文件、Mypy24源码、diff通过；命令、详细原始失败/修复、实际输出和构造例子见 [MS-R2f-final-wiring.md](../requests/D/MS-R2f-final-wiring.md)。回执 tests/.artifacts/D/MS-R2f/full.xml/full.log、checks.json、public-hashes.json、ruff/format/mypy.log，专项m4-2.xml 70通过、bounds.xml 4通过。
- 实际Windows双隐藏进程、内核显式DACL、本机token/PID/创建时间/存活及当前角色key/nonce，帧256KiB/10秒以内、撤销/期限/断帧/重放/并发/协作取消/重连；临时根UTF-8实际read、OS device签名journal传回，双连接读取一次，回复丢失后新连接恢复原Ref/签名，取消后不重新准入。44份随机IPC OS凭据清理回执全cleaned=true，管道/子进程/句柄finally清理；原OS key/文件/跨进程admission与journal回归保留。
- 测试账号/owner/pairing/native确认和current authority是独立受控来源；没有从body授予批准，实连不是真实配对。当前最终无未通过项；早期fixture角色/输出编码/换行/import和M1回执目录/PID失败全部保留并已修复，没有删验权/签名检查。
- A提供真实受保护进程→owner/actor/device/key/pairing/期限映射、native确认、真实当前authority/Root/PrincipalMapping、Container.reader数据权限、OS handles及持久路径；控制端/组装/业务Tool核验归A。缺这些来源默认不可用、不挂载生产/用户项目；开发IPC和SQLite不是D01/D03正式部署决策，未公开配对V2/list/写入安装exec/flags，不推断Tool applied或零费用。
- 只完成本包；完整MS-R2与产品授权继续等待。最终handoff提交后干净交付，停止，等待A接受/下一实际包。
