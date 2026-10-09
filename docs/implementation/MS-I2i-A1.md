# MS-I2i-A1：评估、成果、完成控制与组件接线

日期：2026-10-09。开工来源 `ms-i2i-start / d8023eb07e1460961782f297697da7428f6ad247`。
这是开发组件阶段验收；B最终交接已汇合，唯一一次完整本轮回归运行中，历史1077属于 MS-I2g。

## 实际增加的能力

- 实际固定用户模型分别承担规则语义评估和成果语义核验；共用有界、版本固定的评估输入，避免多规则 Context 递归。
- 从真实已结束 ModelOutput 登记 UTF-8 文本/Markdown Blob、不可变 Artifact 与原操作来源。
- 从原目标、每条约束和每项输出构建合同，生成逐项 VerificationReport、DeliveryProposal 和固定 Bundle。
- 独立控制器复查当前来源/取消/修订/原操作/未知调用/预算，提交同会话 CAS 终态和 Task 成果。报告成功不能直接授权完成。
- 精确用户接受记录只由独立认证用户登记。合同不要求接受时可完成；要求接受时必须匹配确切成果版本。
- 实际本地办公提供方、角色、审批、预算、executor/verifier 和结果恢复接线；模型可以选择 text.inspect、arithmetic.calculate、data.inspect_json。
- A 控制端消费 D 的真实 Windows 活连接、设备签名与临时只读结果；没有生产配对/用户项目授权的默认绑定。

[目录、函数、输入输出及完整处理策略](../coordination/requests/A/MS-I2i-completion-wiring.md)。
新增五个内部持久对象由 catalog 生成逐字段文档；原公共接口数量仍为272，未增加公开 Runtime/Tool 路由或 flags。

## 三组件接受情况

| 包 | 实际来源与回执 | A 接受边界 |
| --- | --- | --- |
| B/MS-C7 | M3 `fecd218`，说明 `09a7cc3`；277 unit、3 routing、基线/最终各4矩阵由 worker 实跑；最终277 unit＋128不同SQL通过，交接8611384 | 阶段接口与来源修复已合入；A 实际 SQL 批读9项通过并独立发布 `ms-i2i-batch-a1 / 65ef26d`；按组件接受 |
| C/MS-T2f | source `b09fb7d`、handoff `efb997c`；316 unit＋178不同 SQL 原节点核验 | 按组件及 A 实际办公消费者接线接受；不标完整 MS-T2/产品能力接受 |
| D/MS-R2f | source `d3f6077`、handoff `cd6b33c`；505项，44份随机 OS 凭据清理回执 | 按真实 Windows IPC/签名/临时读取组件及 A 消费者接受；UAW账号/根确认/Run权限仍是独立测试来源 |

所有 merge 保留 worker 原提交与旧交接；A 没有切换、同步或编辑其他工作区。
原 C 测试失败/修复/更名及 D 失败/清理记录保留；没有将历史未沿用的节点算进最终通过数。
[逐回执 hash 和接受范围](evidence/ms-i2i-worker-receipts.json)。

## A 验证

实际 SQL 使用 A 独立 PostgreSQL55432。Model HTTP 在组件测试中受控，不计真实 LLM 质量。
真实 Windows 测试使用随机密钥和临时文件，实际双进程、OS身份、签名、读取与清理均执行。
A跨阶段去重 **192个聚焦节点（163单元＋29 SQL/OS）通过**；164源码Mypy、Ruff和281文件格式通过。当前受影响模块和跨模块节点见 [A证据](evidence/ms-i2i-a1.json)；唯一一次完整本轮回归运行中。

关键边界：

- 同请求并发四次只提交一次完成；重建控制器恢复原结果。
- 缺用户接受、错误成果版本、failed/not_run/blocked不能完成。
- 文本中的网页链接没有实际网页 Reader 时为 not_run；模型语义通过也不能覆盖技术缺口。
- 真实取消/输入修订之后，旧成果不能完成；持久 claimed/unknown Model 回执阻止终态。
- 评估消费该 Run 的完整工具动作/规格/结果清单；评估后新增动作、任一原行变化都拒绝旧完成提案。只证明本 Run 记录的执行，不证明全局 OS/供应商内部行为。
- 模型漏项、多余 ID、伪造证据和缺实际 artifact 引用拒绝。动态 schema 限定实际要求数量/ID和可用证据别名；代码继续独立复查。
- 已完成模型调用的费用 pending 保留 money hold；不会为了完成而释放未知费用或宣称0费用。
- 三个办公工具经真实 SQL 审批和预算执行；取消后只恢复原结果，提供方撤销后结果读取拒绝。
- A 实际控制客户端→D 实际命名管道→真实临时文件→设备签名结果；篡改命令/回执/尝试或正文注入权限拒绝。

### 失败及修正记录

原始回执全部位于 ignored `tests/.artifacts/A/MS-I2i/`，不覆盖旧文件：

1. 规则 Ref 的正文 hash 与实际行 hash 不同；评估来源改为实际完整行 pin，不改变规则原 Ref。
2. 首次完成 SQL 使用非法 report RefKind；改为契约规定的 verification。
3. 批读测试的 DTO/全NULL SQL参数类型错误修正；9个批读节点通过，原 aggregate 中3个完成失败保留。
4. 完成控制器原先把 pending money hold 当作未完成执行；改为保留 money，并单独核验所有预约是否仍可执行。
5. 办公 fixture 未声明 tool.invoke，以及测试错误地读取不存在的 ToolResult.usage；改为实际 scope 和 usage_ref→Usage 行/版本/attempt/billing 核验，未放宽执行检查。
6. A Runner模块移除跨 package 生产硬依赖；测试显式提供 Runner import 路径。真实控制客户端单独双进程验证，不把函数核验冒充完整传输。
7. 默认受限环境中的 asyncio 用例挂起；同用例在授权 host 环境通过。保留初始结果，后续真实 SQL/OS/async 检查使用 host 环境。
8. 计算任务只有最后一步观察，不能充分证明“只执行一次、不做业务联网”；增加实际 Run 工具完整账本及终态集合复查，保留原 not_run，不强迫语义模型判通过。

## 真实 DeepSeek 验收

实际请求模型 `deepseek-flash`，对应用户指定 DeepSeek-V4.1-Flash。根 Agent、规则评估和成果核验都使用原 Run 固定模型。
办公待办、学术材料讨论、JSON检查、多规则任务已经实际通过；取消和修订阻止旧成果完成；同级中英文冲突返回 rule_conflict。
计算任务第四次真实样例已通过全部要求并提交完成；以 [全部实际尝试与费用记录](evidence/ms-i2i-live-probes.json) 中对应结果为准，不提前标通过。

真实失败也计入：首次输出描述被错误当作格式枚举；规则模型误降平台 critical；计算核验多余空 ID，随后又把记录 ID 当证据别名；修订样例错误使用 Run 而非 input-set 修订号。
已修正调用策略/结构约束，保留每次原请求、响应和费用。失败的原尝试不重发，更正后用明确不同验收请求。
Token 是实际已知用量；供应商货币账单仍 pending，不把估算或未配置金额写成已确认费用。

## 仍未交付的产品能力

生产认证、真实用户配对/根确认、网页实查、专业文件编辑与用户接受 UI 未因本阶段开放。
本机文件写入、安装、exec、子 Agent、DAG及相关 flags 保持原门槛；本阶段未自行决定 D01/D03/D06。
B 最终交接已汇合；A 的唯一一次本轮完整回归正在运行。阶段标签 ms-i2i-a1 不代表完整集成里程碑通过，最终基线待实际回执。

契约结构/1294示例/链接没有错误；整体contract checker因17个旧全量源码摘要过期返回1，不标整个检查通过。旧报告已归档，新完整来源证据在最终集成里程碑更新。
