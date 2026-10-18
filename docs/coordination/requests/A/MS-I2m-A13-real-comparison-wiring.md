# A13：隔离真实报告纠正与完整比较接线

2026-10-18。范围为A拥有的运行探针和离线来源适配。C格式/评分器、B页面、D时钟、公共契约、依赖锁及产品flags均不修改。[实际结果与限制](../../../implementation/MS-I2m-A13.md)。

## 1. `ops/registered_report_probe.py`

| 输入 | 必须满足 |
| --- | --- |
| `--environment` | 原操作者环境JSON，含backend_source、backend_switched_at、依赖/settings摘要、明确隔离scope；同目录有固定runtime源码 |
| `--config` | 原Settings文件；数据库地址由受保护环境提供，keyring引用不展开到命令或回执 |
| `--registration` | A12原registration.json；恰好一个Case、显式一次纠正 |
| `--registration-sha256` | 该登记对象的规范摘要，逐字核对 |
| `--variant-id` | 登记的candidate或baseline准确ID |
| `--report` | 新的私有完整回执文件，首次排他创建；后续只更新该诊断文件 |

输入Case用精确分隔符`\n\n用户追加要求\n`保存两段原文。缺失、多次或空段拒绝；这是具名试验协议，不是产品按关键词判断用户需求。探针要求UAW模块从同目录固定runtime导入、原用户库存为空、无本机安装；同一用户模型与实际时钟显式装配。

```powershell
# 使用已核对的依赖Python和明确的单版目录，数据库环境已在受保护进程中设置。
$env:PYTHONPATH = "$variant/runtime/src;$variant/runtime/apps/local_runner"
& $fixedPython ops/registered_report_probe.py `
  --environment "$variant/environment.json" --config "$variant/settings.toml" `
  --registration "$experiment/registration/registration.json" `
  --registration-sha256 $registrationDigest --variant-id $variantId `
  --report "$variant/live-report.json"
```

返回0表示具名工程场景观察成功，1表示诊断失败，2表示准备输入拒绝；都不表示人审或产品发布通过。stdout仅状态/Run/调用数，详细原用户输入、回答、全部owning_evidence仅入私有report。失败、取消及费用不能删除。最多4调用，无自动重试；探针结束只取消自己未终态的诊断Run。

## 2. 环境摘要与失败核验

`environment_hash(environment)`始终固定依赖库存、锁及settings三个摘要。旧环境不增加字段，摘要保持；存在`evaluation_execution_scope`时，将其规范摘要作为`execution_scope_sha256`进入环境摘要。本轮scope明确为手动原队列、各版空数据库、各版空blob、无本机安装。实际命名空间地址不同不代表配置可以随意变化；变更比较条件须重新登记。

`prepare_bundle`只在已证明Reviewer对应原回答时保留target_attempt_id和target_output_sha256；Reviewer失败仍保留该绑定、failure_code以及`verdict=unavailable`。Selection记录真实失败Reviewer，C原算法将其统计为N/A，不能据此认定零漏判。无依据的绑定仍拒绝。

## 3. 原CLI消费顺序

1. 新环境、原固定源码和完整模型条件在A12 `register`登记后才能调用模型。时间为本机UTC，不能回填或宣称外部认证。
2. 每版运行一次探针，原队列产生所有Model尝试及正式成果/纠正记录。
3. 使用integration中的A10采集器和每版固定environment/config，指定原Run、准确variant-id和第二次完整回答的attempt ID。只读原数据库，不清除失败或补造审阅。
4. A11 `prepare --source <captured> --output <new-review-directory>`准备空白表；真正人工输入后才能显式import。受控评分不冒充真人。
5. A12 `assemble --registration <registration.json> --capture <candidate-dir> --capture <baseline-dir> --output <new-dir>`核对全部条件/库存后调用原C评分器。

本轮两个目录各4调用，最终汇总8调用，退出3/incomplete/incomparable。基线第二次生成可供事实审阅，但随后核验失败，不能标为成功交付。两版最终纠正库存均applied；诊断候选成功后取消收尾，不代用户接受。

## 4. 固定结果与剩余工作

登记摘要`96ca9f9a9483b1a3b46e5321c57d332c6c433889b31d8b82e202250336f33ca8`；准确源码及逐调用脱敏摘要见[机器证据](../../../implementation/evidence/ms-i2m-a13.json)，最终A源版本以DISPATCH页首为准。私有两个captured与review-ready目录及combined/quality-report.json均保留；原回答不提交Git。

9个定向节点通过不能替代事实评审、H02本人重测、本机或Tool跨墙钟验收；未更新last_full，未为B/C/D派新任务。
