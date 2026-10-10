# Session B：前端工作区（原Context负责人）

[并行开发总入口](../PARALLEL.md)

状态：MS-U1已发布待开工：本轮临时负责apps/web真实前端；MS-C7已接受，暂停新Context优化。以DISPATCH的固定版本与派发为准。

## 工作位置和顺序

- 实际分支：`dev/context`。
- 实际worktree：`E:/UAW/.worktrees/context`。
- 首包：MS-C1；后续：MS-C2、MS-C3、MS-C4、MS-C5、MS-C6、MS-C7、MS-U1。
- 交接记录：[docs/coordination/handoffs/B.md](../../coordination/handoffs/B.md)。
- 公共变更提案目录：`docs/coordination/requests/B/`。

## 可修改路径

- `src/uaw/context/facade.py`
- `src/uaw/context/contracts.py`
- `src/uaw/context/ports.py`
- `src/uaw/context/repository.py`
- `src/uaw/context/sources.py`
- `src/uaw/context/rules.py`
- `src/uaw/context/selection.py`
- `src/uaw/context/composer.py`
- `src/uaw/context/references.py`
- `src/uaw/context/model_input.py`
- `src/uaw/context/cache.py`
- `src/uaw/context/registered.py`
- `src/uaw/context/authority.py`
- `src/uaw/context/readers.py`
- `src/uaw/context/read_batch.py`
- `src/uaw/context/read_metrics.py`
- `tests/unit/context/`
- `tests/integration/context/`
- `apps/web/`
- `docs/coordination/handoffs/B.md`
- `docs/coordination/requests/B/`

忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。

## 具体边界

- 本轮MS-U1独占apps/web做真实页面，暂停新Context优化；原Context归属保留。
- seed.py和intent.py包含已验证的理解专用实现，归A；B用新文件实现通用Context组件。
- 通过Reader port处理已有获准来源；Workspace/Board/记忆未接入时明确不可用。
- 不写原文、Model配置或执行权限，不把外部资料升级为系统指令。

公共schema/port/依赖有缺口时，提交有字段、示例、错误语义和受影响调用方的提案，A合入并发布新基线后再使用；不在私有DTO中偷偷加不兼容字段。

## 对应工作包

### MS-C1：规则、来源与窗口分配

对应原轮：[P1-02](../rounds/P1-02.md)。
开发前置：MS-00。

任务：

1. 定义并实现Reader port，固定已读取来源和版本；缺失/越权明示。
2. 按已设计优先级、作用域和信任级别装配InstructionSet；冲突保留明确结果。
3. 按实际模型窗口保护原文/要求及输出空间，计算输入/输出/工具保留。
4. 单独验证权限、材料注入、版本、窗口不足；提交来源装配的输入输出例子。

交付检查：

- 只依赖共同基线与注入port，不导入未合并的Tool/Runner私有实现。
- 外部文本不能升级为平台权限；关键要求不能因窗口不足静默删掉。
- 无完整Reader/模型/Runner时明确边界，不宣称P1-02整轮验收。

### MS-C2：固定快照和引用查询

对应原轮：[P1-02](../rounds/P1-02.md)。
开发前置：MS-I1。

任务：

1. 在新共同基线上完成快照manifest/引用来源和不可变修订的仓储适配。
2. 补实存储测试代码并交A执行或在获准独立环境执行；保持Workspace Reader未接入分支明确。

交付检查：

- Ref只指向真实读取来源；当前授权仍复核。
- 代码和证据可合入，不修改A保留文件。

### MS-C3：通用快照到Model输入转换

对应原轮：[P1-02](../rounds/P1-02.md)、[P1-07](../rounds/P1-07.md)。
开发前置：MS-I2c。

任务：

1. 在context/model_input.py实现公开ModelInputPort.resolve，构造ModelPrompt，不导入Model私有provider类型。
2. 消费已有持久快照/InstructionSet/实际Reader和ModelToolSet，复核当前scope、epoch、依赖版本和撤销；缺authority/能力Reader不可用。
3. 稳定装配获准指令、保留原文、区分外部材料数据，估算完整消息/工具schema；不使用理解专用模板处理agent_step。
4. 组件及真实SQL覆盖重启、换Run、规则/工具/来源/epoch变化、窗口不足及取消；A后续负责composition与Model输入路由。

交付检查：

- 消息文本与真实来源一致，外部材料无法变成系统权限或新增工具。
- 缺工具来源不能伪造空工具，快照不授权当前读取；不修改A保留的seed/intent/model/composition。

### MS-C4：上下文纯计算有界缓存

对应原轮：[P1-02](../rounds/P1-02.md)、[P4-04](../rounds/P4-04.md)。
开发前置：MS-I2e。

任务：

1. 在context/cache.py新增可选进程内有界缓存，仅复用已校验数据的格式化/序列化/token估算。
2. 保持现有GenericModelInputs/TokenCounter公开签名；当前scope/authority/Reader/epoch/规则/工具/窗口/取消每次复核。
3. 键覆盖实际完整内容/元数据、主体/Run、模型/权限/预留和算法版本；容量/字节有界、结果复制、默认关闭。
4. 验证纯计算次数减少、输入/信任/窗口变化失效、跨主体隔离、撤销/取消与容量；实际SQL原回归保留。

交付检查：

- 缓存不保存访问许可/唯一状态/模型输出，不跳过来源读取或最终检查；异常不靠旧值掩盖。
- 只报告实际本地计算变化，不宣称provider缓存或Token/延迟收益；详细范围见MS-I2e-next-packages。

### MS-C5：通用上下文登记/当前权威/完整输入链

对应原轮：[P1-02](../rounds/P1-02.md)、[P1-07](../rounds/P1-07.md)。
开发前置：MS-I2f2。

任务：

1. 实现可信登记入口、主体隔离blob及已有命名schema的SQL来源/配方记录，CAS/幂等/修订/撤销。
2. 从实际Run/原文/政策和登记记录构建CompositionAuthority、Reader及RuleProvider，保持固定用户模型和原文保护。
3. 接通登记→Context.build→snapshot/reference→GenericModelInputs；缓存不替代当前检查，非空工具集缺验证源拒绝。
4. 阶段版先报告固定接口与SHA，然后继续真实SQL/blob重启/隔离/修订/撤销和原模块回归；详见MS-I2g-parallel-packages。

交付检查：

- 单个完整能力包四个里程碑；前两个阶段提交后继续本包，不等待最终集成才做后两项。
- 真实源不来自测试目录，受控provider清楚标注；缺LLM/文件源不宣称产品闭环或整轮验收。

### MS-C6：多规则语义评估/版本复查/读取测量

对应原轮：[P1-02](../rounds/P1-02.md)、[P1-07](../rounds/P1-07.md)。
开发前置：MS-C5、MS-I2f2。

任务：

1. 显式assessor port与RegisteredRuleProvider兼容构造，固定实际候选，模型不能改正文/level/来源。
2. 多规则重要冲突、优先级和精确引用评估；缺实际语义来源不可用，等待前后复查。
3. 登记/build/模型输入/引用整链测量并减少重复展开，禁止缓存当前授权。
4. 自身数据库真实SQL修订/撤销/并发/重启/缓存和原Context回归；详见MS-I2h-parallel-packages。

交付检查：

- 前两里程碑交固定接口后继续同包；受控评估不宣称真实模型语义验收。
- 完整规则/模型/来源不变，查询次数和拒绝行为实际对比。

### MS-C7：Context读取提速/有界批读/来源等价

对应原轮：[P1-02](../rounds/P1-02.md)、[P4-04](../rounds/P4-04.md)。
开发前置：MS-C6。

任务：

1. M1实际SQL基线测量get/往返/Reader/assessor与上下文耗时，尽早交批读内部签名及调用样例。
2. M2减少重复资料展开和纯计算，操作内有界读取，原公开/等待后/提交/派发前复查保留，不缓存授权。
3. M3可选ContextRecordBatchPort消费完整owner/Ref/版本，A做SQL适配；兼容方式可独立继续，证明消息/引用/拒绝等价。
4. M4自身55433实跑原模块与批缺失/删除/撤销/并发/跨主体/新进程，保存实测指标与全部失败修复。

交付检查：

- 完整输入输出/目录/策略以MS-I2i-parallel-packages.md为准；M1阶段说明、M2源码交付后继续M3/M4。
- 优化不删权限/取消/来源门槛，不承诺虚构比例；真实SQL与受控评估分别记账，完整P1/P4未自动接受。

### MS-U1：真实Web工作区/协议客户端/事件恢复

对应原轮：[P1-10](../rounds/P1-10.md)。
开发前置：MS-C7、MS-T2f、MS-R2f。

任务：

1. M1在apps/web锁定React/TypeScript/Vite/pnpm，消费现有契约与实际端点，交客户端阶段接口。
2. M2真实聊天/浅色任务理解/状态/审批取消/文本Markdown成果与合同接受页面。
3. M3Item/seq/revision去重、刷新断线原请求恢复、SSE或明确分页轮询、安全草稿投影。
4. M4类型构建/必要组件测试及Playwright，A端点到达即联调，mock与真实回执分开。

交付检查：

- apps/web与其锁由B独占；暂停新Context优化，后端/公共契约/认证由A维护。
- 不泄漏供应商key/管理员token，不解析模型文字猜执行状态，真实联调缺依赖标pending。

## 当前session开工说明

沿用已有聊天与独立worktree，粘贴本session说明。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session B：前端工作区（原Context负责人）。
当前工作目录必须是E:/UAW/.worktrees/context，分支必须是dev/context。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/B.md。
读取docs/coordination/DISPATCH.md。本轮核对HEAD与ms-i2j-start解析出的commit相同；后续在包边界按A发布的新基线同步。
当前执行MS-U1。工作区干净后fetch origin --tags，使用git merge --ff-only ms-i2j-start同步本工作分支；失败先报告，不reset，保留已有历史。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
