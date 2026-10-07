# Session D：Runner协议与授权组件

[并行开发总入口](../PARALLEL.md)

状态：独立分支/worktree及依赖已准备。首包已分配，开发聊天尚未创建；开工先核对parallel-wave-1和DISPATCH。

## 工作位置和顺序

- 实际分支：`dev/runner`。
- 实际worktree：`E:/UAW/.worktrees/runner`。
- 首包：MS-R1；后续：MS-R2。
- 交接记录：[docs/coordination/handoffs/D.md](../../coordination/handoffs/D.md)。
- 公共变更提案目录：`docs/coordination/requests/D/`。

## 可修改路径

- `src/uaw/workspace/binding.py`
- `src/uaw/workspace/contracts.py`
- `src/uaw/workspace/ports.py`
- `src/uaw/workspace/repository.py`
- `apps/local_runner/uaw_runner/`
- `tests/unit/runner/`
- `tests/integration/runner/`
- `docs/coordination/handoffs/D.md`
- `docs/coordination/requests/D/`

忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。

## 具体边界

- 先落实可信命令信封、期限/主体/签名校验port、授权根和撤销状态。
- RootSelection只由可信本机用户入口生成；测试根限制在本session临时目录。
- D03未决定前不开放安装/写入/exec；仅协议组件不能宣称配对或OS隔离已经可用。
- 签名算法或新依赖需要契约/ADR提案，由A集中落地后再验证真实签名。

公共schema/port/依赖有缺口时，提交有字段、示例、错误语义和受影响调用方的提案，A合入并发布新基线后再使用；不在私有DTO中偷偷加不兼容字段。

## 对应工作包

### MS-R1：Runner协议与授权范围校验

对应原轮：[P1-04](../rounds/P1-04.md)。
开发前置：MS-00。

任务：

1. 落实RunnerCommand/Receipt DTO校验与签名验证port，校验期限、主体、根句柄、fencing和稳定command_id。
2. 实现获准根/相对路径/真实路径校验与撤销模型；临时目录验证链接越界。
3. 设计配对nonce/一次码及RootSelection的来源/有效期/一次使用，不把聊天路径当授权。
4. 列出真实IPC、签名实现、配对存储与D03决定所需接线；包外依赖交A审批合入。

交付检查：

- 组件校验和真实本机临时路径验证有证据；签名替身只算协议测试。
- 不连接真实用户项目、不安装系统环境、不开放exec。
- 没有真实配对/签名/执行权限回执时P1-04不能标accepted。

### MS-R2：真实配对和获准执行接线

对应原轮：[P1-04](../rounds/P1-04.md)、[P1-05](../rounds/P1-05.md)。
开发前置：MS-I2。

任务：

1. 落实实际签名/可信IPC/用户确认配对及授权句柄的存储。
2. D03确定且真实权限到位后才能进入输入快照、隔离和进程；安装另走审批。

交付检查：

- 实际配对/权限有回执，scope逐次复核。
- 代码隔离不声称OS隔离，真实代码任务仍需实际test与交付验证。

## 可复制到新session的开工说明

下面只启动本session任务；用户在独立工作区新建聊天后粘贴。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session D：Runner协议与授权组件。
当前工作目录必须是E:/UAW/.worktrees/runner，分支必须是dev/runner。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/D.md。
读取docs/coordination/DISPATCH.md。首次开工核对HEAD与parallel-wave-1解析出的commit相同；后续按A发布的新基线同步。
若基线未发布，先完成本包可做的设计/提案；不要修改或使用其他session未交接的源码。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
