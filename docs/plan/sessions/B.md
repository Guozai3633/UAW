# Session B：上下文组件

[并行开发总入口](../PARALLEL.md)

状态：独立分支/worktree及依赖已准备。首包已分配，开发聊天尚未创建；开工先核对parallel-wave-1和DISPATCH。

## 工作位置和顺序

- 实际分支：`dev/context`。
- 实际worktree：`E:/UAW/.worktrees/context`。
- 首包：MS-C1；后续：MS-C2。
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
- `tests/unit/context/`
- `tests/integration/context/`
- `docs/coordination/handoffs/B.md`
- `docs/coordination/requests/B/`

忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。

## 具体边界

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

## 可复制到新session的开工说明

下面只启动本session任务；用户在独立工作区新建聊天后粘贴。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session B：上下文组件。
当前工作目录必须是E:/UAW/.worktrees/context，分支必须是dev/context。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/B.md。
读取docs/coordination/DISPATCH.md。首次开工核对HEAD与parallel-wave-1解析出的commit相同；后续按A发布的新基线同步。
若基线未发布，先完成本包可做的设计/提案；不要修改或使用其他session未交接的源码。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
