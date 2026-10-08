# MS-C6 最终接线与读取成本边界

固定开发基线 ms-i2h-start / f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8；阶段源码17e468279586638c543e20b20acb0325e4d28797，阶段handoff a19188c47b4f2d2fedaad89bb0776215d0d649f6。最终源码和实测索引见B handoff。只改B允许路径；不改Model/Run/shared/schema/锁/flags/组装根。

## 构造和消费

```python
# A可信组装根：沿用已发布实际当前Run/固定Model链和真实来源。
inputs = RegisteredContextInputs(
    controller=actual_authenticated_service,
    records=actual_records, blobs=private_owner_blobs,
    transactions=actual_transactions,
    runs=RegisteredRunContextSources(actual_run_execution_sources),
    tool_validator=actual_registered_tool_set_validator,
)
reader = RegisteredContextReader(inputs)
provider = RegisteredRuleProvider(inputs, assessor=actual_fixed_model_assessor)
# A将reader/provider/RegisteredCompositionAuthority(inputs)注入已有ContextComponents。
# actual_fixed_model_assessor 使用 RegisteredRuleAssessor.assess 签名。
# 缺实际assessor的多规则请求明确 unavailable；受控SQL评估器不可用于生产。
```

规则建议再校验与错误、取消语义详见[阶段接口](MS-C6-stage-interface.md)。正文/级别/scope/完整Ref/顺序/targets固定，actual Runtime权限独立复查。材料只保留数据身份。A的评估输入路由应消费已固定候选数据，不能递归进入同一个多规则GenericModelInputs评估；purpose沿用agent_step，不新增公共purpose。A须维持当前Model adapter、真实认证/session、非空工具validator以及最终Model派发复查；B不开放登记HTTP或flags，不直接调用私有provider。

## 有界读取调整

`RegisteredContextInputs.inspect(ctx) -> tuple[RegisteredRecipe, tuple[Ref,...]]`为B内部当前读取批，不是授权快照或公共RecordStore批读port。authority.resolve和评估等待前后复查使用它：

1. 当前_guard/Run/model/policy/full owner/binding/input set在批前实际读取；配方/工具三份记录与seal/owner、实际原文及patch读取。
2. 选择的实际材料/规则两遍读取，blob UTF-8/hash/正文、版本、信任分类和owner/seal分别校验；实际Run Reader仍自行authorize。
3. 配方/非空工具验证源在两遍间以及最后一遍后重新读取，原文集合复查，最后再次_actual access并与批前binding/input set比对。没有缓存权限、Reading、规则建议或输出，批的局部数据随调用结束丢弃；ctx期限统一有界，task取消传播。

避免每个内部材料read都递归展开整条Run authority，但每个公开read/recipe/current仍保留前后实际权威检查；inspect的私有辅助方法不作为外部免鉴权入口。sources.Reader.check/read、snapshot提交前/事务内/提交后复查、GenericModelInputs末尾复查保持。材料/规则/工具在已覆盖await注入点的变化由对应当前边界拒绝；独立外部源不因SQL成为可原子授权，A派发前仍须查当前固定模型/权限。

读取候选最多64；批唯一source最多128，单来源正文最多64KiB，recipe/语义metadata最多256KiB。严格B scope/epoch和实际Run，不跨主体复用。

## 缓存可选/关闭

```python
# 默认关闭；Components与GenericModelInputs可选择同一个纯计算cache。
cache = None
# 可选：PureComputationCache(max_entries=128, max_bytes=2097152)
# 显式关闭：PureComputationCache(max_entries=0, max_bytes=0)
model_inputs = GenericModelInputs(actual_components.composer, cache=cache)
```

仅格式化/序列化/token估算复用；当前Reader/assessor/authority、规则和工具版本、窗口/取消以及最终复查不省略。不得把模型建议、授权或撤销状态存入此cache；不宣称provider prompt cache或Token节省。

## 实测定义

自身ignored `tests/.artifacts/B/MS-C6/read-cost.json`保存每边界RecordStore.get按namespace分布、Reader.check/read及registered body/current gate次数、assessor次数、单调计时、实际消息hash/完整输入估算和撤销拒绝。覆盖registration/read/recipe/authority.resolve/verify/rules/build/ModelInput/reference、cache冷/暖/关闭及撤销后ModelInput。

比较策略为测试内`LegacyExpansion`复现阶段read→recipe/current/read→recipe/current的公共展开结构，对照最终inspect批读取；两者使用同一实际A RunExecutionSources/权限/固定模型、SQL记录和FS blob，不是memory假SQL，不是完整旧commit二进制基准。两个build使用不同operation_id以避开幂等重放；相同实际来源/语义metadata必须产生相同ModelPrompt、InstructionSet和引用正文。SQL事务内部tx.load不算RecordStore.get，Reader port次数与内部body次数分开统计。单机开发环境时延不是生产SLO；顺序运行成本比较，真实受控评估器不证明LLM语义质量。

实测相同材料、两条实际 user_current 规则、显式空工具、同一固定模型与当前A权威，Python3.14.6、B PostgreSQL55433；评估器为显式受控建议，未发送LLM请求。以下单次计时仅为该开发环境结果：

| 边界 | 阶段式展开 get / 秒 | 批读取 get / 秒 | assessor 次数（两策略） |
| --- | ---: | ---: | ---: |
| authority.resolve | 547 / 2.867160 | 222 / 1.263609 | 0 |
| authority.verify | 547 / 3.184992 | 222 / 1.464796 | 0 |
| rules | 1917 / 11.234387 | 1267 / 6.903167 | 1 |
| build | 17205 / 101.894222 | 11088 / 65.759718 | 2 |
| ModelInput | 14515 / 70.807426 | 9427 / 55.694873 | 2 |
| read | 59 / 0.416662 | 59 / 0.311438 | 0 |
| recipe | 65 / 0.350031 | 65 / 0.292041 | 0 |
| reference | 566 / 2.851286 | 566 / 3.222872 | 0 |
| 撤销后的 ModelInput | 262 / 1.697837 | 100 / 0.453367 | 0；均 resource_missing |

build get 减少35.55%，ModelInput get减少35.05%，通过减少重复展开；仍存在较高当前权威读取成本，没有生产延迟达标或Token收益结论。cache冷/暖/零容量各9427 get、assessor2次、相同ModelPrompt，分别54.496503/51.853526/50.224263秒；单次计时不证明cache延迟收益。此cache只复用纯计算；原缓存回归另验_format次数和变异隔离。

最终验收以真实不同节点回执和失败修复索引为准，不把收集/无数据库skip当通过，不把组件测试当P1/P4整轮accepted。A审阅并合入后处理公共接线和跨模块验证；B本包交付后停止，不自动扩包。
