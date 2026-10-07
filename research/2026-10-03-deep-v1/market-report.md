# UAW 市场机会深度研究

研究 ID：UAW-2026-10-03-deep-v1｜版本：1.0｜模式：Deep Research  
研究/采集日期：2026-10-03（Asia/Shanghai）｜范围：全球市场，中文用户作为首批切口  
输入：项目根目录已有产品与架构文档；公开研究、官方产品资料和公开社区反馈。  
决策：先判断有无值得验证的真实任务，再判断 UAW 能否带来可支付的增量结果。本文是机会研究，未开展用户访谈、产品对比实测、收费、联系或发布。

标签含义：Verified Fact＝已核对资料中的事实；Reported Evidence＝作者/用户报告，未经本研究独立复现；Analytical Inference＝证据上的分析；Hypothesis＝待检验假设；Unknown＝没有足够材料。官方能力已核对不代表实际质量已验证。证据 E/L 编号对应第12部分和完整台账。

## 01. Executive Summary

**建议保留 UAW 的通用工作区方向，用一个反复发生的交付任务验证其价值。优先实验是“周期报告更新后，保留人工修改，只修受影响内容，并交付可定位依据与异常清单”。** 这是实验优先级，不是已经成立的市场定位。【C008 Hypothesis；E020、E025—E030、L002】

需求查证的结果分三层：

1. **真实任务存在。** 用户实际把多 PDF 取数成表、整理文件、撰写状态草稿、阅读/标注文献、修改代码交给 AI，也继续投入撤销重试、核验数字和审查改动。研究显示 AI 可在某些任务节约时间，但收益取决于任务、工具和使用方式。【C002、C005 Reported Evidence；E001—E006、E020、E025—E031】
2. **通用能力已经有强供给。** WorkBuddy、Cowork、Codex 等已覆盖 UAW 构想中的许多基础能力；Elicit 有周期研究更新，NotebookLM 已有 Drive 自动同步。多 Agent、本地文件、引用、计划任务都不能独立证明空白。【C003 Verified Fact/Analytical Inference；E007—E019】见 [WorkBuddy 产品指南](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Product-Guide)、[Elicit Routines](https://support.elicit.com/en/articles/17220392-routines-in-elicit)、[Google 自动同步更新](https://workspaceupdates.googleblog.com/2026/05/keep-your-sources-up-to-date-with-automatic-Drive-syncing-in-NotebookLM.html)。
3. **UAW 的商业需求尚未验证。** 未取得目标用户的任务频率、完整流程耗时、重复使用、真实付款、获客成本或生产成本记录。现有架构是设计依据，不能当采用证据。【C001 Verified Fact；C007 Unknown；L001—L005】

机会收敛：O001 周期业务报告优先；O002 有限文献的关键命题核验作为第二方向；O004 补充式核验服务作为低成本实验形态；O003 开发验收包暂后置；O005 三群体同时完整平台首发暂被阻断。所有前四方向均“待验证”，没有方向通过开发投入的商业证据门槛。

最小行动：48小时内找3位确有重复报告任务的中文使用者，查看其最近两次真实修订过程；若存在实际损失，再用现成工具加透明人工服务跑一次对照交付。先验证问题与净收益，随后验证第二次使用和真实付款。【C011 Analytical Inference；L002、E002、E003；实验详见 validation-plan.md】

## 02. Market Landscape

**市场边界以任务定义。** UAW 对应的是“把自己的材料、文件、代码转成可修改、可核验的成果”的执行工作区。上下游包括模型与搜索供应商、知识/文件来源、Runner 与权限、文件格式/办公生态、用户或组织采购。通用聊天、生成内容、企业流程编排、学术检索、IDE Agent 和人工服务存在交叉，但客户人数不能直接相加。【C003 Analytical Inference；L001、E007—E019】

| 供给层 | 主要替代 | 客户保留它的合理原因 | UAW 尚须证明 |
|---|---|---|---|
| 通用任务工作区 | WorkBuddy、Cowork | 易上手、已有授权和生态、免费/订阅预算已占用 | 同一完整任务更少返工、成本可接受 |
| 开发执行 | Codex、Claude Code、Cursor、OpenCode | 仓库上下文、diff、现有工作流与权限配置 | 接入后仍有净收益 |
| 文献与来源工作区 | Elicit、NotebookLM/Gemini Notebook、Zotero | 搜索、引用、已有笔记与文献管理 | 特定学科/中文笔记的验证收益 |
| 办公原生/确定性自动化 | Google Sheets AI、Apps Script、Excel公式/脚本、n8n | 简单规则稳定，已有资料与协作关系 | 为什么规则或原生工具不够 |
| 人工/不行动 | 自己核对、助理、现有模板、延后处理 | 不增加学习/资料整理成本 | 损失足够高且付费者可行动 |

公开供给已相当丰富，准确率、格式保真、局部修订、成本和任务验收仍需实测；本研究不宣称整个市场成熟或完全未被满足。模型和 Agent 快速更新构成后来者风险，既有供应商增加更新、审查或权限能力会迅速消除功能缺口。【C003、C010 Analytical Inference；E004、E007—E019】

中文首批切口指语言与任务渠道，不等于仅中国大陆。国家/地区支持、模型供应、账号与支付、组织数据许可必须在招募时记录。全球可服务客户数仍 Unknown；不能用中文人口或全球知识工作者人数直接替代。【C007 Unknown】

## 03. Voice of Customer

**研究方法与分母。** 使用任务词、实际使用、失败、替代和不采用等查询，保存32条查询。公开反馈是目的性便利样本，中文主要来自 V2EX，英文主要来自 Reddit、Cursor 论坛和 GitHub。不是全量抓取，也不是随机抽样。

人工候选26条，排除4条（bot总结、同文跨帖、工具推广、没有终端使用结果），脚本输入22条、有效22条、精确重复0、近重复候选0、Synthetic 0。R006/R012 同作者不同观察，仍只算一个独立来源；同线程不当多个独立组。22是记录数，不是22位客户。版本多数 Unknown，7条反馈日期 Unknown，4条作者 Unknown；这些材料只支持行为线索，不能代表当前版本表现或需求率。

用原上下文人工多标签。正面偏好6条、返工4条、DIY4条、核验3条、免费依赖3条，主题重叠；这些计数描述本次选取材料。自动关键词工具对中文短摘录覆盖不足，未用其主题计数下结论。清洗和短原文见 reviews.csv、manual-cleaning.json、cleaned/。

| 观察 | 具体行为及证据 | 正面/反面一起解释 | 不能推出 |
|---|---|---|---|
| AI 已进入真实杂务 | 多PDF取数、目录整理、状态邮件；E026/R015 | 任务有价值，现成工具已经能做 | UAW有独立需求 |
| 纠错依然由人承担 | 表格撤销重试，公式有用但数字仍要核验；E020/R001、E027/R017 | 可控性有用；核验本来也是专业工作 | 每个人都痛、全自动最合适 |
| 资料与成果之间绕行 | 想减少Excel导出、Sheets重上传；E025/R014 | 有整合摩擦；同帖存在Apps Script/Gemini替代 | 2026仍无连接器或必须换平台 |
| 格式要求影响适配 | 严格长PPT模板失败；E023/R011 | 泛营销材料可能适用；任务边界决定收益 | 已证实所有中文格式效果差 |
| 免费与易用带来试用 | 专家团/文件夹理解成本低；E023/R006、R008 | 必须保留这些优势；同作者计划换免费工具 | 试用、积分消耗等于付款 |
| 替代流程有合理性 | Zotero读全文/标注/摘录；E030/R020；固定小改动手工；E020/R003 | 保留专业习惯可能比替换更好 | DIY用户愿为平台付费 |
| 执行规模产生审查负担 | Cursor审查积压；子Agent重复权限提示；E031/R021、E032/R022 | 详细案例有诊断价值，未复现 | 当前所有版本都未修 |
| 非采用者缺少任务映射 | 已有coding工具却不知Cowork接何任务；E028/R018 | 使用门槛也可能是没有新增需要 | 全部非顾客是潜在客户 |

原始页：[实际办公与代码使用](https://www.v2ex.com/t/1141350)、[WorkBuddy 正反反馈](https://v2ex.com/t/1232713)、[Sheets 绕行](https://www.reddit.com/r/ClaudeAI/comments/1rxoncj/anyone_actually_using_claude_cowork_with_google/)、[数字核验](https://www.reddit.com/r/ClaudeAI/comments/1s2hz4o/are_people_in_finance_really_getting_daily_use/)、[文献工作流](https://www.reddit.com/r/PhdProductivity/comments/1l9mrwr/whats_your_full_literature_review_workflow/)。【C002、C005 Reported Evidence】

独立研究补充与矛盾：
- CHI研究调查319位知识工作者、936个事例，描述核验、整合和任务管理；自报与相关关系不代表AI导致质量下降。[Microsoft Research](https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/)【E001】
- 66企业、7137人随机提供集成工具；作者报告后半段使用者邮件时间约每周少两小时，未检测到任务数量/构成变化。这里是使用者子群描述，不当全体平均因果效果；本次读取摘要。[研究v4](https://arxiv.org/abs/2504.11436v4)【E002】
- 早期2025 METR实验，16位熟悉成熟开源仓库的开发者、246任务，报告时间增加19%；历史窄样本不能断言当前AI普遍减速。2026后续实验遇到拒绝不用AI的选择偏差，机构不提供可靠当前提速估计。[历史实验](https://arxiv.org/abs/2507.09089v2)、[2026更新](https://metr.org/blog/2026-02-24-uplift-update/)【E003、E004】
- 英国政府试点超过2万人获工具，报告自报平均每日节省26分钟；获工具人数不是全部问卷分母，也未独立计时。组织工具效用不等于个人买新工具。[政府报告](https://www.gov.uk/government/publications/microsoft-365-copilot-experiment-cross-government-findings-report/microsoft-365-copilot-experiment-cross-government-findings-report-html)【E006】

因此需测“准备—执行—核对—修正—导出—接受”全部成本，不能只测生成速度或满意度。【C005 Analytical Inference】

## 04. Customer Segmentation

以下是行为分层，不是编造 Persona。任务频率/损失/预算除明确自报外均 Unknown；渠道列是待试验渠道，尚未招募。

| 八类 | 已见行为/状态 | 使用者与付款者 | 候选渠道与验证 |
|---|---|---|---|
| 重度使用者 | 自称离不开Cursor；E020/R002 | 使用者；付款主体/额度Unknown | 开发社区；看真实变更验收成本 |
| 普通使用者 | 目录、多PDF与邮件；E026 | 自己使用；个人或单位支付Unknown | 中文办公社群；最近一次成果和复用 |
| 不满使用者 | 长模板失败、数字核验；E023、E027 | 使用者未必能采购 | 业务报表/财务运营；看失败材料与处理代价 |
| 已流失者 | 未取得已发生流失证据；R012仅计划换免费产品 | Unknown | 需补招过去30天实际停用者 |
| 替代方案使用者 | 手工小改、DIY脚本、Zotero；E020、E021、E030 | 自己/实验室/公司均待问 | Excel/Zotero/行业社群；原生工具强基线 |
| 有需要但未购买者 | 看见免费依赖；尚不等于有强需要且无预算；E023 | 付款意愿Unknown | 试用者；以具体任务与价格选择验证 |
| 因价格/复杂度/信任拒绝者 | 无免费不用；试用前去标识；E023、E027 | 数据批准者可能另有人 | 先核资料权限、准备成本，不承诺“本地=不出网” |
| 尚未意识到路径者 | 已有coding工具不知通用台怎么用；E028 | 使用者；新增预算Unknown | 演示其现有任务；无真实任务就排除 |

三层非顾客：①即将离开者：免费期结束计划迁移（Reported Evidence），不是已流失；②主动拒绝者：价格/资料焦虑（Reported Evidence），需区分没有预算与不愿提供材料；③行业尚未覆盖者：本次没有可证实的人群规模或渠道（Unknown），不能把教育研究的覆盖抱怨推成整个学科空白。

**首批任务假设。** 当新材料或新月份数据到来，负责周期报告的中文业务运营/分析人员希望更新已接受报告，保留已改文字和口径，快速定位变化及需自己决定的异常，拿到可继续编辑的文件。【C008 Hypothesis；E025—E027】情绪收益是假设的可控与放心；社会收益是假设的可对同事解释；不能代替实际验收。

旅程：收到材料 → 整理权限/格式 → 判断哪些旧结论受影响 → 更新表格和叙述 → 核验数字/来源 → 人工修改 → 接受/交付 → 下期再用。记录每步主动工时、等待、交接对象、失败恢复。采购者可能是主管/IT、付款者可能公司；若使用者无法自主试用，当前单用户实验应换可授权的小范围任务，不能假设采购已解决。

学术次切口：已有3—10份可授权全文与既有中文笔记，对5—10条重要命题核对来源、前提、反例，并更新受影响段落。学科、论文访问、导师要求、付款者均未知。保留Zotero/Word习惯；不以“完整自动综述”进入。【C008 Hypothesis；E005、E029、E030、L004】

## 05. Competitive Gap Analysis

| 同一结果问题 | 官方已可做的事 | 剩余缺口状态 | 选择现有方案的原因 |
|---|---|---|---|
| 本地材料→办公成果 | WorkBuddy公开本地任务、多Agent、模型与办公交付；Cowork公开文件/连接工具、多步骤任务 | 中文严格式、局部修订与完整核验净收益Unknown | 上手容易、已订阅/免费、目录习惯 |
| 周期更新报告 | Elicit Routines找新证据、更新artifact和运行历史；NotebookLM Drive自动同步 | 多来源/人工改动保持/逐结论失效边界需实测 | 现成垂直检索和来源生态 |
| 来源可定位与综述 | Elicit/NotebookLM；OpenScholar显示检索及引用支持的潜力 | 目标学科/中文命题与笔记质量Unknown | 已有专业工具与引用流程 |
| 小代码修改→可信验收 | Codex工作区/steering/diff与审查；Claude Code子Agent；Cursor IDE整合 | 用户特定验收漏项、版本失效规则Unknown | 已有仓库上下文、低切换成本 |
| 固定表格规则 | Sheets AI函数、Apps Script、公式；n8n完整workflow | 规则足够时UAW可能无增量 | 稳定、低费用、无需新平台 |

依据：[Cowork 官方](https://support.claude.com/zh-CN/articles/13345190-开始使用-claude-cowork)、[Codex 官方工作方式](https://developers.openai.com/blog/mastering-codex-remote-for-engineering)、[Notebook 来源限制](https://support.google.com/gemininotebook/answer/16215270?hl=en)、[Sheets AI](https://support.google.com/docs/answer/15877199?hl=en)、[OpenScholar](https://www.nature.com/articles/s41586-025-10072-4)。【C003 Verified Fact；C004 Analytical Inference；E005、E007—E018】

已证实的是能力重叠与特定文档限制；**“竞争者无法保留人工修改并核验交付”没有被证实**。缺口长期存在的可能原因包括需求分散、异常处置昂贵、格式组合长尾、客户愿自己抽查、原生生态已足够。这些都是 Hypothesis，不是竞争企业战略内幕；E014—E017 是它们已经投入解决的反例。【C004、C010】

迁移四力：推动力是重复整理/核验/返工；吸引力是接受成果更快；焦虑是资料权限、错误责任、覆盖人工改动、收费不可控；牵引是既有Office/Zotero/IDE、同事格式、已有订阅。一次性成本包括连接/导入/学习/许可，持续成本包括复核、支持、协作与退出格式。初期副本试用、常用文件导出和局部并用是 Hypothesis，需计时证明足以降低成本。【E020、E025、E027、E030】

| 七条路线 | 本研究取舍 |
|---|---|
| A 不满意用户 | 有案例，但不给“抱怨者都会迁移”结论；筛到重复同一任务者才试 |
| B 被忽视细分人群 | 中文周期报告/中文学术笔记候选；“被忽视”尚未知 |
| C 新用户任务 | 当前证据不足，不以新颖任务首发 |
| D 连接割裂流程 | O001可测试；先和原生自动化比，连接本身非独特 |
| E 降低采用门槛 | 有需要线索但强竞品已有优势；副本/成品试用可测，不单独成为卖点 |
| F 新交付/商业模式 | 透明人工辅助、按小任务交付可先验需求；规模与责任成本未验证 |
| G 先成为补充工具 | 当前优先：并用文件核验/局部更新，不要求换掉现有工作台 |

## 06. Cross-Industry Discovery

底层问题是：输入变化后旧成果何处失效、人应该何时接管、什么才算交付通过。三领域都有实际源机制；迁移到 UAW 的商业收益均是 Hypothesis，不因类比而成立。【C006 Analytical Inference】

| 源行业与真实案例 | 实际机制与效果边界 | UAW机会假设 | 目标需求证据与最小检验 |
|---|---|---|---|
| 汽车制造：Toyota TPS | jidoka检测异常停线、andon叫负责人；官方说明真实组织机制，没有本研究独立效益估计 | 从“持续多Agent生成”变为“正常自动、异常定位后由人决定”；把注意力集中到需判断的单元格/命题 | E020/E027有纠错核验；用同样报告比较完整复核与异常清单，测漏错和主动工时 |
| 航天工程：NASA验证矩阵 | 需求唯一ID、来源、验证方式可追溯；方法存在不等于万能质量保证 | 将用户目标→成果位置→依据/实际检查→版本关联；材料或用户改动后显式使受影响验收失效 | E030/E031有来源/审查劳动；L003/L004已有设计；人工做5条目标追溯，看是否更快找到失败 |
| 外科手术流程：WHO检查表（远行业） | 三关键阶段、角色确认；早期多点前后试点改善，同页也谈Ontario强制推广未见改善 | 少量必要检查置于授权前、接受改动前、交付前；用户“接受”与程序成功分别记录 | E027/E032有信任/审批摩擦；对比每次工具弹窗与语义边界检查，测打断次数和遗漏 |

来源：[Toyota TPS](https://global.toyota/en/company/vision-and-philosophy/production-system/)、[NASA 矩阵](https://www.nasa.gov/reference/appendix-d-requirements-verification-matrix/)、[WHO 正反案例](https://www.who.int/news-room/questions-and-answers/item/safe-surgery-saves-lives-frequently-asked-questions)。【E033—E035】

九项结构类比（源侧明确内容来自上述材料；其余组织激励/付款判断为 Analytical Inference）：

| 维度 | Toyota源→UAW | NASA源→UAW | WHO源→UAW |
|---|---|---|---|
| 任务 | 生产合格物→交付可用成果 | 满足工程要求→满足用户重要目标 | 安全完成操作→在边界避免关键遗漏 |
| 流程 | 检测/停线/处置→定位异常/接管/续做 | 需求/验证矩阵→目标/成果/真实检查 | 三节点确认→少数授权/接受/交付节点 |
| 资源 | 产线传感与标准→工具日志与任务标准，后者常缺 | 专业测试资源→有限搜索/解析/人工检查 | 临床团队培训→单用户规则，专业责任不可复制 |
| 协作 | 操作者/负责人→同一用户分时接管即可 | 多学科接口→不同材料/工具接口 | 团队发声→用户审查，不能只加更多Agent |
| 决策 | 可识别异常停线→模糊语义需人判 | 验证与验证需求价值分离→执行成功与用户接受分离 | 安全检查后仍有判断→检查通过不等于正确决策 |
| 时间 | 即时生产→周/月报告，停整任务代价不同 | 生命周期/变更→成果版本与改动失效 | 关键时刻→少量可撤回边界 |
| 信息 | 现场可见异常→给位置/依据/变化 | ID与来源链→目标、引用、检查链 | 口头明确确认→可审查状态；不能用自评分代替证据 |
| 风险责任 | 工厂质量责任→用户与服务交付责任待界定 | 工程验收责任→任务事实标准/未覆盖项 | 医疗责任→不能迁移到一般办公的效果与责任 |
| 付款者 | 企业质量投入→个人/小团队预算Unknown | 项目资助→用户是否为追溯另付费Unknown | 医疗组织→UAW个人付费不可由此推出 |

不可迁移因素：制造有稳定标准，知识工作标准经常含糊；NASA矩阵维护有成本，小任务可能不值得；手术团队风险、培训、协作和强制制度与单人办公不同。WHO反例说明检查表形式化可能没有收益。若异常清单漏重大错误、矩阵维护超过节省时间、节点更多却未减少风险，则淘汰相关迁移，而非增加更多检查。【C010 Analytical Inference；E035】

完整迁移边界和逐实验条件见 cross-industry-map.md。

## 07. Opportunity Map

| ID / 机制 | 需求类别与目标 | 支持 / 反证 | 商业已知部分分/100；覆盖；未知区间 | 证据/5；状态 |
|---|---|---|---|---|
| O001 流程连接+异常更新 | 成熟任务，局部未满足待验证；周期报告责任人 | E020/E025/E027；E007/E014/E015/E017 | 45.00；52%；23.4—71.4 | 2；待验证，优先实验 |
| O002 命题追溯+笔记保持 | 成熟学术任务，学科缺口待验证 | E005/E029/E030；E013/E014/E016 | 46.34；41%；19.0—78.0 | 2；待验证，次选 |
| O003 代码目标验收包 | 成熟且强供给任务 | E031/E032；E009/E010、E004反历史外推 | 34.63；41%；14.2—73.2 | 2；待验证，暂后置 |
| O004 只读核验服务 | 补充交付模式；是否重复劳动未知 | E001/E027/E030；E005、现成审查 | 49.27；41%；20.2—79.2 | 2；待验证，可作实验形态 |
| O005 三群体通用完整首发 | 宽范围供给假设，没有聚焦行为结果 | L001/L002；E007/E008/E010 | 20.00；18%；3.6—85.6 | 1；当前首发淘汰/阻断 |

评分是基于部分证据的分析判断，数值不是客观概率；Unknown未填零。13项商业维度＋独立证据轴见 opportunities.json，26个单项权重±20%情景见 scores.json。局部排名即使变化不大也无法消除全部区间重叠和覆盖差异；O004分数高不代表商业更优。关键支付与可行性门槛缺证据，O001—O004全部未通过。

优先 O001 的理由是：有具体可观察文件/人工改动、可重复同类任务、能用现有工具与人工在小预算内证伪，且与既有成果/版本设计接近。频率、净收益、付款、可触达仍未知。O004是可降低实验成本的交付方式，不能把其少接入误当高需求。【C008、C009 Hypothesis；C011 Analytical Inference】

## 08. Market Potential

**不提供无依据全球规模。** 年份2026、币种USD、单位为“唯一付费账户/年”。只模型化 O001，办公/开发/学术重叠者不重复计数。符合周期任务定义的全球中文客户数、问题发生率、可服务人数、渠道触达/转化、交付与获客容量全部 Unknown，因此三情景 TAM/SAM/SOM 均 null。数值未知不等于零。【C007 Unknown】

模型：
- TAM＝符合用户定义的客户数×问题发生率×每账户单位数×年价格。
- SAM＝实际可服务、可接入和可付款的同定义账户×年价格。
- SOM＝受渠道转化、获客容量及交付容量限制的账户＋实际留存账户，再乘年价格；期初留存设0只是未取得UAW客户的建模起点。
- 同一人多任务仍计一个账户；若转向企业采购或逐任务收费，重建模型，不能沿用个人账户假设。

下面仅为**成本压力情景 Hypothesis**，不是报价、预算承诺、营收预测或市场平均成本。

| 情景 | 年收入/账户 | 年可变成本/账户 | 年贡献/账户 | 假设CAC | 回收月数 | TAM/SAM/SOM |
|---|---:|---:|---:|---:|---:|---|
| 保守 | $144 | $156 | -$12 | $60 | 不成立 | Unknown |
| 基准 | $180 | $96 | $84 | $40 | 5.71 | Unknown |
| 乐观 | $240 | $72 | $168 | $25 | 1.79 | Unknown |

固定成本压力假设$12,000/年；未有客户数，营业贡献仍 Unknown。基准只是$15/月价格和$8/月可变成本的算术，人工支持稍多便可能破坏贡献；不算无留存证据的LTV。

定价参考只是替代预算：[Claude Pro](https://claude.com/pricing)月付$20/年付$200；[Cursor](https://cursor.com/pricing)Pro月付$20、Teams标准$40/人/月；[n8n](https://n8n.io/pricing/)Starter年付折算€20/月。这些公开报价不是客户成交，更不是愿意额外买UAW。【E011、E012、E018 Verified Fact】
Elicit价格有行业/计费分支，本次分支看到Plus年付$132、Pro年付$468，不能泛化为统一最低价。WorkBuddy报价正文两次读取失败，索引还含9月30日截止活动，未采金额。Microsoft促销与原价分支、Notebook套餐动态页未完整核价，不用旧价格做优势比较。【E013；E036 Unknown】

成本记账必须包含：模型全部尝试、搜索/解析、失败重试、存储、支付、人工交付/复核/支持、准备和数据迁移；免费额度另记，不能记作可持续零成本。每份被接受成果成本＝总尝试成本÷被接受份数；无人接受时不报有限单价。用户节约的时间不等于平台盈利。

收入假设比较：月订阅适合经常重复且复核成本可控；按有限任务交付便于初次验证但人工交付难规模化；纯核验补充包减少迁移但易成为重复检查。个人愿付、主管批准、组织预算需分别观察。【C007 Unknown；C008 Hypothesis】

增长信号是第二次实际任务、停止补贴后继续使用与付款；衰退信号是免费期轮换、原生能力覆盖、Agent生成更多却增加审查。E023是免费驱动/配额自报，E004是“难让使用者不用AI”的相反信号，均不代表市场增长率。【C010 Analytical Inference】

## 09. Differentiation & Market Entry

十项方向说明，每一项保留证据与未知；两条路线均处于实验阶段。

| 项目 | O001 周期报告 | O002 关键命题/笔记 |
|---|---|---|
| 1 目标用户 | 中文周期业务报告责任人；Hypothesis E025—E027 | 已有全文、中文笔记且需核验的人；Hypothesis E029/E030 |
| 2 重要任务 | 新资料到来更新已接受报告，保留人工口径 | 核对少数命题并修受影响笔记 |
| 3 现有不足 | 绕行/核验案例存在；目标当前原生工具不足Unknown | 覆盖和来源限制有材料；目标学科不足Unknown |
| 4 不同价值 | 成果位置—证据—异常—人工修改联动；Hypothesis L003 | 命题—前提—来源—反例—版本联动；Hypothesis L004 |
| 5 可量化收益 | 全流程主动工时、重大错、被覆盖人工改动、接受次数 | 支持定位率、漏反例、核验工时、笔记保持 |
| 6 尝试理由/并用 | 用副本回到常用表格/文档；用户不需先迁移工作台 | 保留Zotero/Word，限制3—10篇与5—10命题 |
| 7 首次触达 | 中文业务/Excel社群、允许展示真实任务的同行；渠道Hypothesis | 中文研究方法/Zotero社群或可接触实验室；渠道Hypothesis |
| 8 成熟企业未占据原因 | 不能断言未占据；长尾口径/支持成本为Hypothesis，已有周期功能反证 | 垂直工具已投入；具体学科中文笔记边界Unknown |
| 9 复制后剩余优势 | 若存在：用户授权形成的口径、验收实例与修订历史；当前无壁垒证据 | 若存在：学科标准、可复核命题/反例库；当前无独占资源 |
| 10 留存/口碑机制 | 下一期沿用已接受成果与规则；实际重复使用Unknown | 新证据影响旧命题并被用户继续采用；实际频率Unknown |

中文支持、好界面、本地授权、多Agent都是竞争条件或待检验体验，不能直接当可持续优势。第一份成果应让用户看见具体变化、核验依据和未完成项；承诺对象是任务结果，内部Runtime结构不进入用户销售话术。【C003、C009 Analytical Inference/Hypothesis】

扩展需要新证据：O001到相邻报告先证明相同数据口径/异常模式可复用；到学术或开发需分别重做任务标准、素材许可、付款与渠道；团队协作需验证角色和组织采购，不能仅沿用单用户留存。

## 10. Critical Review

| 反向问题 | 已有反面证据/替代解释 | 推翻或暂停条件 |
|---|---|---|
| 是否只是现成产品功能组合？ | E007—E018已有广泛功能及周期更新 | 原生配置在可接受成本内完成同一任务，就淘汰该差异假设 |
| 是否把“核验”误当自动化需求？ | E027/E030核验也是专业工作；E005强垂直供给 | 用户仍必须重读全部来源，净工时未降 |
| 是否把“有用”误当增量？ | E002/E006显示集成工具有用 | 相比用户最好现有工具不更好 |
| 是否把历史失败当当前机会？ | E004提醒旧RCT不能泛化；旧帖可能已修 | 当前版本复现不了问题或供应商已解决 |
| 是否把免费喜欢当付费？ | E023免费轮换/不付费；E024额度不是账单 | 只愿免费、第二次实际任务不回来 |
| 是否忽略完整成本？ | 准备资料、核验、格式修正、客服可能占多数 | 支持工时使贡献为负；失败尝试也计成本 |
| 是否让核验器自己误判？ | L003只是设计，不是可信度证明 | 漏重大错误/过度自信，无可定位依据 |
| 是否用形式化矩阵代替成果？ | E035推广反例、NASA维护负担 | 工具状态全绿但实际不能接受 |
| 是否可以用更简单方式？ | DIY、Sheets原生、n8n、现有脚本 | 固定规则或只读服务已足够，改用更小方式 |
| 是否真的能交付？ | 团队、运行账单、Runner实现/跨平台测试未查得 | 未能在明确授权素材上稳定完成有限任务 |

资料权限/组织数据规则、国家可用性、实际文件保真和模型出网路径需针对试用资料核对；本地Runner不自动等于离线推理。未取得具体法律/采购结论，不把广泛“合规”当市场壁垒。

最大 Unknown：目标任务的周/月频率、损失、真正付款人、付费替代预算、可接入素材、技术和人工成本、重复使用与可获取客户。全部可能推翻首选方向。【C007、C010】

## 11. Validation Roadmap

全为建议实验，尚未执行；不承诺团队资源或日程。首轮用现成工具与透明人工辅助，验需求后再决定实现范围。详细计时表、访谈问题、付款与停止规则见 validation-plan.md。

| 窗口 | 动作/样本 | 继续条件（预设决策阈值，不是人口统计） | 暂停/放弃 |
|---|---|---|---|
| 48小时 | 3位报告责任人，最近2次真实修订材料/过程；核任务、授权、基线 | ≥2/3在上月重复发生≥2次，且每次主动损失>30分钟或有可证实的交付风险；能提供授权副本 | 没有重复任务/素材，或原生工具5—10分钟解决 |
| 两周 | 先访8人：4业务、2学术、2开发作比较；核心试验另补足5位O001用户，每人2个匹配任务，10尝试全记 | ≥4/5用户主动时间中位数改善≥30%且≥15分钟/任务；≥4/5用户两次任务均可接受（至多一次修订且计时）；0重大错/人工改动被覆盖；≥3/5主动选择下一真实任务 | 净收益不达、重大错、只有创始人重度人工救火；判别问题无需求还是方案失败 |
| 付费观察（两周后有足够时间则开始） | 对所有成功与失败都保留记录；明确限额与人工服务，给统一试验价格 | 第一付费周期≥3/5实际支付；下一周期≥2/5再用且实际续付，未到期则Unknown | 口头说愿付、只收可退预约、朋友帮忙不算通过 |
| 条件式30天 | 两周净收益通过再实现一个实际任务流程；5位用户持续实测 | 相比强基线保持收益，重大错0，失败成本可追踪 | 不通过则不扩平台；重做切口或O004实验 |
| 条件式60天 | 资源足够且付款通过，扩到10—15位、连续3个周期 | 观察按周期留存与全部成本；单位贡献为正，人工服务可持续 | 依赖免费额度/不可持续人工就收缩 |
| 条件式90天 | 前面通过才试第二渠道/相邻任务 | 新渠道仍有真实付款和交付，新增任务单独验收 | 没有留存或获客成本回收不成立，不扩展 |

阈值为本研究 Hypothesis，先做基线，允许在比较试验开始前修正并冻结；不能看完结果再调阈值。小样本用于决定下一步，不宣称PMF或显著性。

责任建议：项目负责人招募/冻结规则/记录成本；任务拥有者提供素材并验收；独立复核者盲查关键数字/来源/修改保持。若仅一人兼职所有职责，记录偏差并缩小测试，不假定已有这些人。首轮预算上限假设$150现金＋20小时研究/交付人工；每种工时分别记录，超预算即停并调整范围。未开展任何招募发送、收费或发布。

## 12. Evidence Appendix

### 结论—证据索引与适用边界

| Claim ID / 标签 | 陈述与证据 | 推理/适用范围/不确定性 |
|---|---|---|
| C001 Verified Fact | 文档规划单用户通用工作区、版本成果和核验；L001—L005 | 仅证文档内容；没有证明实现或采用 |
| C002 Reported Evidence | 真实AI辅助材料交付/代码/研究任务存在；E001/E002/E005/E006/E020/E025—E030 | 多类型实际报告；不是代表性需求率或UAW需求 |
| C003 Verified Fact + Analytical Inference | 官方能力重叠；E007—E019 | 能力事实支持通用差异未证；效果/套餐地区待实测 |
| C004 Analytical Inference | 周期/同步已有供给；剩余局部修订缺口未知；E014—E017/E025/E029/E030 | 不能宣布更新空白；历史用户问题可能已解 |
| C005 Reported Evidence + Analytical Inference | 核验返工/准备存在，净收益要完整计量；E001/E003/E004/E006/E020/E023—E032 | 自报和窄实验；无普遍程度，历史不代表当前 |
| C006 Analytical Inference | 三源机制可作为实验假设；E033—E035 | 源存在不等于目标有效；激励/责任不同 |
| C007 Unknown | UAW付款、频率、市场数量、获客和成本未知；L002/L005；E011—E013/E018/E023/E024/E036 | 报价/额度不是UAW成交，三情景非市场事实 |
| C008 Hypothesis | 中文周期报告优先，学术次选；E020/E025—E030/L002 | 按证伪成本选实验，不宣称分层已代表市场 |
| C009 Hypothesis | 既有成果/版本协议有望适配可信交付；L001/L003—L005/E034 | 设计适配不证明实现质量或优势 |
| C010 Analytical Inference | 原生替代、补贴、维护、历史变化可能消除机会；E003/E004/E005/E007—E019/E023—E035 | 反例用于边界和停止；各来源独立性见台账 |
| C011 Analytical Inference | 先验证有限任务再扩大投入；L001/L002/L005/E002/E003 | 当前证据足以开展低成本实验，不足以证明值得完整开发 |

### 文件与验证

- evidence-ledger.csv：42条（5条项目资料组、37条外部材料）；40条已读/提供，2条不可访问。记录内容、链接、日期/采集日、样本口径、独立组、利益关系、反证和局限。
- reviews.csv：22条短原文与中文转述；selection-exclusions.csv：4条人工排除；manual-cleaning.json：人工主题；cleaned/：脚本清洗，无Synthetic。
- search-log.json：32条查询、访问限制和停止理由；不是全部搜索候选数量统计。
- competitor-matrix.csv、cross-industry-map.md、customer-pain-map.md、opportunity-map.md：专项视图。
- opportunities.json / scores.json：部分评分、Unknown、门槛和26种敏感性情景。
- market-model.json / market-estimates.json：互斥账户模型、三种假设情景、null规模。
- validation-plan.md、task-observation.csv：可执行实验与空白真实记录表；未填写模拟客户。
- ledger-check-v3.json：修正日期/样本格式并补WHO已读发布日期后通过；旧ledger-check.json保留原失败记录。结构通过不验证真实性/代表性。
- build_research.py：数据组装来源，非产品实现；artifact-assembly-summary.json：未执行外部行动声明。

发布日期未知显式保留；如CHI论文只读到2025年4月则不编造日。研究论文摘要支持范围另注，不声称全部全文已读。已访问来源按同研究/同公司/同线程合组，避免将多个页面当独立验证。官方资料存在供应商利益，社区有自选/幸存/推广/版本偏差，数据不外推总体。

未采信：WorkBuddy报价正文不可访问且索引优惠过期（E036）；PMC论文验证码（E037）；NBER读取失败改同研究arXiv摘要，非两独立研究；Manus/Microsoft/Notebook动态报价未完整核价；旧项目评审中的外部断言不自动承袭。没有绕过访问限制。

本地资料覆盖：ARCHITECTURE、PRODUCT_VALIDATION、FRONTEND_BLUEPRINT、ADMIN_CONFIGURATION、RUNTIME_DECISIONS、CONTROL_TOOLS读取相关内容；DELIVERY_VERIFICATION与ACADEMIC_AGENT读取目标/验收章节；CRITICAL_REVIEW与CACHE_DESIGN、LOCAL_APPROVAL_SEMANTIC按相关章节查阅。没有把demo模拟成功标记当生产结果，没有运行产品性能测试。

阶段0—9均完成桌面研究/分析产物；阶段2/3的代表性访谈与现场观察受限，阶段7/8的可行性、付款、成本验证未执行，阶段9只形成实验方案。15个决策问题索引：1—3见§02/04/05；4—5见§03/08；6—7见§04/05；8—10见§06；11—13见§09/11；14见§09/11；15见§10/11。


### 可读来源索引

以下为来源索引；完整样本、独立组、利益关系、局限与反证见 evidence-ledger.csv。Unknown是发布日期未取得，均于2026-10-03采集。

| ID | 来源 | 发布日 | 标签/访问 |
|---|---|---|---|
| L001 | UAW ARCHITECTURE v0.8 | Unknown | Verified Fact / provided |
| L002 | UAW PRODUCT_VALIDATION | Unknown | Verified Fact / provided |
| L003 | UAW DELIVERY_VERIFICATION | Unknown | Verified Fact / provided |
| L004 | UAW ACADEMIC_AGENT | Unknown | Verified Fact / provided |
| L005 | UAW ADMIN_CONFIGURATION/RUNTIME_DECISIONS | Unknown | Verified Fact / provided |
| E001 | [Microsoft Research CHI critical-thinking study](https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/) | Unknown | Reported Evidence / accessed |
| E002 | [Shifting Work Patterns v4](https://arxiv.org/abs/2504.11436v4) | 2025-11-13 | Reported Evidence / accessed |
| E003 | [METR early-2025 developer RCT v2](https://arxiv.org/abs/2507.09089v2) | 2025-07-25 | Reported Evidence / accessed |
| E004 | [METR experiment redesign update](https://metr.org/blog/2026-02-24-uplift-update/) | 2026-02-24 | Reported Evidence / accessed |
| E005 | [OpenScholar Nature paper](https://www.nature.com/articles/s41586-025-10072-4) | 2026-02-04 | Reported Evidence / accessed |
| E006 | [UK cross-government Copilot report](https://www.gov.uk/government/publications/microsoft-365-copilot-experiment-cross-government-findings-report/microsoft-365-copilot-experiment-cross-government-findings-report-html) | 2025-06-02 | Reported Evidence / accessed |
| E007 | [WorkBuddy product guide](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Product-Guide) | Unknown | Verified Fact / accessed |
| E008 | [Claude Cowork getting started](https://support.claude.com/zh-CN/articles/13345190-开始使用-claude-cowork) | Unknown | Verified Fact / accessed |
| E009 | [Claude Code subagents](https://code.claude.com/docs/en/sub-agents) | Unknown | Verified Fact / accessed |
| E010 | [OpenAI Developers Codex remote guide](https://developers.openai.com/blog/mastering-codex-remote-for-engineering) | 2026-06-23 | Verified Fact / accessed |
| E011 | [Cursor pricing](https://cursor.com/pricing) | Unknown | Verified Fact / accessed |
| E012 | [Claude pricing](https://claude.com/pricing) | Unknown | Verified Fact / accessed |
| E013 | [Elicit pricing](https://elicit.com/pricing) | Unknown | Verified Fact / accessed |
| E014 | [Elicit Routines help](https://support.elicit.com/en/articles/17220392-routines-in-elicit) | Unknown | Verified Fact / accessed |
| E015 | [Google Drive automatic syncing launch](https://workspaceupdates.googleblog.com/2026/05/keep-your-sources-up-to-date-with-automatic-Drive-syncing-in-NotebookLM.html) | 2026-05-26 | Verified Fact / accessed |
| E016 | [Gemini Notebook source limitations](https://support.google.com/gemininotebook/answer/16215270?hl=en) | Unknown | Verified Fact / accessed |
| E017 | [Google Sheets AI function](https://support.google.com/docs/answer/15877199?hl=en) | Unknown | Verified Fact / accessed |
| E018 | [n8n pricing](https://n8n.io/pricing/) | Unknown | Verified Fact / accessed |
| E019 | [OpenCode security model](https://github.com/anomalyco/opencode/security) | Unknown | Verified Fact / accessed |
| E020 | [V2EX actual AI work](https://www.v2ex.com/t/1141350) | 2025-06-27 | Reported Evidence / accessed |
| E021 | [V2EX Excel annotation DIY](https://www.v2ex.com/t/1139727) | 2025-06-19 | Reported Evidence / accessed |
| E022 | [V2EX agent maker notes](https://www.v2ex.com/t/1148052) | 2025-07-28 | Reported Evidence / accessed |
| E023 | [V2EX WorkBuddy mixed experiences](https://v2ex.com/t/1232713) | 2026-08-07 | Reported Evidence / accessed |
| E024 | [V2EX WorkBuddy incomplete task](https://v2ex.com/t/1224396) | 2026-07-02 | Reported Evidence / accessed |
| E025 | [Reddit Cowork Sheets workflow](https://www.reddit.com/r/ClaudeAI/comments/1rxoncj/anyone_actually_using_claude_cowork_with_google/) | 2026-03-19 | Reported Evidence / accessed |
| E026 | [Reddit mundane Cowork tasks](https://www.reddit.com/r/ClaudeAI/comments/1sfhin6/beyond_the_lifechanging_hype_what_are_you/) | Unknown | Reported Evidence / accessed |
| E027 | [Reddit finance adoption/verification](https://www.reddit.com/r/ClaudeAI/comments/1s2hz4o/are_people_in_finance_really_getting_daily_use/) | Unknown | Reported Evidence / accessed |
| E028 | [Reddit developer non-adopter](https://www.reddit.com/r/ClaudeAI/comments/1wbez51/is_claude_cowork_actually_useful_and_what_do_you/) | Unknown | Reported Evidence / accessed |
| E029 | [Reddit education Elicit concern](https://www.reddit.com/r/PhD/comments/1istbkr/thoughts_on_elicitcoms_research_results/) | Unknown | Reported Evidence / accessed |
| E030 | [Reddit literature workflow](https://www.reddit.com/r/PhdProductivity/comments/1l9mrwr/whats_your_full_literature_review_workflow/) | Unknown | Reported Evidence / accessed |
| E031 | [Cursor stale review backlog](https://forum.cursor.com/t/past-agent-suggestions-wont-go-away-even-when-i-ask-nicely/151723) | 2026-02-12 | Reported Evidence / accessed |
| E032 | [Claude permission inheritance issue](https://github.com/anthropics/claude-code/issues/57118) | Unknown | Reported Evidence / accessed |
| E033 | [Toyota Production System](https://global.toyota/en/company/vision-and-philosophy/production-system/) | Unknown | Verified Fact / accessed |
| E034 | [NASA requirements verification matrix](https://www.nasa.gov/reference/appendix-d-requirements-verification-matrix/) | Unknown | Verified Fact / accessed |
| E035 | [WHO safe-surgery checklist](https://www.who.int/news-room/questions-and-answers/item/safe-surgery-saves-lives-frequently-asked-questions) | 2014-08-20 | Reported Evidence / accessed |
| E036 | [WorkBuddy pricing access limitation](https://www.workbuddy.cn/docs/workbuddy/Pricing) | Unknown | Unknown / inaccessible |
| E037 | [PMC Elicit evaluation unread](https://pmc.ncbi.nlm.nih.gov/articles/PMC12483133/) | Unknown | Unknown / inaccessible |
