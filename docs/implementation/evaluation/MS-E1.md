# MS-E1：离线独立质量门槛组件

2026-10-17，C / dev/tool。组件开发完成；**实际候选/基线与真正人工核对未提供，M4实际实测pending，P1-15/H02不据此接受。** 没有模型/账号/SQL调用或新增真实费用。

## 固定来源与交付

原worktree `E:/UAW/.worktrees/tool`，干净原HEAD730a419c7b6558d239a701e3206b48a9cb353043。fetch origin --tags后只读远端正式DISPATCH、ls-remote核对，依次快进 `ms-i2m-start / 1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe` 和 `ms-i2m-a6-source / b16c69a92d81124c00fb859ce8123748f56df054`；各时点HEAD与标签一致。未合浮动integration/reset/rebase/stash，旧C提交/回执保留。A6接线元数据在随后文档提交，从origin/integration只读消费；没有因源码标签内缺文档再次停工。

- M1源码 **49d3fbfeaa1ec5a3aedcb1becccd1d5fa4683eee**，精确接口文档 **5096a2c5816532efff729c612c3004a5723bf982**。
- M2/M3题集/完整统计 **36507dda7fc03d59a465c2696928b5395ed1fc27**。
- 实际评分器指纹/受控报告 **55c3e99b28026706846ef13febaaf1f832170fdd**。
- 最终源码（含显式Reviewer绑定加固） **c8dba72e3a5dc707911c841e3cf6c3bf781d9ac3**。

类型唯一源为 `src/uaw/evaluation/contracts.py`；[五个完整schema](MS-E1-schemas.json)自M1冻结，最终测试核对未漂移。该协议是C独立离线文件格式，不是共享HTTP/Runtime DTO，不用于生产权限。

## 文件、算法和边界

| 文件 | 责任 |
|---|---|
| evaluation/contracts.py | strict/frozen类型、显式nullable、UTC/范围、无强转、完整尝试/独立review及报告 |
| evaluation/io.py | bounded UTF8/JSON、重复键/非有限数/深度拒绝、规范hash、exclusive原子报告发布 |
| evaluation/reader.py | 仅四个显式输入文件、JSONL限制、重复attempt/同请求序号/review拒绝 |
| evaluation/metrics.py | 全部费用/未知维度、足够精度Decimal、精确分子分母、N/A |
| evaluation/runner.py | 原样本/观测/输出/review绑定、独立评分/版本对比/门槛、评分器来源指纹 |
| ops/evaluate_conversation.py | 固定CLI、可读有界诊断与0/1/2/3退出码，无账号/模型/导出/写工具 |

`evaluate_files(suite:Path, manifest:Path, observations:Path, reviews:Path)->Report`。只读开发者明确给定的离线数据文件；locator/URL/ref不展开、不联网、不执行答案。另只读本组件自身六个安装源文件计算evaluator_source，附Python/Pydantic版本；计算前后指纹不一致则拒绝。报告的input_sha256在四个原文件字节hash外，额外有 `NamedHash(name="evaluator_source",...)`，不改M1 schema，不让候选自报评分器版本。候选source/model/config/prompt/environment/suite固定，评分器与候选版本分开。

规范JSON SHA256为sort_keys=True、ensure_ascii=False、allow_nan=False、紧凑separators的UTF8。Case/Suite/Observation/Answer完整结构分别pin，来源text另以UTF8字节hash，不混作全文或整页hash。失败/未知output=null的pin必须也是null。原输入文件字节hash与规范对象hash不同，均保留。

JSON单记录2MiB、深度48；Suite/Manifest各2MiB，observations16MiB、reviews8MiB，JSONL每行256KiB、最多4096行；单候选库存最多2048尝试，题集1–128条。Strict schema拒绝extra字段/bool当int/浮点money/非UTC/时间倒退/active大于wall/失败无cause；不静默选择重复键或重复attempt。报错不输出原正文值。

完整报告先在目标同目录临时文件写完/fsync，再hardlink exclusive发布；旧输出路径存在即退出2，不覆盖旧输入/报告。真实并发两个CLI子进程验证单赢家。没有后台重试/进程、数据库或HTTP，不影响Runtime flags/固定用户模型。

## 质量、费用和比较口径

语义只消费绑定正确且明确证据已审的独立Review；basis=model_suggestion不作为答案真值。controlled_test仅验证计算，所有相关率标provisional，不能支持正式发布。人工声明必须由实际人员提供；CLI只验证其hash/版本绑定，**不认证人的行为**，Report.human_verification明确offline_assertions_only_not_identity_authentication，不授权发布/Task完成。C未生成human_verified样本或human_evidence_review记录。

| 指标 | 分子 / 分母 |
|---|---|
| answer_error | 独立标签answer_correct=False / 该标签非null的已选择输出 |
| reviewer_miss | 对已独立确认错误答案仍passed的实际绑定Reviewer / 此类错误答案中实际passed或failed的Reviewer |
| unnecessary_block | 独立标签unnecessary_block=True / 该标签非null的输出 |
| unsupported_execution | 独立标签unsupported_execution=True / 该标签非null的输出 |
| requirements_lost | 独立标签requirements_preserved=False / 该标签非null的输出 |

Reviewer未启用、failed/unavailable/not_applicable或没有错误答案样本使对应漏判分母为0时，保留N/A/null，绝非0漏判。reviewer_required在实验前Policy登记；为false不强加每条请求固定自评，为true分母缺失不能通过。显式选了Reviewer但不存在/错phase/错case/target/output则是绑定错误，不能伪装成未启用。报告另列NA例数。

伪造资料或输出hash时不计算相应语义分母；观测binding不通过的费用单列unverified_costs，未归属manifest观测及费用也保留，不隐藏或当确认账单。矛盾acceptable标签不制造接受分母。关键Case预登记critical：独立确认答案错误、无证据执行或保留要求丢失即阻断，不能靠普通阈值放行或漏填critical_error绕过。指标阈值用精确分子与分母交叉相乘；八位展示小数不参与放行决策。关键/阈值错误优先blocked，缺人工等原因仍保留；信息缺失、零可接受数、零必需分母为incomplete。

所有answer/reviewer/tool/preparation的成功/失败/取消/unknown与重试均保留。各用量给known_total/unknown_attempts；费用按币种独立列confirmed/pending/unknown_estimate及未知金额/账务数。pending预留不是账单，unknown不回填零；局部64位十进制精度防大额累计丢小数。不改全局Decimal环境。

active_ms为全部观测主动时间和，attempt_wall_ms_sum不冒充用户总等待；experiment_wall_ms来自固定manifest实际起止区间。声明库存/时段/hash不符保持incomplete。单位可接受输出成本只有接受分母正且该币种全账单确认时才计算，否则null。

比较要求同suite/environment/完整model pin/provenance且无结构性来源缺口；不同prompt/source是候选被比较项。不可比返回明确原因、无delta并独立阻止候选通过。合法比较分别给各质量率、时间、失败/重试/尝试、完整已知用量及逐币种已知confirmed/pending/unknown差异；任一质量分母N/A则该差异仍null，不做无意义比值。基线的已知语义错误保留在基线报告，但不污染候选门槛；坏基线不被“洗白”，也不把旧错判成新错。受控比较只证明计算，不是模型质量改进声明。

## 样本与可运行报告

[16条候选说明](MS-E1-candidates.md)：revision/holdout各8，办公3/学术2/技术4/缺材料2/合理歧义3/纠正2。办公和学术材料、其余自含规范为本开发代理草拟的synthetic数据；文中“构造材料”不是人类已核对或真实业务资料。原TCC/ZooKeeper概念错误纳入但无专用关键词规则；所有候选 **needs_human_review**，没有自动标签真值。实际打开官方资料的位置、UTC及选取中文摘要hash都在每条Evidence，摘要hash不是网站原HTML或人工审核证明。

- `tests/fixtures/evaluation/ms-e1-interface`：单条构造观测，pending USD0.02、无review，实际CLI退出3/incomplete。
- `tests/fixtures/evaluation/ms-e1-candidates`：16条题集但观测/review为空，最终实际CLI退出3/incomplete，0运行不代表0错。
- `tests/fixtures/evaluation/ms-e1-accounting`：[最终受控报告](MS-E1-controlled-report-final.json)来自三条明确构造观测（失败→重试错误6→构造Reviewer passed），CLI退出1/blocked，已知错误与漏判各1/1/provisional；confirmed0.07/pending0.02均是构造金额，不是新增账单/实际模型费用。旧[阶段受控报告](MS-E1-controlled-report.json)原字节保留，grader fingerprint不同，不覆盖或冒充最终来源。

```powershell
.venv/Scripts/python.exe ops/evaluate_conversation.py `
  --suite tests/fixtures/evaluation/ms-e1-accounting/suite.json `
  --manifest tests/fixtures/evaluation/ms-e1-accounting/manifest.json `
  --observations tests/fixtures/evaluation/ms-e1-accounting/observations.jsonl `
  --reviews tests/fixtures/evaluation/ms-e1-accounting/reviews.jsonl `
  --output tests/.artifacts/C/MS-E1/new-controlled-report.json
```

路径必须是新文件；退出0 passed、1 blocked、2输入/IO拒绝、3 incomplete。组件工程命令退出0与报告发布门槛不是同一结论。

## 验证、原失败及未完成项

最终 `.venv/Scripts/python.exe -m pytest tests/unit/evaluation --junitxml=tests/.artifacts/C/MS-E1/final-evaluation-v2.xml`：**72个不同离线节点全部通过，0 failure/error/skip，3.43秒**，包括真实CLI子进程/并发、固定schema稳定、16样本待审、重复/错hash/跨case/损坏源/注入、独立Reviewer N/A/漏判、全失败/重试成本、精确阈值、大额小数与版本不可比。没有跑Tool/历史SQL/全仓，也不累加阶段4/21/5/66/67/69/70成为新节点。

ruff/format **16文件** 通过（6组件文件+1CLI+9专属测试/fixture），mypy **7源码/脚本** 通过。环境为原uv.lock冻结91包，未装新依赖。独立SQL **N/A，未运行且本包无需**；本轮真实模型调用/真人样本核对/实际候选比较均0。

所有原始回执ignored `tests/.artifacts/C/MS-E1`，verification-index.json/build_index.py从真实XML去重、列每个最终节点、全部XML SHA256及 **26条原failure/error：18条预期TDD红测试、8条整批回归/setup/teardown记录**。后者来自两次1失败/3error：巨型bytes参数自动生成pytest node id超过Windows32767环境变量限制，及候选隔离修复漏保留unknown_manifest原因；改有界ids并修正后全部复验通过。首个参数名补丁断言失败、命令继续重复旧失败，原回执保留；其后添加guard并精确修复。对巨型日志Get-Content扫描滞留的两个已核实C进程精确停止，未停止其他worker/模型进程；pytest本身当时早已完成。

预期红测试覆盖缺新模块/CLI、损坏资料误入语义分母、不可比原因/关键阻断、旧错污染新版本、矛盾接受、大额累计/阈值舍入、critical绕过、评分器来源缺失与Reviewer引用；初始mypy10条错误、静态格式提示也保留。不是隐藏失败或更改真实期望来“通过”。M1 schema与原Source/锁/shared/Tool/Runner/Run由scope guard核对未改。

**M4：等待A从准确固定候选与历史基线owning记录导出四文件（含全部attempt/原失败/用量/pending），并提供真正独立人工核对。** 本仓公开H01-I02/I03错误记录仅用来设计反例，不是完整真实输出/manifest，不能替代该导出。未读取A凭据/本人会话、不自行调用模型、不重放写操作；未装管理员HTTP。待来源后使用新报告路径比较，不改旧样本/旧报告。现在只交组件开发与受控计算回执，实际质量/本人体验/发布/P1-15/H02门槛保持pending；包后停止，不因A6 Tool时间提案扩包。
