# 多session开工、合并与交接流程

[分工总览](PARALLEL.md) · [当前主计划](SEQUENCE.md) · [提交交接模板](../coordination/HANDOFF_TEMPLATE.md) · [公共变更模板](../coordination/REQUEST_TEMPLATE.md)

## 1. 开工前还需要什么

接口已经说明“传什么、返回什么”。实际并行还需要把下面六件事固定下来：

| 要固定的内容 | 原因 | 谁负责 |
| --- | --- | --- |
| 共同的真实代码提交 | 各session不能基于不同版本的未完成代码猜对方行为 | A |
| 各自能改哪些文件 | 不同模块仍会碰到composition、schema、公共DTO、依赖等同一文件 | A分配，开发session遵守 |
| 谁维护某个状态 | 例如用户原文归Run、TaskFrame归Intent；重复建账会互相覆盖 | 契约固定，A审阅 |
| 公共变化如何提出 | 原接口不够时需要明确改字段及消费方，不能各自扩展 | 开发session提案，A集中落实 |
| 怎样证明本包完成 | “代码写了”不能证明接线、权限和失败分支正确 | 开发session验证组件，A验证组合 |
| 如何合入和退回 | 冲突不仅是文件冲突，也可能是两份不同权限/版本策略 | A集成，原负责人修业务问题 |

首次协作每个session先领一个小包，不按整个Runtime一次交付。不要让多个session在 `E:/UAW` 这份相同工作目录里同时写代码。

## 2. A先执行MS-00

以下是MS-00的开工检查表。2026-10-07代码基线已通过73项全量检查，Git已建立并关联用户提供的远端；提交、工作区与派发的实际状态以DISPATCH为准。B/C/D独立分支、worktree和依赖已配置，开发聊天待用户在对应目录开启。

1. 检查当前工作和遗留进程。P1-01已完成协议回归，保存本轮部分实现的准确记录；真实LLM语义质量仍待验收。
2. 对齐公共schema源、生成schema和运行包副本，以及HTTP路由/实现范围清单。现有入口已改动但未验证时不能先登记为已验收。
3. 运行静态、类型、必要全量检查；需要真实PG时使用本机开发库。取得新的本轮回执。真实LLM仍待D06，组件开发验证通过不能代替这个门槛。
4. 检查 `.gitignore` 和候选文件清单，确保 `.data/`、`.env`、私有配置、虚拟环境、缓存、测试临时文件、构建物和 `.worktrees/` 不会进入提交。
5. 初始化本地Git仓库并创建 `integration` 基线提交。Git作者身份缺失时明确补齐仓库级配置；不自行修改用户全局身份。逐路径暂存并检查暂存diff后提交。
6. 将**实际SHA**、schema/锁文件摘要、支持范围与未过项写入 [DISPATCH.md](../coordination/DISPATCH.md)。全部满足后由A更新并行计划的 `dispatch_ready`。

用户指定的`origin`是`https://github.com/Guozai3633/UAW.git`。本机集成使用`integration`；worker提交后由A审阅并合入，远端状态以实际推送回执为准。

## 3. 独立worktree和分支

A保留 `E:/UAW` 作为集成目录；B/C/D独立目录已创建，分支和实际位置如下。首波统一从固定标签`parallel-wave-1`对应提交开始；E仍只是候选。

| Session | 建议分支 | 建议目录 |
| --- | --- | --- |
| A | integration | E:/UAW |
| B | dev/context | E:/UAW/.worktrees/context |
| C | dev/tool | E:/UAW/.worktrees/tool |
| D | dev/runner | E:/UAW/.worktrees/runner |
| E，可选 | dev/evaluation | E:/UAW/.worktrees/evaluation |

以下是由A执行的PowerShell示例。先把变量填成实际存在的提交SHA；未填写时示例直接停止。仓库初始化和真实基线提交先按上节完成。

```powershell
$taskBaselineRef = '填写实际基线提交SHA'
if ($taskBaselineRef -eq '填写实际基线提交SHA') { throw '先完成MS-00并填写基线SHA' }
git -C E:/UAW rev-parse --verify "$taskBaselineRef^{commit}"
if ($LASTEXITCODE -ne 0) { throw '基线提交不存在' }
git -C E:/UAW worktree add -b dev/context E:/UAW/.worktrees/context $taskBaselineRef
if ($LASTEXITCODE -ne 0) { throw 'Context worktree创建失败' }
git -C E:/UAW worktree add -b dev/tool E:/UAW/.worktrees/tool $taskBaselineRef
if ($LASTEXITCODE -ne 0) { throw 'Tool worktree创建失败' }
git -C E:/UAW worktree add -b dev/runner E:/UAW/.worktrees/runner $taskBaselineRef
if ($LASTEXITCODE -ne 0) { throw 'Runner worktree创建失败' }
```

若使用Codex管理的worktree，应在Git基线就绪后明确从记录的提交创建，并把工具返回的真实目录写回handoff。两种方式选一种，避免重复建同名分支；不能依赖默认远端分支来代表当前未推送的工作。

用户随后在各自目录新建**本地聊天**，绑定下面的现有目录。它们已经是worktree，无需再创建第二套。把 [B](sessions/B.md)、[C](sessions/C.md)、[D](sessions/D.md) 页末开工说明粘贴进去。本聊天可作为A。每个session启动先核对cwd、分支和基线SHA；聊天描述相同不代表工作目录已经隔离。

## 4. 文件归属和公共变更

所有具体允许路径都在各session页和 `planning/parallel-plan.json` 中。这里补充容易发生冲突的文件：

| 文件/职责 | 负责人 | 开发session怎样参与 |
| --- | --- | --- |
| `contracts/interface_catalog.py` 与全部生成schema/API文档 | A | 提交最小契约变更提案，附调用方和成功/失败示例 |
| `composition.py`、`application.py`、API路由、资源提示词 | A | 自己提交模块facade/port及接线说明 |
| `shared/`、`run/`、`model/`、当前 `intent/` | A | 通过公开port消费；领域缺口先提案 |
| 当前 `context/seed.py`、`context/intent.py` | A | B在新的Context组件文件中工作，后续A处理迁移接线 |
| 依赖锁、基础测试fixture、数据库迁移、Docker启动脚本 | A | 提供依赖/迁移/环境提案；不用多个session各生成一套 |
| 计划状态、根README、统一实施证据 | A | 开发session只在自己的handoff报告，A集中更新 |
| Context新组件、Tool组件、Runner组件 | B/C/D各自拥有 | 包边界保持独立，需要联合改动时先由A重新分配范围 |

开发session发现自己的需求需要公共文件，不等于停下整包：先提交提案并继续不依赖该改动的部分。依赖提案的接线必须等A合入后同步真实基线。

普通引用“调用同一个方法”也可能有误解，交接至少附三组可执行例子：成功、拒绝或失败、重复或版本冲突。异常/取消/等待的返回规则不能只留在聊天里。

不要为缺少实现的领域返回假的成功。尚未开放的Tools/Runner flags保持原值；只有真实依赖与相应验收到位后由集成入口启用。

## 5. 运行和测试环境也要隔离

- 本次A已通过同一uv.lock离线配置三个`.venv`，editable项目来源各自独立；底层Python安装共用。仅准备时使用A已有下载缓存，依赖包采用copy模式，worker后续不操作这个共享缓存。
- 每个worktree使用自己的 `.venv/`、`.cache/` 和忽略的 `.data/`；Python/依赖遵循同一 `uv.lock`，开发session不重写锁文件。需要新增依赖由A集中处理。
- 首波开发session运行本包unit/组件用例，回执写 `tests/.artifacts/<session>/<包ID>/`。A负责实际SQL/组合回归并写统一实施证据。
- 需要独立跑真实PG时，由A提供受控本机连接配置和唯一测试主体/命名空间；不把密码贴聊天或写入handoff。现有PG fixture按随机主体清理数据，禁止truncate共享库。
- 只有A运行 `start-dev-db.ps1`、迁移、环境摘要、全量证据生成和共享schema生成器。不同worktree里的脚本可能生成不同开发密码/容器配置，不能同时各跑一套共享端口的启动流程。
- 默认不用同时启动多个后端。需要时A分配独立端口，例如A 8000、B 8101、C 8102、D 8103，并各自使用不同测试配置。
- 不向worker worktree复制整份 `.data`、凭据库或真实用户资料；签名/路径/配对用本session临时fixture。测试替身与实际能力回执明确区分。
- A必须在集成SHA上实际重跑组合验证；worker的测试成功不能推出合并后同样成功。数据库迁移期间暂停使用同一库的测试，迁移后再恢复。

Git worktree隔离源码和工作目录；它不自动隔离数据库、端口、系统凭据或OS权限。本方案通过文件归属、独立环境及A集中安排共享资源控制这些边界。

这一步先解决开发环境互不干扰；产品本身的并行Agent、沙箱、共享任务、代码撤销等仍按原P2/P3工作包实现。

## 6. 一包怎样提交和合并

1. **开发session交付：**在自己的分支提交本包代码，只在自己的handoff写实际SHA、改动清单、验证回执、缺口与接线要求。A的派发和接受记录写DISPATCH，双方不在同一状态文件同时写。提交前核对修改路径都在分工表内。
2. **A审阅范围：**检查公共文件越界、schema与port一致性、状态归属及真实/替身证据。无须等待三个包都完成才开始接收。
3. **有问题退回负责人：**模块业务规则由B/C/D修；跨模块接口缺口由A处理，再发布新基线。不要只在合并时选“保留当前/保留对方”跳过语义判断。
4. **A依次合入：**开始前保存干净集成工作区，审阅分支diff。第一次建议使用普通 `git merge --no-ff`，保留模块分支边界；需要拆公共修改时先形成独立提交，不机械地整包覆盖。
5. **解决冲突：**A判断状态/权限/版本的正确规则，必要时由对应负责人出修复提交。只修文件标记不算解决语义冲突。
6. **实际回归和发布：**A在合入结果上验证前后公共调用和组合场景，更新实施记录、逐操作实现范围和计划。记录真实集成SHA，接受一个包后再接下一个。
7. **开发session同步：**包交接完成且自己的目录干净后，把新集成分支合入自己的分支，再领下一包。首次协作不要重写已交接提交历史。Git worktree内可见同一仓库的本地 `integration` 分支，无需Git远端。

一份merge既包含代码又包含接线变更时，保持业务提交与公共契约/集成提交可分辨，便于定位和回退。不是每个包都需要新增框架或全量测试；A按实际组合风险执行必要检查。

## 7. 合并出问题如何退回

- 未完成的merge先检查 `git status` 和手工修改；确保没有需保留的独立用户改动后，使用Git的merge abort恢复合并前状态。
- 已合入的坏包由A做 `git revert` 形成新的回退提交。回退merge时先确认父提交，不能机械填写主线编号。
- 不使用 `reset --hard`、目录覆盖或删除worktree来“解决”冲突。其他session分支保留，修复后重新审阅合入。
- 数据库变更不能只靠代码revert撤销；A记录对应迁移/数据兼容/备份策略。凭据、已发生的外部动作也不能随代码提交自动回退。
- worktree归档或删除只在提交和必要回执已保存后进行；保留未提交工作及必要的忽略文件。

## 8. 怎样判断这一轮协作是否有效

记录每包实际开发/等待时间、公共提案次数、越界修改、文件冲突和接口语义冲突、退回次数及A的集成耗时。第一次只比较“是否更快得到可验证的完整结果”，不按session数量承诺速度倍数。

如果A积压，先缩小交付包并减少共享变化；若某个worker总在等上游，就给它独立样本或尚未依赖接线的组件任务。完成一波后再决定是否用第5个session。

## 9. 会话与目录隔离

单独创建聊天不代表源码已经隔离。使用同一个Local目录的聊天会操作同一份文件；选择Codex的Worktree模式则可由应用创建独立Git worktree。[OpenAI官方说明](https://learn.chatgpt.com/docs/environments/git-worktrees)

本次已按上表创建长期固定目录，用户选择这些目录作为各自本地聊天的工作区即可。三个worktree共用Git对象库和远端，各自拥有源码、分支和index；它们不是OS安全沙箱。
