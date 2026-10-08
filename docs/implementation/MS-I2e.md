# MS-I2e：Tool 核对组件接受与下一轮基线

日期：2026-10-08。集成分支 `integration`；固定标签 `ms-i2e`。已验证代码/证据提交见 [DISPATCH](../coordination/DISPATCH.md)，标签另包含随后编写的派发状态。

## 1. 合入与实际修复

| 来源 | 源码 / 交接提交 | A 合入 | 接受范围 |
| --- | --- | --- | --- |
| C / MS-T2b | `c78d37101a4c203cbe487f15cb5cabc063ca5f76` / `3c76bb2c9f281ce48c99de500b2a9faa504ab03e` | `daaae65870642a8fa54b23eb276150e004a5ffd1` | 预算/政策 port 消费、可信回执核对及独立费用恢复组件 |

B 的 MS-C3、D 的 MS-R2b 和 A 的根执行租约/Model 输入路由已经在前一 [MS-I2d](MS-I2d.md) 验证；本次基线包含这些已合入成果。合并无冲突，A 没有修改三个 worker 的原 worktree、分支、提交或 handoff。

首次同时收集 Tool 单元/SQL 时失败：两个目录都有 `test_reconciliation.py`，pytest 默认导入模式发生模块名冲突。A 将集成分支的 SQL 文件改为 `tests/integration/tool/test_tool_reconciliation_postgres.py`，保留原业务和所有断言；重新收集、执行通过。C 原 handoff 里的文件名和缺连接回执保持历史原样。

## 2. 实际验证

- 独立 Tool 检查：`tests/unit/tool tests/integration/tool --require-postgres`，**140 passed，0 failure/error/skip，167.62s**；其中单元97项，真实 PostgreSQL 43项。
- 相比前一基线，C 新增31项单元和26项SQL；原66项单元/17项SQL也重新运行。
- 全量：`./ops/check.ps1 -WithPostgres`，**563 passed，0 failure/error/skip**，耗时 `672.21s (11m12s)`。Ruff、138文件格式检查、95源码文件的 Mypy 通过。
- 对象/接口校验：1268 named schemas、272接口；已实现生产入口仍26项。生成器只检查契约与计划，不代替运行验证。
- 全量回执：[p0-tests.xml](evidence/p0-tests.xml)；环境、版本与实际源码摘要：[environment.json](evidence/environment.json)。A 的独立 Tool 回执位于 ignored `.data/ms-t2b-accept.xml`。

C 原环境的43项准备错误不是产品失败，也不是通过证据；本次在真实开发 PostgreSQL、随机独立主体与受控来源执行到业务断言，没有 SQLite/mock 替代 PostgreSQL，不清空整库。

## 3. 已确认行为与接线边界

1. Tool 消费实际 `ExecutionPolicyPort` 与 `BudgetStatePort`，原尝试费用恢复不再私读预算/政策表；缺 port 明确拒绝。
2. 原动作、attempt、provider、精确 receipt Ref、Usage attempt 与实际证据绑定核对。证据检查后再次读取回执，来源变化/撤销拒绝，同版本不同正文冲突。
3. 固定费用计划与 CAS 支持重启、新进程、提交后响应丢失与并发恢复，不在 Tool 锁内调用预算服务。不能换 attempt、重发动作或推断未执行。
4. 效果结论和费用独立。`EffectRecord.confirmed` 只表示结论确定，必须读实际 receipt.outcome；`not_applied` 可能有非零费用，`unknown` 也可能费用已确认。核对 `ok` 不表示整个工具/Task 成功。
5. 已知效果不会因费用拒绝而回滚；pending 未观察维度保留额度。原 Run 取消或过期后可以核算原尝试，新的执行准入仍拒绝。

当前没有实际 `ActionReceiptLookup`、生产 receipt/evidence Reader、角色/资源/executor 或真实 Runner authority；没有新增 composition 绑定、HTTP 或已实现 Runtime 数。受控 SQL Reader 是组件测试来源，不能注册为产品工具。

## 4. C-003 公共提案的决定

- 保留 `EffectRecord` 现有字段，不给 confirmed 增加“执行成功”的含义。下一包提供严格实际 outcome 读取，消费方显式检查 outcome 与所需验收。
- 保留 `ReconcileRequest(action_id, expected_revision)`；批准 C 的内部可选 Lookup port，由独立已登记来源选取实际固定 Ref。方法与缺省行为见 [下一轮契约](../coordination/requests/A/MS-I2e-next-packages.md)。不接受模型额外 receipt 参数。
- 暂不改变 BudgetService 的 pending 增量/最终账单修订规则。现有拒绝与原额度继续保留，后续真实 confirmed 账单可核对；需求进入 A 的预算规则版本后再实现，不让 C 私写会计状态。
- orphan Tool 意图的会计恢复/实际 dispatch 协调进入 A 的 MS-I2f/完整 MS-I2；当前不以调用 dispatch“修账”来证明实际执行。

## 5. 下一轮与未通过门槛

共同基线 `ms-i2e`：B / MS-C4 上下文纯计算有界缓存；C / MS-T2c 统一核对入口与明确 outcome 读取；D / MS-R2c 签名终态回执 journal；A / MS-I2f 实际设备归属、登记命令及当前权威。各包的精确输入/输出、目录、策略、失败和验收见 [范围文档](../coordination/requests/A/MS-I2e-next-packages.md)，可直接转发的消息见 [NEXT_WAVE](../coordination/NEXT_WAVE.md)。

完整 MS-I2/MS-T2/MS-R2、P1-02/03/04 仍未完成。真实 LLM、配对、可信 IPC、OS 凭据实连、安装/写文件/exec、通用 Context authority 和 Agent 闭环尚未验收；功能旗标保持原值，D01/D03/D06 保留原门槛。

回退由 A revert 相应源码及集成提交；保留已存在的持久意图、unknown/已知效果与费用记录。代码回退不撤销外部副作用。本轮没有真实业务 dispatch。
