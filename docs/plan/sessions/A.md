# Session A：集成与任务理解

[并行开发总入口](../PARALLEL.md)

状态：MS-I1开发范围完成；继续MS-I2公共接线。以DISPATCH的固定版本与派发为准。

## 工作位置和顺序

- 实际分支：`integration`。
- 实际worktree：`E:/UAW`。
- 首包：MS-00；后续：MS-I1、MS-I2、MS-I3。
- 交接记录：[docs/coordination/handoffs/A.md](../../coordination/handoffs/A.md)。
- 公共变更提案目录：`docs/coordination/requests/A/`。

## 可修改路径

- `src/uaw/composition.py`
- `src/uaw/application.py`
- `src/uaw/shared/`
- `src/uaw/api/`
- `src/uaw/infrastructure/`
- `src/uaw/run/`
- `src/uaw/model/`
- `src/uaw/intent/`
- `src/uaw/context/seed.py`
- `src/uaw/context/intent.py`
- `src/uaw/resources/`
- `contracts/`
- `planning/`
- `design/`
- `architecture/`
- `technology/`
- `ops/`
- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `tests/conftest.py`
- `tests/integration/test_control_plane.py`
- `tests/integration/test_bootstrap.py`
- `tests/integration/model/`
- `tests/integration/intent/`
- `README.md`
- `DEVELOPMENT_PLAN.md`
- `.gitignore`
- `.gitattributes`
- `tests/integration/test_context_wiring.py`
- `tests/unit/model/`
- `docs/plan/`
- `docs/api/`
- `docs/design/`
- `docs/technology/`
- `docs/implementation/`
- `docs/DOCUMENT_MAP.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/coordination/DISPATCH.md`
- `docs/coordination/HANDOFF_TEMPLATE.md`
- `docs/coordination/REQUEST_TEMPLATE.md`
- `docs/coordination/handoffs/A.md`
- `docs/coordination/requests/A/`

忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。

## 具体边界

- 负责现有P1-01收尾、公共契约、组装根、迁移、依赖锁和合并。
- 独立组件的业务错误交回对应负责人修复，A负责跨模块接线与冲突裁决。
- 逐包审阅、合并、回归；保持集成分支可启动，不同时接收多份公共改动。
- B/C/D首包已合入，MS-I1开发范围通过；A继续MS-I2，B按新基线执行MS-C2。

公共schema/port/依赖有缺口时，提交有字段、示例、错误语义和受影响调用方的提案，A合入并发布新基线后再使用；不在私有DTO中偷偷加不兼容字段。

## 对应工作包

### MS-00：收尾并建立共同基线

对应原轮：[P0-05](../rounds/P0-05.md)、[P1-01](../rounds/P1-01.md)。
开发前置：本session收尾与初始化工作。

任务：

1. 检查并结束遗留运行；完成当前P1-01的静态/真实PG边界检查，修复实际失败。
2. 同步契约源与生成物、已挂载入口与实现范围，记录真实模型仍待D06。
3. 检查忽略规则，初始化Git并创建本地基线提交；不提交.data、凭据、构建缓存或worktree。
4. 冻结schema/公开port/事件/失败/版本语义，记录真实提交SHA、依赖锁摘要和模块修改边界。
5. 分别配置B/C/D的worktree与环境，填写交接记录，变更dispatch_ready后才开工。

交付检查：

- 当前源码全量检查有新回执；历史60项不是当前P1-01的通过证明。
- Git实际可用，所有session基于相同真实提交SHA；当前工作已保留。
- 提供方未配置仍保留门槛，不把开发边界通过写成真实LLM验收。

### MS-I1：合入Context并接Intent/Model

对应原轮：[P1-01](../rounds/P1-01.md)、[P1-02](../rounds/P1-02.md)。
开发前置：MS-00、MS-C1。

任务：

1. 审阅B的目录/接口/证据，集中处理公共契约提案后合入。
2. 完成composition和Model输入port接线，处理现有context/intent.py与通用装配器的职责。
3. 验证输入修订、摘要权限、窗口/结构协议以及来源删除与撤销；保留实际P0/P1门槛。

交付检查：

- 组合回归通过，A/B对接线前后公开port样例达成一致。
- Context绑定、规则和引用实际一致；无真实LLM门槛时只验收开发范围。

### MS-I2：合入Tool与Runner协议基础

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)。
开发前置：MS-I1、MS-T1、MS-R1。

任务：

1. 分别审阅合入C/D基础包，统一批准契约/依赖/数据库变更。
2. 确认审批、预算、配置、Runner调用port及调用顺序；修跨边界失败返回。
3. 发布第二个集成SHA供C/D同步；真实执行仍等待后续接线和授权。

交付检查：

- 三模块接口消费方检查通过；不是把签名/执行替身当真实Runner。
- D03选择及提供方配置的未满足项仍可见。

### MS-I3：汇合后进入Agent闭环

对应原轮：[P1-07](../rounds/P1-07.md)、[P1-08](../rounds/P1-08.md)、[P1-09](../rounds/P1-09.md)、[P1-11](../rounds/P1-11.md)。
开发前置：MS-C2、MS-T2、MS-R2。

任务：

1. 统一跨模块回归，检查原始完整轮的依赖与真实模型/环境门槛。
2. 按P1-06/07/08/09/10/11原计划接变更、Agent、完成核验、用户控制和页面。
3. 此包是后续汇合入口；不能代替尚未展开的页面与闭环轮。

交付检查：

- 50轮主计划的退出标准保持有效。
- 真正的P1阶段验收需真实用户授权、测试、成果和审阅证据。

## 可复制到新session的开工说明

下面只启动本session任务；用户在独立工作区新建聊天后粘贴。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session A：集成与任务理解。
当前工作目录必须是E:/UAW，分支必须是integration。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/A.md。
读取docs/coordination/DISPATCH.md。首次开工核对HEAD与parallel-wave-1解析出的commit相同；后续按A发布的新基线同步。
当前执行MS-I2。工作区干净后fetch origin --tags，将ms-i1合入本工作分支，保留已有提交历史。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
