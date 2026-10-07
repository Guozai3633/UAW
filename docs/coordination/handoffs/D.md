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
