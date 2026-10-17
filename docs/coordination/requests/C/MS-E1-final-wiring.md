# C/MS-E1 最终消费说明

2026-10-17；E:/UAW/.worktrees/tool / dev/tool。
共同基线ms-i2m-start / 1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe，固定消费ms-i2m-a6-source / b16c69a92d81124c00fb859ce8123748f56df054；准确核对并顺序快进，无浮动integration/rewrite。

阶段M1源码49d3fbfeaa1ec5a3aedcb1becccd1d5fa4683eee / 文档5096a2c5816532efff729c612c3004a5723bf982；M2/M3源码36507dda7fc03d59a465c2696928b5395ed1fc27；评分器指纹/初版受控报告55c3e99b28026706846ef13febaaf1f832170fdd；最终源码 **c8dba72e3a5dc707911c841e3cf6c3bf781d9ac3**。独立handoff随后提交。

精确v1私有字段见[阶段契约](MS-E1-stage-interface.md)，类型源src/uaw/evaluation/contracts.py，生成schema在docs/implementation/evaluation/MS-E1-schemas.json。M1冻结字段未改，72节点含schema稳定性检查；新增evaluator_source只利用既有NamedHash元数据，报告四输入原字节hash外给实际评分器源文件/依赖版本指纹，不能由候选自报。

完整算法/分母/失败边界/真实命令：[MS-E1实施](../../../implementation/evaluation/MS-E1.md)；16候选、split和实查primary source：[样本说明](../../../implementation/evaluation/MS-E1-candidates.md)。所有候选needs_human_review，human_verification=null；C没有生成真正human_evidence_review。受控labels/model verdict只证明计算，不计真人决定或实际模型质量。

A导出：1）固定Suite及其完整规范hash，先真正人工核对关键rubric/来源并按版本保留；2）Manifest记录精确source/dirty/prompt/environment/model/provider/config hash、先登记Policy、完整尝试库存和最终Selection；3）所有失败/成功/重试/Reviewer/tool观测与实际时段/用量，unknown维度显式null，pending预留不充确认账单；4）独立review绑定Case/Output完整hash和来源审查，model建议用model_suggestion，不复制passed造人审。C不替A导出私有原记录或访问其账号/密钥。

命令固定：`python ops/evaluate_conversation.py --suite <suite.json> --manifest <manifest.json> --observations <observations.jsonl> --reviews <reviews.jsonl> --output <new-report.json>`。0=完整门槛passed，1=blocked，2=输入/IO拒绝，3=incomplete。任何旧输出都不覆盖；新来源/评分器比较必须新报告路径。

真实组件验证72不同离线节点通过，ruff/format16文件及mypy7源码/脚本通过；原26条failure/error（18红测试、8批次/夹具记录）和类型/补丁诊断保留在tests/.artifacts/C/MS-E1及机器索引，SQL N/A、真实模型/实际人审/实际候选对比0。新受控报告MS-E1-controlled-report-final.json明确blocked/provisional；旧阶段报告保留，题集空输出报告incomplete，不以零错误过门槛。

M4 **actual evaluation pending**：尚无A准确实际候选/基线四文件和真正人审；A6输出明确是受控HTTP测试，不能冒充真实DeepSeek。默认CLI只读离线文件，另读取本评测包自身源文件计算版本指纹，无后台任务、关闭不需回收Runtime资源；缺输入拒绝，四文件可空观测但结果incomplete。源码不被产品Tool/Run/Runner/Agent引用，无公共DTO/依赖/flags/Tool时间port修改。

A可现在审阅M1–M3并消费固定schema；实际来源到达后再运行M4，不能把harness72项当事实质量或H02 accepted。A逐阶段合入/处理公共接线，C本包结束保持干净停止，原Tool交付/失败/费用/last_full完整保留。无需另发跨会话消息。
