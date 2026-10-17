# A12固定实验与多Run比较汇总接口

2026-10-17。A自有离线来源适配，准确源码见DISPATCH的`ms-i2m-a12-source`。C契约/评分器不变；不要求B/C/D同步或续包。

## 1. 事前固定入口

```text
python ops/conversation_experiment.py register --draft <草案.json> --output <新登记目录>
```

### ExperimentDraft `uaw.experiment-draft.v1`

| 字段 | 类型与约束 |
| --- | --- |
| schema_version/id | 固定版本/C Identifier；不能额外提供registered_at |
| suite | C Suite：1–128题，固定原文、rubric、材料、split、人审状态及版本 |
| limits | PolicyLimits：id、reviewer_required和4个错误率阈值；阈值沿用C的0–1十进制字符串 |
| candidate/baseline | VersionPin，两个不同ID；环境、model及provenance必须相同 |
| VersionPin.id/provenance | C Identifier；actual_candidate或controlled_fixture，不提升来源类别 |
| VersionPin.source_commit/environment_sha256 | 40位源码提交/64位环境摘要；不得以当前浮动HEAD代替实际运行版本 |
| VersionPin.model | C ModelPin：provider_id/version、model_id/version、configuration_sha256完整相等 |
| VersionPin.prompts | 1–64个C NamedHash，名称唯一；各自源码的实际提示词摘要 |

PolicyLimits的4个字段为`max_answer_error_rate`、`max_reviewer_miss_rate`、`max_unnecessary_block_rate`、`max_unsupported_execution_rate`。本接口不设置模型或产品默认预算，只固定实验的比较条件。

### ExperimentRegistration `uaw.experiment-registration.v1`

| 字段 | 类型与约束 |
| --- | --- |
| schema_version | 固定版本 |
| registered_at | CLI实际当前UTC；没有可供操作者回填的日期参数 |
| draft | 上述完整严格草案 |
| policy | C Policy；完全等于limits加registered_at、baseline_required=true |

输出`registration.json/suite.json/policy.json/registration-audit.json`，独占新目录。审计含规范摘要、待人审题ID、当前UTC记录的证明范围、0调用和未决定发布。允许未审工程草案不等于质量可以通过；登记时间和人审声明均非外部认证。

## 2. 完整结果汇总

```text
python ops/conversation_experiment.py assemble --registration <registration.json>
  --capture <候选题1原四文件目录> --capture <基线题1目录>
  [--capture <其余每题每版的目录> ...] --output <新汇总目录>
```

目录由操作者明确提供，不从回答/locator展开路径；每题每版一个原采集包，来自A10或合法审阅后的四文件。每包只含一题且没有内嵌baseline；候选ID必须与登记一致，不能为了汇总重命名原attempt或改写Observation。

验证顺序：总目录/文件量→C严格Reader和二次字节摘要→登记Case/VersionPin/Policy→原调用时间→完整attempt pins/归属→题目覆盖→新Manifest→C原评分。少题、重复目标、旧调用、修改条件、未知版本或摘要错误拒绝；失败题也必须保留原记录。已有回答审阅不得改写原已核准Case；存疑或修改须新登记。

限制：最多256目录、原四文件总64MiB，输出Observation16MiB/Reviews8MiB，C各对象/行/库存上限仍有效；内存读取后再次累计限制。任一来源错误在正常输出前拒绝；IO或最终C拒绝可能留下新目录现场，旧输入和旧输出不覆盖，不自动重试。

输出C四文件、原`registration.json`、逐采集原字节摘要的`assembly-audit.json`和原C生成的`quality-report.json`。观测/审阅行原样连接（仅缺末尾时补换行）；所有失败/unknown/重试/费用保留，模型建议不变成人审。

退出：register成功0（只说明登记成功）；assemble沿用C的0 passed/1 blocked/2输入或IO拒绝/3 incomplete。失败stdout只含固定operation error、安全code及异常类型，不泄露私有正文/路径。任何组件成功都不代表本人满意或发布门槛通过。

## 3. 实际状态和消费边界

本轮构造47节点通过，包含2题×2版完整来源、失败/unknown/重试/费用及A11已核准Case不变。实际已登记一个将来A9/A9a报告纠正工程试验，题目未人审，**未执行新模型/未汇总真实新旧结果**。原历史诊断不纳入本次预登记结果；完整16候选未登记为已审题集。

当前一个实验必须共用一个完整ModelPin；有不同生成参数/配置摘要的题目不可静默混合比较。register的时间是本机UTC而非可信外部时间戳，文件内容来源仍需操作者保存和审阅，接口不证明没有其他未提交Run。

[算法与目录](../../../implementation/MS-I2m-A12.md) · [实际回执](../../../implementation/evidence/ms-i2m-a12.json)。
