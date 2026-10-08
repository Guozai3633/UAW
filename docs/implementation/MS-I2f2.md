# MS-I2f2：缓存、工具恢复和签名 journal 集成

日期：2026-10-08。Session A，`E:/UAW` / `integration`。详细接口、来源与默认边界见 [接线设计](../coordination/requests/A/MS-I2f2-integration.md)。固定发布与代码 SHA 由 [DISPATCH](../coordination/DISPATCH.md) 记录。

## 1. 实际交付与合并

三个 worker 都固定 `ms-i2e / ba2f3b0d9417e6d695eaa74c2f766217c98b01f1`；A 从 `ms-i2f1 / d3fca345` 逐包合入。没有冲突或路径归属越界，未改写 worker 原 worktree、分支、提交和 handoff。

| 包 | 原源码提交 | 原交接提交 | A merge | 新增检查 |
| --- | --- | --- | --- | --- |
| MS-C4 | acc68fc670ed5edb5186908219408c1bc4c1dfda | 1acedb4e6a15a5cc9de6ff7a1c1afd34afc9ab1e | 2f674ec86daeeb61bf1c635f5d7fbb035a1110d2 | 67单元＋11 SQL |
| MS-T2c | 3d8cda36d1422a70fb877a87868affe587c1441c | 3c0cd999ca9f02303de2786e31ef49df56a19a53 | 23739a10ef6e5b7312f4a6ceca8249aa9179919c | 38单元＋27 SQL |
| MS-R2c | 38ee8099129fd54571435faaeb8bd0b4f339a17c | 1e89d5c845423f7769cf1025491c9f82103c165e | 5b8c1adcd16fa54acfbf32040ec5c5da6ef17a32 | 73单元＋5实际跨进程 |
| A / MS-I2f2 | 见DISPATCH | 本记录 | 集成分支 | 10跨模块 SQL/组装检查 |

Worker 原回执如实保留：B SQL 仅收集，C SQL 缺 URL 在 setup 停止；本次接受以 A 的实际 PostgreSQL 回执为准。新增量 78＋65＋78＋10＝231，不能将含旧回归的组件总数重复计入新增。

## 2. A 的接线与修正

- 新 `src/uaw/run/runner_receipts.py` 从平台 SQL 原命令和独立设备 owner 构建 `RegisteredReceiptCommand`，前后复查当前来源，严格复制 DTO，设独立恢复调用时限。默认缺生产通道/签名来源仍拒绝。
- composition 提供内部 `runner_receipt_commands`，缓存可显式注入两个计算入口；默认关闭，不创建 journal、不开放 Tool/Workspace/通用 Context/Agent Runtime。
- D journal 输出从 `artifact` 统一为 `content` 固定引用。原交付保留；不存在公共 RefKind/schema/锁/迁移变更，也不提供透明旧引用别名。
- 新 SQL 测试使用实际登记/权限/预算服务和真实 Ed25519 原语；channel/root/consent、设备私钥及签名 failed receipt 为明确受控输入，没有执行文件动作或真实 IPC。
- 两次独立运行发现同一个新增测试 fixture 的错误调用：先使用了不存在的 `device_id` 参数，再将初始 key revision 写为 1；实际注册 revision 是 0。修正测试消费真实方法 `revoke_key(key_id, expected_revision=0)`，没有放宽实现或修改公共契约。

## 3. 验证回执

- 独立组件复验：**674 passed，0 failure/error/skip**。B 174单元＋35真实SQL；C 135单元＋70真实SQL；D及其原公共回归250项；A新增10项。
- 全部 **841个唯一测试节点通过，0 failure/error/skip**：先实跑674个组件用例，再补跑其余167项。聚合JUnit累计 1443.84s；原610项全部覆盖，新增231项。不是一条pytest命令连续执行841项。Ruff/格式156文件、Mypy102源码文件通过。
- 1281 schemas、272接口、304负例拒绝、26已实现公开操作；50轮/115节点和27功能包的依赖/目录检查通过。没有新增公开执行入口。
- [全量聚合JUnit](evidence/p0-tests.xml)、[841节点覆盖证明](evidence/ms-i2f2-coverage.json) 与 [现场环境/源码摘要](evidence/environment.json) 是发布证据；原始两批回执位于 ignored `.data/ms-i2f2-components.xml` 和 `.data/ms-i2f2-remaining.xml`。覆盖清单与两批实际case逐项匹配，无重复或遗漏。
- A主动停止了重复SQL的整套运行，该进程退出不作为通过回执；static/format/mypy已经通过。其后仅补尚未覆盖的167项。辅助覆盖脚本初版的项目导入路径和参数反斜杠归一化错误已修正，最终实际841项收集和674项既有回执精确匹配；没有修改运行源码或测试输入。
- 环境读取实际开发Docker/PostgreSQL版本，摘要逐项核对当前源文件；原公共schema/ports/contracts、锁和提示词相对ms-i2f1不变。

## 4. 接受边界与下一项依赖

MS-C4/MS-T2c/MS-R2c 只按组件接受；MS-I2f2 只按集成开发范围接受。当前权限/来源不被缓存，恢复不创建 attempt 或 reserve/dispatch，签名/confirmed/核对 ok 不代表外部动作成功或用户任务完成。

生产 Lookup/Tool Reader/executor、通用 Context authority/Reader、真实认证通道、配对、本机根/OS 密钥、IPC 与最终 fence/撤销消费仍有缺口。完整 MS-I2f/MS-I2/MS-T2/MS-R2 和 P1 阶段未验收，能力 flags 继续关闭，D01/D03/D06 保留。

B/C/D 当前包已到交付边界；后续同步固定新集成版本，不自动重开旧包或进入完整执行包。A 先完成上述真实来源契约和接线再发布可独立开发任务，见 [下一轮安排](../coordination/NEXT_WAVE.md)。
