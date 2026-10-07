# A 接受 MS-C2：固定上下文快照和引用组件

日期：2026-10-07。这是组件接受记录，完整 P1-02 仍在开发中。

## 实际合入

- B 实现：`c85bf52b283866cfdcad689356faee239152ba1d`；交接：`c6ae25dc7526f811f2b614508e93a017e09ecdd1`。
- B 开发基线：`ms-i1` / `f33d16245619b6d446816a36b65bd5c1fc607593`。
- A 接收时基线：`ms-i2a` / `ac9bf621e3caebf060300b3a628b77dee36f7ab0`。
- A merge：`aa421be113388a5639963eefa4ddf4a45faeb192`，保留两份 worker 提交和原历史，没有合并冲突。
- 差异只在 B 获准的六个 Context 源文件、两份测试及自身提案/交接文档。没有修改 A 保留文件、公共 schema、锁、模型选择或能力 flags。

## 接口审阅决定

采用 B 的 `ContextRepository`、`Composer`、`References`、`CompositionAuthority` 及可选 facade 注入参数，具体消费要求见 [A 接线决定](../coordination/requests/A/MS-C2-integration.md)。

组件可原子保存不可变快照、规则、Scope、原始 ContextRequest、Run 绑定和实际读取的来源记录；相同逻辑 operation 重放，同键异参拒绝。打开快照/引用时重新检查当前来源、权限、取消、epoch、规则和固定模型窗口。新 epoch 新建快照，原快照不会被覆盖。

这些组件没有与审批的新 public ports/Runner 签名冲突。`ContextComponents` 原有参数兼容，新增仓储/authority 均为可选；A 的理解专用 builder 与 Model 输入解析仍使用原有来源协议。默认组装未注入通用 authority，因此 `RuntimeBindings.context` 继续未绑定，通用 build 不会返回伪造成功。

## A 实际执行的验证

```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/context
./ops/start-dev-db.ps1
.venv/Scripts/python.exe -m pytest -q tests/integration/context tests/integration/test_context_wiring.py --require-postgres
./ops/check.ps1 -WithPostgres
.venv/Scripts/python.exe ops/capture_environment.py
.venv/Scripts/python.exe contracts/check_interfaces.py
```

- Context 组件：**64 passed**（原 MS-C1 39 项＋MS-C2 新增 25 项）。
- 真实 PostgreSQL：B 新增 **9 项**和 A 原 MS-I1 接线 **8 项**，合计 **17 passed**。随机主体清理，无 truncate，未给 B 复制配置/凭据。
- 用例实际核对事务回滚、持久重放、并发一次保存、参数冲突、epoch 失效、真实原文引用、来源删除、当前政策撤销、取消及缺 Reader 无提交。SQL 测试中的 epoch/空能力集合明确为受控适配器，不代表产品工具发现已完成。
- 集成全量 **285 passed，0 failure/error/skip**；Ruff/格式通过，Mypy 检查 80 个源码文件。相较 `ms-i2a` 新增 34 项（25 组件＋9 SQL），原有 251 项继续通过。[JUnit](evidence/p0-tests.xml) 与 [源码/环境摘要](evidence/environment.json)记录当前源码回执。

## 未完成范围与下一步

生产 `CompositionAuthority`、实际 ModelToolSet Reader、各 purpose 规则/保护/epoch 所有者、通用 Model 输入解析仍需 A 后续接线。没有把测试中的空工具列表或理解指令用于 agent_step。Workspace/Board/Memory、预览/已完成 Run、多目录自然语言规则评估、Citation 和分页仍明确不可用。

本次不修改公共 schema、依赖锁、迁移或能力开关，不扩模型/文件/网络权限。D01/D03/D06 仍保留。完整 P1-02 及 Agent 闭环不因组件 SQL 通过自动接受。

B 本包接受后保留干净交付边界，未自动安排下一包；C/D 继续 `ms-i2a` 的 MS-T2a/MS-R2a，无需中途同步本次 Context 合入。A 继续公共接线和组合验收。[统一派发表](../coordination/DISPATCH.md)记录实际状态。

源码回退可由 A 正常 revert 本次 merge；不会因此删除已存在的不可变数据库记录。后续读取仍受当前授权与版本检查。
