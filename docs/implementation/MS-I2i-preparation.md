# MS-I2i：四session开工准备

日期2026-10-09。本次仅准备下一轮安排与文档/计划生成器；运行源码来源为 `ms-i2h-a3 / 3e5917d9b8dffa767f403c3d71a1884327db8f70`。运行能力与测试回执没有因发包增加。

安排准备提交：**af93ca649f848cf50b5373ce143f25f7ff5017b8**。开工标签 **ms-i2i-start** 包含随后状态元数据；以解析出的标签commit同步。atomic发布后核对远程integration与标签，详见[派发表](../coordination/DISPATCH.md)。

## 已准备的包

| Session | 包 | 范围 | 状态 |
| --- | --- | --- | --- |
| A | MS-I2i | 当前模型评估、实际文本成果、完成校验/提交及逐包集成 | 已发布待开工 |
| B | MS-C7 | 上下文读取提速、可选批读、来源/结果等价及性能回执 | 已发布待开工 |
| C | MS-T2f | Decimal计算、JSON检查、多executor/verifier、实际结果与恢复 | 已发布待开工 |
| D | MS-R2f | Windows双进程IPC、独立身份/活连接源、只读临时根传输与恢复 | 已发布待开工 |

详细策略/接口/输入输出/允许目录：[完整分包](../coordination/requests/A/MS-I2i-parallel-packages.md)。四份开工消息：[NEXT_WAVE](../coordination/NEXT_WAVE.md)。状态、标签与实际SHA：[DISPATCH](../coordination/DISPATCH.md)。

## 独立与协作

- 三个worker消费同一固定基线和原已接受组件，不读另一个开发分支。B/C/D各自模块错误与SQL/OS回归自己完成，A做消费者、公共适配和跨模块验收。
- M1尽早固定阶段接口，M2提交源码后继续M3/M4；A收到可审阅SHA就处理。B批读SQL适配由A优先提供，B原get兼容策略和测量独立继续；C/D不等待它。纯文本/计算成果链不等待本机通道。
- A新增成果文件的精确归属已列入plan；D原workspace四文件保留，未用整个workspace目录覆盖D归属。公共schema/shared/锁/组装/API仍集中A；新内部接口未在此准备包假称为已实现。
- 真实DeepSeek集中A配置/调用，worker不用复制A凭据；数据库仍独立55433/55434/55435。D仅开发Windows通道与临时根组件，真实native用户确认、正式配对与D03部署决定另验。

## 已核对的来源

只读核对原worktree：B `dev/context / 1cd90da9c3cebb5da551913dbb0cbee5bace9832`；C `dev/tool / 94c75066ed1c9a2ddb7f48a871ddafa957d5ba2d`；D `dev/runner / 7d6ee06e35de0dfb89bdec6fbdf3de29e54109f9`。均干净；原提交已在A的运行来源内。未替worker同步/改分支或发送聊天消息。

开工时worker核对HEAD等于ms-i2i-start的commit，并按本包提供的摘要和[上轮环境来源](evidence/environment.json)确认公共文件。固定源文件字节如下，准备阶段不修改：

| 文件 | SHA256 |
| --- | --- |
| contracts/uaw.schema.json | 3147f4dbee08f3ecd2681895f563b187f574a2f4d5f74acdbc1ef60c6841e0a1 |
| src/uaw/shared/ports.py | fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104 |
| src/uaw/shared/contracts.py | 08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b |
| src/uaw/shared/stores.py | 47e0f6b70a843bebf9fd1477e3a8c507b75cad8d8b01f03a2ea1b0b5f26fd300 |
| uv.lock | a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f |
| src/uaw/resources/prompts/intent-understand-v1.txt | a61a99f44b40e05c9452d9cdccf0d54ee7421d8cdc4d1b976e95335095d2e01a |
| src/uaw/resources/prompts/agent-root-v1.txt | 873ab6d0a770755e7eee416cb6a7eecee601fb9712fb3f4596c3eaa93f1a1352 |

## 验证范围

计划生成器核对39个包、五份session模板、目录归属无重叠、依赖无环及本地链接。第五份E模板保持可选未派发。另核对准备包没有改变运行来源字节、worker原提交祖先及工作区状态；实际结果见[准备证据](evidence/ms-i2i-preparation.json)。

没有重新执行Runtime/SQL/LLM；13次调用、31聚焦检查与1077历史覆盖仍属于原验收阶段。本包发布后四个新包才开工；没有预先接受完整MS-I2i或P1。
