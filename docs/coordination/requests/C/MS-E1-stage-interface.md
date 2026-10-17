# MS-E1 M1：严格离线接口和可运行阶段

2026-10-17，Session C，E:/UAW/.worktrees/tool / dev/tool。
共同基线 `ms-i2m-start / 1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe`，固定消费 `ms-i2m-a6-source / b16c69a92d81124c00fb859ce8123748f56df054`。干净原HEAD730a419c7b6558d239a701e3206b48a9cb353043，fetch/远端DISPATCH/ls-remote核对后依次快进，均曾HEAD等于标签。A6接线文档是随后发布的元数据，从origin/integration只读读取，未合浮动integration。
阶段源码 **49d3fbfeaa1ec5a3aedcb1becccd1d5fa4683eee**。M1后继续M2/M3，不等新包或真实模型；M4实际候选导出尚未提供，保持pending。

## 唯一类型源和精确接口

`src/uaw/evaluation/contracts.py` 是 **ms-e1.v1** 的唯一私有类型源，独立于shared/API/Runtime契约；`docs/implementation/evaluation/MS-E1-schemas.json` 导出Suite、Manifest、Observation、Review、Report五个精确JSON Schema（各自闭合$defs，extra字段拒绝）。M1只跑4条边界测试，不宣称完整质量设施已验收；原红/类型失败均保存，后续只修行为不随意改冻结字段。

```text
.venv/Scripts/python.exe ops/evaluate_conversation.py
  --suite <suite.json> --manifest <manifest.json>
  --observations <observations.jsonl> --reviews <reviews.jsonl>
  --output <new-report.json>
```

入口 `evaluate_files(suite:Path, manifest:Path, observations:Path, reviews:Path)->Report`；CLI不带账号/配置/自动导出/真实模型参数。退出0 passed，1 blocked，2严格输入或IO拒绝，3 incomplete。报告先完整写入同目录临时文件并fsync，再exclusive hardlink发布，任何已有路径不覆盖；无后台任务。无SQL，N/A；不碰原Tool/Runner/Run、锁或flags。

## 冻结输入形状

- Suite：schema_version/id/version/created_at/cases（1–128）。Case：id/version/split(revision或holdout)/category/prompt/rubric/evidence/review_status/human_verification。Rubric含expected_behavior、required_facts、allowed_assumptions、retained_requirements、critical。原材料/一手资料Evidence含id/kind/locator/captured_at/text/sha256/url；SHA绑定实际UTF8 excerpt/原材料，非整页hash。未经真正人工核对的一律needs_human_review且human_verification=null。
- Manifest：schema_version/policy/candidate/baseline（可null）。Policy含id/registered_at、预先声明reviewer_required/baseline_required及四个最大率（十进制字符串）。CandidateManifest含id/provenance(actual_candidate或controlled_fixture)、source_commit(40hex)/dirty/working_tree_sha256、suite_sha256/environment_sha256、完整provider/model/version/configuration_sha256、prompts(name/hash)、started_at/finished_at、inventory_complete、attempts与selections。dirty=true必须有工作树hash，不能假装干净。每候选最多2048attempt。
- AttemptPin：attempt_id/observation_sha256/output_sha256。Selection：case_id/answer_attempt_id/reviewer_attempt_id，缺结果显式null。完整库存声明不能只导出最后一次成功。
- Observation每JSONL行：schema_version/manifest_id/case_id/case_version/attempt_id/logical_request_id/attempt_number/phase/status/started_at/finished_at/active_ms/wall_ms/usage/output/reviewer/failure_code。phase为answer/reviewer/tool/preparation，失败/取消/unknown必须保留cause；重复attempt或同logical_request的重试序号拒绝。active不大于墙钟，UTC区间核对毫秒。
- Usage：input_tokens/output_tokens/model_calls/tool_calls均可null表示未知，不能填零；money十进制字符串或null，currency/billing_state(confirmed/pending/unknown)。confirmed禁止未知money。pending reservation绝不当账单，失败/重试仍计成本。
- Output：decision(reply/ask/tool/deliver/blocked/none)/原text/evidence(kind/id/version/hash)。ReviewerObservation仅给phase=reviewer，明确target_attempt_id/target_output_sha256/verdict(passed/failed/not_applicable/unavailable)。Reviewer本身也是实际attempt，费用不能漏掉。
- Review每行：schema_version/id/manifest_id/case_id/case_version/attempt_id/output_sha256/case_sha256/basis/reviewer_id/reviewed_at/evidence_sha256/evidence_reviewed/labels/notes。basis=human_evidence_review、model_suggestion或controlled_test。Labels分别给answer_correct/unnecessary_block/unsupported_execution/requirements_preserved/acceptable（均可null）和critical_error。字符串/关键词不评分，model_suggestion不替代独立结论。

所有nullable字段也须按schema明确提供；JSON输入不做bool/int/字符串强转。duplicate JSON key、NaN/Infinity、坏UTF8/过深/超量拒绝；只读四个显式文件，URL/locator/ref均当数据，不联网、不展开附件/路径。Suite/Manifest各2MiB，observations16MiB、reviews8MiB，JSONL每行256KiB/最多4096条；输入原字节hash另记Report.input_sha256。

## Hash与报告语义

`digest(x)` = UTF8(sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',',':')的规范JSON)的SHA256。A先构造严格模型.wire()再hash：Suite整体、Case整体、Observation整体、Answer整体分别绑定，不能用只对text的hash代替Output hash；纯来源text.sha256为实际UTF8字节。没有自动Unicode归一化。

Report固定保留完整Manifest、四文件原字节hash、候选/基线所有attempt摘要、未归属/未通过binding观测及单列unverified_costs、逐项integrity_issues、独立质量率/分母/N/A、全尝试计时和费用，comparison及release_gate。human_verification明确offline_assertions_only_not_identity_authentication：CLI验证人工声明的绑定，不能认证人的行为，不授予产品发布/任务完成权限。C不生成human已审声明。

CandidateReport包括attempt/failure/cancelled/unknown/retry计数、每个实际attempt及原usage、selected/acceptable/人审/受控/model建议计数、答案错误/Reviewer漏判/无谓阻断/无证据执行/保留要求丢失、active总和/attempt_wall_ms_sum/实验墙钟、各用量known_total及unknown_attempts。多attempt墙钟和不冒充用户总等待；实验墙钟来自manifest区间。成本按币种分confirmed/pending/unknown_estimate和未知金额数；零可接受数或账单未完成时单位可接受输出成本为null。

## 可执行样例和阶段实测

`tests/fixtures/evaluation/ms-e1-interface`提供四文件；明确controlled_fixture、not-a-real-model，非真实输出，无人工审查。按README命令输出ignored `interface-report.json`，实际退出3/incomplete，pending USD0.02、Reviewer N/A、未知答案错误率null。再次同路径退出2，原字节保留。
M1：4单元/CLI子进程通过；7源码/脚本mypy通过，ruff通过。红测试缺新模块/CLI的初始失败、第一次类型检查10条错误、格式前静态提示保留在tests/.artifacts/C/MS-E1，未当产品失败或真实模型质量结果。M2样本与M3完整统计/注入/hash/费用/比较边界继续，现阶段不声称正式release可passed。

A导出actual_candidate时保留全部attempt、真实失败/用量和pending费用，给精确源码、model/config/prompt/environment/suite hash及实际UTC区间；先冻结Policy再实验。真实独立人工核对从实际人员提供，不能从modelpassed复制，也不能把此fixture改provenance当生产来源。实际文件到达后C离线运行M4；无来源不请求A凭据或自行发模型。
