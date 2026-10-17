# A10 只读采集接口与 C/MS-E1 消费

2026-10-17；准确源码发布后见 DISPATCH 的 `ms-i2m-a10-source`。这是 A 的来源适配，不是新的 worker 包，不要求 B/C/D 同步。

## 命令接口

```text
python ops/capture_conversation_evaluation.py
  --config <原受保护settings.toml>
  --environment <固定运行environment.json>
  --case <严格Case对象JSON>
  --policy <严格Policy对象JSON>
  --run-id <明确终态Run>
  --candidate-id <本次候选ID>
  [--answer-attempt-id <明确最终完整答案的原调用ID>]
  [--repository <可解析准确Git提交的仓库>]
  --output <尚不存在且父目录已存在的目录>
```

| 输入 | 结构与约束 |
| --- | --- |
| config | `Settings`；只从操作者已配置的数据库和开发主体读取，不接受模型传入身份；凭据使用原受保护环境，不打印或复制 |
| environment | 本轮沿用的 H02 本机清单；必需 `backend_source`、`backend_switched_at`、`dependency_inventory_sha256`、`dependency_lock_sha256`、`settings_sha256`；同级 `runtime/` 逐字核对源码，不修改环境文件 |
| case | C `Case`，原始/追加文字必须逐字对应；rubric、来源、人审状态保持真实；不从回答反推已验证标准 |
| policy | C `Policy`，真实登记时间和门槛；不会把事后政策改成事前登记 |
| run/selection | 归属用户、未删除会话、终态、conversation-v1且无Tool效果；选中答案须原决策及当前input_revision；全失败允许不选择 |
| output | 独占新目录，不覆盖；权限依据是操作者本机执行，不是产品路径读取授权 |

成功 stdout 只有 `captured/attempts/human_reviews/new_model_calls/runtime_writes`，退出0；失败输出固定 `capture_rejected` 与异常类型，退出2，不泄露 SQL 参数、原文或凭据。具体异常保留在开发调试而非用户聊天消息；不自动重试或修补来源。

## 输出及消费

| 文件 | 作用 |
| --- | --- |
| suite.json | C `Suite`，一个明确样本及原Case状态 |
| manifest.json | C `Manifest`，准确候选/固定模型/配置、完整attempt pins、显式selection；本版本baseline为空 |
| observations.jsonl | 全部调用逐行 C `Observation`；实际代码/用量/时段；Reviewer精确绑定原输出 |
| reviews.jsonl | 空文件；绝不从模型passed生成human_evidence_review |
| audit.json | 原记录版本/摘要、模型请求配置、源码证明范围及局限、导出器字节指纹；仅本机保存 |
| review.html | 无脚本、转义后的待核对材料，没有人审写入/用户接受功能 |

独立评分直接使用未修改的 C 命令：

```text
python ops/evaluate_conversation.py --suite <suite.json> --manifest <manifest.json>
  --observations <observations.jsonl> --reviews <reviews.jsonl> --output <新report.json>
```

沿用0通过、1阻断、2输入拒绝、3未完成；本次实际门槛为未完成。接口严格结构以 `src/uaw/evaluation/contracts.py` 和 [C交接](../C/MS-E1-final-wiring.md) 为准。

边界：最多512条记录；有缺失主动时间的调用整包拒绝，不少导调用、填零或复用预留费用。只有实际捕获任务的库存完整，不能扩称整个产品或所有历史完整；环境源码归属为原操作者启动记录加字节校验，无逐Run不可变版本证书。题集人审、事前登记、实际新旧版本对比与H02本人体验还需独立完成。详细算法与真实结果见 [A10实施](../../../implementation/MS-I2m-A10.md)。
