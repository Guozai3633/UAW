# A17：同次来源检查中复用纯格式校验

2026-10-12，继续原MS-I2l，基于A16准确来源
02033c0831d1a5e56580136a392f69ee753cca9f；发布元数据3d0ac536e69b48724edba9f79fe0d59226813ce3。
只改A schema/命令来源/统一current/peer入口与A测试；不修改worker业务、权限策略、公开DTO或flags。
准确源码由DISPATCH随后公布，不建立新共同start，不要求worker同步或开新包。

## 实际热点与边界

A新增临时诊断child复用原D installed fixture，保留原真实首次链成功断言。
该诊断在原源码失败65.77秒；只保存模块/函数/行号/次数/CPU指标，无凭据、目录、正文或账号值。
子进程整个serve loop包含并行监控、执行和初始化等待，cProfile本身有开销，不能用于生产耗时比例。
其中validate_contract约8106次、累计5.371秒，JSON Schema descend/evolve/ref占主要选定CPU热点。
原独立 metadata CPU诊断测试保留，新增child诊断不覆盖旧节点/原回执。
新增诊断入口installed_child_profile.py仅显式指定时收集，不加入默认test_*回归额外重复完整链。
原诊断失败XML仍保留首次执行节点名，文件归档名称改变不算复跑成功。

本阶段优化的是**同一包内静态Schema对完全相同JSON内容的重复计算**。
不缓存业务许可、签名成功、当前账号、SQL输入、OS/key/native状态或工具/模型结果。
内容格式正确不等于权限允许：完整业务谓词及每次真实SQL/外部来源仍执行。

## 实现

src/uaw/shared/schema.py增加内部contract_validation_scope()：

1. 仅 owning asyncio task 内同一次元数据pass有效。嵌套同task共用，child/thread不能命中父scope，
   后续pass重新创建。退出/失败/取消清空所有digest与ContextVar。
2. 仅 exact JSON builtin（str-key dict/list/str/int/finite float/bool/null）可参与。
   tuple、自定义/子类对象、非string key、非有限数、循环/超限值绕过复用，沿原validator执行。
3. 对完整内容作JSON编码（sorted keys，不混淆bool/int/float），最多16KiB、2048节点、32深度。
   编码SHA256+schema名称+**同一实际validator对象**作比较；不留raw值，不以对象id推断内容。
4. 只保留成功格式结果，最多256项；失败每次完整生成原错误路径。
   validator被替换/缓存逐出，旧记录不能命中；值被修改后digest不同，重新校验。
5. validate_contract原接口和ContractViolation字段/路径保持；未进入scope的调用沿原计算。
   scope不是公共wire对象或模型工具，无HTTP/模型可启用入口。

显式scope只接入RegisteredRunnerRechecks.current、RunnerCommands._collect、
EnrolledPeerRegistry.current/owner等短来源读。没有scope跨文件读、模型、用户/native UI或工具效果。
SQL两个完整pass、最终fresh witness、事务观察、取消/期限、双方OS/key/签名/native/目录仍原样。
production checked_metadata=False保持；没有启用既有元数据输入缓存候选。

## 同来源测量

同一实际SQL登记命令、actor/channel和完整current输出，channel/root/native/gate受控：

| 指标 | 绕过纯格式复用 | 复用 |
| --- | ---: | ---: |
| 实际fresh SQL SELECT | 43 | 43 |
| 实际格式校验计算 | 221 | 50 |
| 单pass格式复用 | 0 | 171 |
| 样本墙钟秒 | 0.400 | 0.244 |

输出逐字段相同；SQL次数明确未减少。仅一个组件样本，不承诺整个任务同比提速。
不将格式复用171次当作少执行171次权限检查。

## 验证和中断

- 21单元通过：新6个范围/类型/validator替换/取消隔离节点及原15契约节点。
- 58受影响SQL节点通过：统一current、原完整peer/owner、撤销/外部等待后key检查、
  lease/device、current/history/absence/tombstone、SQL变化监控和取消。
- 1实际SQL测量节点通过，验证相同projection/fresh SELECT。
- 212源文件Mypy、8修改文件Ruff/格式通过；更完整实际链另列本阶段证据，不据组件通过接受整链。

本阶段不同通过节点80（21＋58＋1），历史并集368未全部在本版重跑，不称一次全量。
随后未加profiler的实际首次链仍1失败/104.73秒：新Run原command1/open0、无签名回执，
原reply deadline未增加；3次composite累计11.223秒包含watch与execute并行。
启动35.875秒、callback21.789秒等口径与前轮机器负载不同，不能据单样本推断通用性能退化比例。
只有“未体现整链成功/收益”的结论成立。4随机凭据、2keys、child/proof清理通过。
诊断原源码与优化后链都是独立新临时实例；不重发unknown，原成功断言/失败单独保留。
该失败不计入80通过节点，读取/签名journal/恢复及后续材料成果仍未验收。

初次单元受限执行没有XML完成回执，已中断；在正常审核运行后21项完成，未将中断计入通过。
原性能对比因自动审批审核额度不足未执行，用户继续后按同一require_escalated重试完成。
不是unsafe判定；没有绕过审核。诊断profiling首次原成功断言失败独立保留，不xfail/skip或放宽期限。
原格式101字符修正不改变语义。实际文件/签名journal/恢复结果见本阶段JSON。

## 停止与后续

本次没有新worker包。B/C/D保留交付点；A继续自己来源成本、原注册/发送和真实文件汇合。
原10秒reply/30秒lease/120秒root及更早期限、unknown不重发、旧journal独立权限保持。
不开放子Agent/DAG/写入安装exec；不代本人确认或接受，不新增模型调用或访问用户文件。
完整材料→Context→固定模型→引用/Artifact/Verification→本人接受与汇合全量仍须真实完成。
回执见docs/implementation/evidence/ms-i2l-a17.json；旧1691全量及旧失败/费用保持。
