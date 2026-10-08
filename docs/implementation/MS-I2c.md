# MS-I2c：C/D 组件接受与下一轮公共接口

日期：2026-10-08。固定版本 `ms-i2c`。完整 MS-I2 与 P1-02/03/04 继续 in_progress。

## 实际合入

| 包 | Worker 提交 | A merge | 本轮接受范围 |
| --- | --- | --- | --- |
| C / MS-T2a | e3a19dd / 827f6ca | 3148cf1 | 持久调用账本、审批权威及预算阶段恢复组件；66 个原组件用例、17 个真实 PostgreSQL 用例 |
| D / MS-R2a | 2049c3d / 45e0f56 | 440d2fc | 真实 Ed25519、当前 key 角色/撤销与持久一次消费；原汇报 100 项范围已实际复核，包含跨进程竞争 |

没有合并冲突，没有改写 worker 分支或 handoff。D 的 100 项含共享契约/签名检查，不当作 100 个新增用例。C 新增 14 个单位检查和 17 个 SQL 检查；D 新增 25 个组件检查。

## 实际发现与修复

1. C 首次 SQL 联测在准备阶段 17 项全部报错：ProviderBinding 契约为 active，fixture 与 authority 使用 connected。A 做最小兼容修复，受控 fixture 状态不表示提供方实际联网。
2. C 的未知用量只观察到币种，原共享 schema 错误要求未观察的计数。A 允许 pending 省略全部未知维度；confirmed/estimated 仍要求完整记录。预算结算按缺失维度保留预留，不把未知写成零。
3. 新增 A 用例先后把金额字符串格式、reservation 的部分结算状态写成了错误预期，失败；改为 Decimal 数值比较和既有 partially_settled 状态。账本的 billing_pending/held 仍分别验证未知用量；实现未因此改动额度算法。

## 新代码与公开消费契约

- BudgetService 实现 BudgetStatePort：当前账本和原尝试 reservation 查询，单 SELECT 一致观察、主体/Run/会话/任务/attempt 绑定、revision 检查，取消/过期后允许账务恢复读。查询不授权新动作。
- ToolReconciliationReceipt 和 ToolReceiptReaderPort：固定动作/尝试/提供方/回执/实际证据/用量核对；没有生产 Reader。确定效果必须有证据，不从超时推测。
- RunnerAuthoritySnapshot 和 AsyncRunnerAuthorityPort：认证来源独立于命令、字段全部必填；没有生产 authority。D 下一轮实现异步消费协议。
- ModelPrompt 明确为已有 ModelInputPort 的公开结果；B 可只读导入，provider 类型仍私有。

详细签名与限制见 [MS-I2c ports](../coordination/requests/A/MS-I2c-ports.md)。没有新增迁移、依赖或 HTTP 路由，没有开放 flags。

## 验证与证据

最终全量 **360 passed，0 failure/error/skip**，耗时 286.20 秒；Ruff/格式检查通过（121 文件），Mypy 检查 89 个源码文件通过。证据见 [JUnit](evidence/p0-tests.xml) 和 [环境/源码摘要](evidence/environment.json)。发布前执行：

```powershell
./ops/check.ps1 -WithPostgres
.venv/Scripts/python.exe ops/capture_environment.py
.venv/Scripts/python.exe contracts/check_interfaces.py
.venv/Scripts/python.exe planning/build_plan.py
```

真实 PostgreSQL 使用原开发实例、唯一测试主体与定向清理。Docker 当时关闭，启动原 Docker Desktop 后恢复既有数据库，没有安装或重置。测试确认无生产 Reader/authority/executor 的分支保持不可用。

## 下一轮及限制

B 的 MS-C3（模型输入）、C 的 MS-T2b（预算接口与核对）、D 的 MS-R2b（异步协议）可在固定版本上并行。见 [直接转发说明](../coordination/NEXT_WAVE.md)。A 继续公共组装、当前权威和组合验收。

Tool/Workspace/通用 Context 仍未绑定为产品能力；Agent 循环、可信 IPC、实际用户配对、OS 密钥库实连、安装/写入/exec 与实际 LLM 未完成。D 的 SQLite 仍是显式开发组件存储，不代表 D01 已决定；D01/D03/D06 门槛继续保留。
