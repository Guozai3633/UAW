# Session E：可选样本与评测

[并行开发总入口](../PARALLEL.md)

状态：代码基线已通过73项检查，Git已关联远端；尚未创建worker/worktree。B/C/D/E取得实际派发SHA和记录后才开始组件包。

## 工作位置和顺序

- 建议分支：`dev/evaluation`。
- 建议worktree：`E:/UAW/.worktrees/evaluation`。
- 首包：MS-Q1；后续：本轮无。
- 交接记录：[docs/coordination/handoffs/E.md](../../coordination/handoffs/E.md)。
- 公共变更提案目录：`docs/coordination/requests/E/`。

## 可修改路径

- `tests/evaluation/`
- `tests/fixtures/parallel/`
- `docs/coordination/evaluation/`
- `docs/coordination/handoffs/E.md`
- `docs/coordination/requests/E/`

忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。

## 具体边界

- 第5个session可选，负责办公/开发/学术样本、验收表和来源/权限反例。
- 不改Runtime或其他session测试，不生成共享JUnit和环境摘要。
- 无真实提供方时只提交样本/预期标准，不生成伪模型样本或语义质量分数。

公共schema/port/依赖有缺口时，提交有字段、示例、错误语义和受影响调用方的提案，A合入并发布新基线后再使用；不在私有DTO中偷偷加不兼容字段。

## 对应工作包

### MS-Q1：三类样本及语义审阅标准

对应原轮：[P0-01](../rounds/P0-01.md)、[P1-01](../rounds/P1-01.md)、[P1-11](../rounds/P1-11.md)、[P2-07](../rounds/P2-07.md)。
开发前置：MS-00。

任务：

1. 补办公、开发、学术的原始输入、材料、可接受成果与返工标准。
2. 增加任务扩大范围、缺口、数字/日期、后续纠正等语义审阅样本，区分硬断言与人工质量判断。
3. 为已合入组件补跨边界测试提案；不与B/C/D修改同一份测试。

交付检查：

- 样本来源与预期可审阅，不能把固定关键词当语义质量验证。
- 真实LLM质量/费用仍待配置，无对应回执不填评分。

## 可复制到新session的开工说明

下面只启动本session任务；用户在独立工作区新建聊天后粘贴。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session E：可选样本与评测。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/E.md。
核对当前cwd为本session worktree，并读取docs/coordination/DISPATCH.md的真实基线SHA和本session派发状态。
若基线未发布，先完成本包可做的设计/提案；不要修改或使用其他session未交接的源码。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
