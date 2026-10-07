# MS-I1：第一波组件合入与 Context 接线

日期：2026-10-07。A 已分别审阅、合入 MS-C1、MS-T1、MS-R1；完成 MS-I1 的开发范围。P1-02/03/04 整轮仍为开发中。

## 合入记录

| 包 | 实现提交 | 交接提交 | A 合并提交 |
| --- | --- | --- | --- |
| B / MS-C1 | 307a49b | 0da308f | 2f0a427eaf1e8d4b050cdfa2d8dafc007716bcbc |
| C / MS-T1 | f9622ca | 5dd77c2 | e7b4a74640ad333dc80b291472f1550afbbd74e7 |
| D / MS-R1 | d77bf35 | 300bdf5 | c8a40d663cccb05bd57c346a788487f594935fe8 |

三个包的修改均位于各自允许路径；公共 schema、shared ports/contracts、uv.lock 和理解提示词保持原固定摘要。未发生合并冲突。Worker 交接文件保留原报告；接受状态由 A 的 DISPATCH 维护。

## 实际接线

1. `composition.compose_understanding_context(records, policies)` 是有真实依赖的组装入口。生成一个 `IntentContexts`，由 Intent 和 Model 输入读取共用，不再由 Model 临时创建另一套无配置 resolver。
2. `run/context.py:RunContextSources` 读取真实 Run、取消账本、当前执行政策及已受理来源集合。输入必须属于该 Run 的固定原文/补充集合；同用户、同会话的其他输入也不能直接引用。固定数值版本从 SQL 读取，并复核当前删除状态。支持完整原文和 Unicode 字符位置的 text_span；UTF-8 hash 对应实际片段。不会 trim、归一化或用摘要替换原文。
3. `context/intent.py:UnderstandingRules` 只提供包内 `intent-understand-v1` 平台指令。单条已登记指令没有竞争规则，因此不额外调用模型评估冲突。项目、技能、用户规则继承和多条自然语言冲突评估仍明确不可用，不按词典处理。
4. `model/context.py:FixedModelWindow` 经既有 PolicyResolver 核对用户显式选择来源、固定配置、提供方当前撤销及执行权限。窗口来自实际 ModelCatalogEntry，不采用模型自报窗口，也不换模型。额外预留 512 的序列化估算空间。
5. Intent 调用 B 的规则装配与 Selector；显式传入 PreservationSpec，将所有原文和补充 Ref 设为必保留。输入、指令和输出空间放不下时返回 `context_insufficient`，不删要求。通用 ContextRequest/TaskFrame 的 requirement_ids、pending_action_refs 保留仍属于 MS-C2，当前不宣称已实现。
6. 指令集、空工具集、快照和来源绑定仍由已有的理解专用事务写入。manifest 的输入 Ref 携带实际 hash，依赖包含固定配置、用户模型政策和平台指令。输入修订在写入时 CAS 复核；Model 读取重新构建核对来源、规则版本和快照。
7. Provider adapter 在 Model 网关准入前计算完整原生 HTTP JSON 的 UTF-8 保守估算，包括消息、输出 schema、工具定义和生成参数；与已有估算取较大值，再加输出空间校验。不是精确 tokenizer，也不承诺模型供应商的实际计费量等于估算。
8. 修正 Model 工具建议的 RefKind 为 `configuration`，与 C 的 ToolRegistry/normalize 一致；受控模型响应已实际经过注册 schema 和参数规范化检查。没有因此注册产品工具或开放执行。

## 产品能力边界

- Container 增加 `context_components`，只表示理解所用组件可访问。`bindings.context` 仍为空；通用 ContextRuntime.build/快照 Composer 等待 MS-C2。
- 仍只有既有 24 项产品操作。没有新增 HTTP、模型可调用的空工具、管理员配置或依赖包；无数据库迁移。
- Runner 根/路径检查和 Tool 目录是已合入组件。签名、可信 IPC、真实配对、审批、派发、效果/结算仍未连通，Tool/Workspace Runtime 不绑定，flags 不改变。
- Run 外的输入预览、项目规则和任意资料 Reader 尚未注入；缺依赖返回不可用。当前适配器只消费已受理且活动中的 Run。
- 已完成的 Intent 回执可按既有规则重放。旧格式的未完成 understanding 快照不自动改写；重新解析不一致时拒绝，需要新的 attempt/turn。当前 frame 读取不依赖旧快照重新生成。
- D01 最终存储权威、D03 执行方式、D06 外部模型与语义验收仍待落实；本包没有自行决定。

## 验证与证据

先在三份组件合并后执行 **211 项**；随后针对上述实际接线新增 8 项 SQL/组装检查和 3 项原生请求估算检查，最终 **222 passed，0 failure/error/skip**。

```powershell
./ops/check.ps1 -WithPostgres
.venv/Scripts/python.exe ops/capture_environment.py
```

最终回执见 [JUnit](evidence/p0-tests.xml) 与 [源码及环境摘要](evidence/environment.json)。Ruff/格式检查通过；Mypy 覆盖 src 和实际 Runner 模块，共 75 个源码文件。Docker 和 PostgreSQL 在本轮实际可用，版本现场读取。测试使用真实 SQL、真实本机临时路径/junction 和受控 HTTP 回复；不作为外部 LLM、真实签名或 Runner 执行回执。

新增检查覆盖实际片段 hash、Run 来源限制、删除后的快照拒绝、政策撤销/取消、实际小模型窗口不足、窗口伪造、未知技能规则、组装实例共用以及 native body 超窗时禁止 claim/发送。既有输入修订、摘要不覆盖原文、并行幂等与结构输出回归继续通过。

## 接续与回退

- B 按 DISPATCH 的新固定 `ms-i1` 标签同步，开始 MS-C2；详细消费边界见 [A 的接线说明](../coordination/requests/A/MS-I1-adapters.md)。
- C/D 的首包组件已接受；MS-T2/MS-R2 仍待 MS-I2。A 接下来提供预算/审批/持久调用与 Runner 权威适配协议，未提供的真实依赖不能用测试替身代替。
- 代码回退由 A revert 接线提交或具体组件的 merge 提交，保留 worker 历史。没有执行用户项目、外部写操作或新增迁移需要撤销；已发生的历史模型费用不由源码回退撤销。
