# 2026-10-18：A16单会话续项已交付，进入H02-v7本人重测

本轮本人指定全部由A完成，未派发BCD或同步其分支。审阅等待计时、原剩余额度纠正、持久接受和取消已集成；短报告误走普通回复的样例已在固定提示词补充后用原题复测。当前实际入口与清单见 [H02-v7](../implementation/human-tests/H02-v7.md)，准确回执见 [A16](../implementation/evidence/h02-i04-a16.json)。

P1-14/16/17按真实工程与体验工作记开发中；50不同SQL、当前固定模型办公/学术诊断和部署分别报告，不把这些升级为整轮accepted。本人满意/接受、人工事实样本和可比质量仍pending。下一轮先按本人反馈修复，再做质量核准和办公/学术整体验收；本机、Tool、子Agent与DAG分别推进。下方分包、来源和“未装配”是各历史阶段状态，当前以DISPATCH页首为准。

# 2026-10-16：MS-I2m并行开发入口

P1-13实际普通聊天一次固定模型调用已交付；H01-v5本次本人反馈“可以了”，仅认可普通问答复体验。P1-14原Run续跑、P1-15独立正确性及H02完整验收仍未通过。

[正式分包与M1–M4](../coordination/requests/A/MS-I2m-parallel-packages.md) · [固定A/B/D接口与C消费约定](../coordination/requests/A/MS-I2m-AD-contract.md) · [四份提示词](../coordination/requests/A/MS-I2m-session-prompts.md)。共同标签ms-i2m-start及准确40位SHA以远端DISPATCH页首正式发布为准。

| Session | 本轮模块 | 说明 |
| --- | --- | --- |
| A | Run/API与真实接线 | 同Run回答/纠正、安全消费、实际固定模型和逐阶段集成 |
| B | apps/web | 问题发现/原Run答复、受理与生效、刷新及成果审阅 |
| C | 独立质量评测 | 临时新增evaluation目录；原Tool交付保留，不扩大原Tool包 |
| D | 执行计时组件 | 临时新增execution_clock.py；主动/等待/CAS恢复，不延长旧调用或授权 |

新增RunConversationView读图合同解决页面无法准确发现问题的缺口；现有P1-12四端点保持兼容，实际handlers到A阶段公布后才联调。C/D本轮明确新文件归属，暂停继续原本机链；本机首次链仍独立未通过。每包四里程碑连续完成，阶段SHA到即审，不等待全员最终交付。原表与历史状态如下，冲突以本段及正式DISPATCH为准。

# H02：下一次对话与单 Agent 文本体验开发安排

2026-10-14。P1-12公共契约/严格消费者已交付，准确阶段源码以DISPATCH为准；**P1-13～17尚未验收，新页面/续跑handler尚未装配，无新worker正式包**。本页由 [ADR-001](../decisions/ADR-001-conversation-and-delivery.md) 约束，任务权威在 planning/catalog.py，生成轮次页记录精确依赖。[P1-12消费说明](../coordination/requests/A/H02-P1-12-ports.md)。

## 1. 按模块—阶段—每轮任务推进

| 工作包 | 主责/模块 | 每轮目标和任务 | 目录与退出条件 |
| --- | --- | --- | --- |
| [P1-12](rounds/P1-12.md) | A：公共协议、Run/API | 固定首次动作、消息完成、原问题答复/纠正、暂停计时对象；发布兼容契约与消费例 | contracts/、src/uaw/shared/、docs/api/；准确来源、迁移/旧数据方案可审阅 |
| [P1-13](rounds/P1-13.md) | A：Agent/Intent/Run接线 | 普通首次调用直接回答/用工具/提问；消息与正式成果分流；不固定独立理解/自评 | src/uaw/agent/、intent/、run/、resources/prompts/；真实普通样本一次成功调用，全部失败/费用另计 |
| [P1-14](rounds/P1-14.md) | A：Run控制；B：页面 | 原 Run 追加回答、纠正、安全边界、暂停与恢复、刷新/幂等 | src/uaw/run/、api/、apps/web/src/；实际同Run连续问答、长等待/取消/授权失效/重启通过 |
| [P1-15](rounds/P1-15.md) | A：独立评测 | 人工核对小样本/反例，旧新策略实测；分别报告答案错误/漏判/不必要阻断 | tests/fixtures/evaluation/、ops/、docs/implementation/evaluation/；关键概念/证据错误阻断，指标分母和失败清晰 |
| [P1-16](rounds/P1-16.md) | A：文本成果；B：审阅 | 粘贴材料→来源Context→固定模型→Artifact/准确引用→逐项检查/接受；单Agent独立验收 | src/uaw/workspace/、agent/completion/、apps/web/src/；办公与学术各一个完整真实交付 |
| [P1-17](rounds/P1-17.md) | A集成、用户本人 | 固定新版本、实际启动，体验对话→澄清→纠正→文本成果，按原owner修复和复体验 | docs/implementation/human-tests/；工程、事实质量、本人体验、产品接受分别记录 |

这些是目标目录；worker 具体允许文件在正式分包时固定，不授权 A 代写 B/C/D 的业务源码。

## 2. 可并行的安排

```mermaid
flowchart LR
  Base[已验固定模型、历史、最小Context来源] --> Contract[P1-12 公共契约]
  Contract --> Fast[P1-13 快通路]
  Contract --> Eval[P1-15 人工样本与评测]
  Fast --> Continue[P1-14 原Run接续和计时]
  Fast --> Text[P1-16 单Agent文本成果]
  Continue --> Human[P1-17 H02真人体验]
  Text --> Human
  Eval --> Human
  Human --> Methods[P2-07 办公学术方法扩展]
  Local[本机文件签名发布链] --> FileGate[独立真实本机验收]
  Child[子Agent、共享板、Join] --> Collaboration[独立协作验收]
```

A 先提交公共协议，再让 B 消费实际来源做问题答复/纠正与审阅页面。P1-15 样本和 harness 可与快通路开发并行，最终实测用准确候选源码。

C/D 继续本机链的原接口和证据缺口，具体下一包在来源准备好后派发；它们不是 H02 文本门槛。无需给空闲会话虚构任务。后续单 Agent 的 P2-07 不依赖 P2-06 Join，也不自动补入 P1-11 完整本机写入测试门槛；协作和代码完整目标保留。

## 3. H02 必过体验

1. 普通解释/比较/发散能得到有用回答，小歧义给假设或少量解释；缺必需原文仍具体提问。
2. 用户回答问题后原 run_id 接续，历史/输入/未受影响成果保留；无需先停止重新发送。
3. 等待用户超过原主动执行时限仍按剩余额度续跑；取消、费用上限及授权期限分别正确处理。
4. 用户补充纠正明确显示受理/生效状态；页面刷新不重复任务，终态后新请求有独立 Run。
5. 粘贴办公/学术材料产生可读文本或 Markdown 成果、准确引用、逐项核验与合同要求的本人接受。
6. 固定人工样本通过关键事实和证据门槛，记录不必要提问、模型调用/等待/用量/全部失败与 pending费用。

先准备真正可体验版本，再提供实际入口，本人体验与成果接受由用户操作。原 H01 历史和取消状态不改变。本轮不要求用户重新配对/选目录才能测试粘贴文本。

## 4. 发布与分派

P1-12阶段只发布可消费的契约来源，无当前续跑服务实例；它足够A进入P1-13组件开发。B真实联调前需A发布精确服务/来源及正式页面包；不让接口发布伪装成已安装handler。逐包审阅接线，模块回归与跨模块回归按受影响风险执行，汇合里程碑再做一次相应全量。

性能记录以普通无工具调用数、主动执行、用户总等待和接受成果全成本比较 A32；一条 108.5 秒记录只是参考样本。新非关键阈值跑前填写，不凭一条样例宣称普遍加速或质量达标。
