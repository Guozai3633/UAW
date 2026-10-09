# MS-I2h-A3：DeepSeek 真实模型与根 Agent 小样例验收

日期2026-10-09。Session A / E:/UAW / integration。本阶段只验收真实模型协议、任务理解与有界根 Agent；完整MS-I2h、P1及专业成果交付继续进行。

## 1. 实际配置来源

用户指定 `DeepSeek-V4.1-Flash`，并提供已登记的Windows凭据句柄。核对CredentialMetadata提供方为deepseek-live、受保护凭据可读取；没有打印或提交Key。官方名称对应API标识 `deepseek-flash`，真实鉴权GET /v1/models也返回该ID。[官方模型说明](https://api-docs.deepseek.com/news/news260910/)

通过实际ConfigurationService登记提供方、固定模型、开发手动审批和本机开发存储策略，再stage→validate→activate。只发布本机开发配置；没有替用户决定最终云端/本地历史方案。首次实际ModelRuntime成功调用的持久证据作为内部连接验收来源；连接同时推进provider.configs/providers版本，再发布引用新版本的model/configuration。

配置是https://api.deepseek.com/v1、显式Chat Completions、json_object加UAW本地schema校验、默认reasoning none。开发目录限制100000输入窗口/4096输出，低于供应商上限；角色仍遵守用户固定模型与Run预算。没有宣称供应商原生严格JSON Schema，也没有验证原生function-call协议。

## 2. 真正发现并修复的问题

1. **模型算错引文位置。** 首次办公样例的摘要正确，start/end却不对应原文，系统返回intent_quote_invalid，没有提交错误TaskFrame。现在模型只需给source_index和逐字text；Runtime用唯一精确匹配计算Unicode位置，不做模糊匹配、空白归一化或推断。重复/不存在/不完整引用仍拒绝；旧式显式span仍严格校验。原模型输出独立保留，SemanticParse持久化的是定位后的合法提案，原用户goal没有改写。
2. **学术回答被512 Token截断。** 首次学术根回答finish_reason=length，被拒绝为agent_decision_invalid。assemble_agent_runtime新增显式max_output_tokens，同步用于Context输出预留和Model请求，默认512兼容；实际学术复验配置2048，不自动重发旧失败/未知发送。
3. **连接状态缺真实入口。** 内部ModelConnectionAcceptance仅由管理员调用，读取实际证据owner的SQL invocation/output，核对成功终态、内容、提供方版本与实际模型名。不能靠调用者JSON或fixture声明active；旧Run固定版本不会自动迁移。
4. **JSON对象遗漏必填字段。** 2048 Token的学术复验返回完整回答，但漏了proposed_calls，仍被本地schema拒绝。根提示词增加三个必填key和空数组示例，保留严格校验，不在后端擅自补字段；另建明确复验Run，失败调用及费用记录继续保留。

## 3. 可复跑入口和范围

`ops/agent_probe.py`使用受保护本机开发用户、真实Run/Intent/角色/规则/Context/Model/Tool，未导入测试fixture。每次新逻辑验收显式给request-id；已有私有回执时拒绝重跑，未知发送不换ID盲目补发。输入最多8192 UTF-8字节，根步骤最多4步，输出可选512/1024/2048/4096 Token。

`--approve-text-inspection`是此次开发验收显式授权的脚本审批，只允许精确注册的只读text.inspect；核对原参数、资源与字节上限后，通过实际ApprovalService批准一次，再恢复原operation。它证明审批域链路，不代表真实前端人工点击或生产自动审批。

完整输入、ModelOutput、观察与原始API正文在ignored .data/私有Blob。公开回执只收样例、状态、Token、配置版本与摘要，不含Key/请求头。[实际证据索引](evidence/ms-i2h-a3.json)记录最终结果、首次失败、修复和测试批次；不把HTTP200或respond当Run.completed。

## 4. 保留的边界

- 办公待办、精确文本统计和小样本学术讨论是人工选择的开发样例，证明这些链路可运行，不能外推成专业质量通过率。
- 文本检查的数字/哈希按实际输入独立核验；办公条目和学术限制由A检查。尚无独立的通用任务完成/成果审阅服务，Run不标completed。
- 学术样例最终回答正确区分6/10和7/10的观测差异与总体优势，说明小样本、独立性和实验设计缺口，没有编造论文或检验数值；A按本样例接受。还不能据此证明完整学术Agent或专业成果质量，后续独立完成校验需要覆盖计算、证据和叙述一致性。
- 实际Token与缓存数读API；缺可核对账单/价格来源的费用保持pending，不记为免费或已结算。
- 实际多规则固定Model assessor、真实embedding、生产认证/IPC/用户确认、文件业务Tool和完整成果仍待接线。默认公开Agent/Tool/通用Context与flags没有开放，B/C/D已接受组件及原标签保持原样。
- 本阶段只执行受影响及跨模块检查；历史完整1077仍属于ms-i2g，A2的421覆盖也保留为历史，不改写成当前完整回归。

代码/证据提交：`20bb296052417743673fcb0b906226b79f5cbeb0`。固定阶段标签`ms-i2h-a3`包含后续发布状态；原worker开工标签不移动。
