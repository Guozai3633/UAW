import csv,json
from pathlib import Path
R=Path(__file__).resolve().parent
D='2026-10-03'
F='evidence_id content source_name original_url source_type published_at collected_at region population sample_size method supports_conclusions limitations conflict_of_interest counter_evidence_ids confidence label access_status independent_group synthetic'.split()
def writej(n,x): (R/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writec(n,f,x):
 with (R/n).open('w',encoding='utf-8-sig',newline='') as o:
  w=csv.DictWriter(o,fieldnames=f);w.writeheader();w.writerows(x)
E=[]
def ev(id,name,url,type,date,group,content,claims,limits,region='全球/样本地区有限',pop='知识工作者/具体范围见内容',sample='',label='Verified Fact',conf='medium',access='accessed',coi='发布者可能有产品/机构利益',counter=''):
 if sample: limits += ' 样本口径：'+sample+'。'
 sample={'E001':'319','E002':'7137','E003':'16','E020':'3','E021':'1','E022':'1','E023':'7','E024':'1','E025':'1','E026':'1','E027':'2','E028':'1','E029':'1','E030':'1','E031':'1','E032':'1'}.get(id,'')
 if date=='2025-04': date='Unknown';limits+=' 仅取得2025年4月，日Unknown。'
 E.append(dict(zip(F,[id,content,name,url,type,date,D,region,pop,sample,'读取公开正文/指定资料相关章节，人工核对；摘要范围另注明',claims,limits,coi,counter,conf,label,access,group,'false'])))
ev('L001','UAW ARCHITECTURE v0.8','urn:provided:UAW:ARCHITECTURE.md','provided_document','Unknown','uaw-design','设计定义单用户通用工作区、七个逻辑Runtime、本地授权、按需委派和成果核验。','C001;C009;C011','高信心仅针对文档；不是实现或市场结果。',access='provided',conf='high',coi='项目自有设计')
ev('L002','UAW PRODUCT_VALIDATION','urn:provided:UAW:PRODUCT_VALIDATION.md','provided_document','Unknown','uaw-design','三类目标已选，真实反复任务、验收、基线、重复使用与付款均待确认。','C001;C007;C011','文档承认缺口不证明现实没有潜在客户。',access='provided',conf='high',coi='项目自有计划')
ev('L003','UAW DELIVERY_VERIFICATION','urn:provided:UAW:DELIVERY_VERIFICATION.md','provided_document','Unknown','uaw-design','设计区分真实执行、语义满足、版本与用户接受，修改后检查可失效。','C001;C009','尚无实测；不能证明实现可行性。',access='provided',conf='high',coi='项目自有设计')
ev('L004','UAW ACADEMIC_AGENT','urn:provided:UAW:ACADEMIC_AGENT.md','provided_document','Unknown','uaw-design','学术命题、前提、来源定位、复现已在设计中；学科与首发任务未定。','C001;C009','设计协议不能证明专业能力。',access='provided',conf='high',coi='项目自有设计')
ev('L005','UAW ADMIN_CONFIGURATION/RUNTIME_DECISIONS','urn:provided:UAW:ADMIN_CONFIGURATION.md+RUNTIME_DECISIONS.md','provided_document','Unknown','uaw-design','终端用户无需服务API key；平台负担配置/成本；模型继承、撤销保留用户改动是既定方向。','C007;C009;C011','供应商、账单、支持成本、容量未定。',access='provided',conf='high',coi='项目自有设计')
ev('E001','Microsoft Research CHI critical-thinking study','https://www.microsoft.com/en-us/research/publication/the-impact-of-generative-ai-on-critical-thinking-self-reported-reductions-in-cognitive-effort-and-confidence-effects-from-a-survey-of-knowledge-workers/','research_paper','2025-04','ms-critical-thinking-study','作者报告核验、整合与任务管理成为AI辅助工作的思考活动。','C002;C005','中等：自报问卷，相关不是因果，无UAW购买记录。',sample='319人；936事例',label='Reported Evidence',coi='Microsoft作者；与E002不同样本但同机构影响')
ev('E002','Shifting Work Patterns v4','https://arxiv.org/abs/2504.11436v4','research_paper','2025-11-13','ms-work-patterns-study','随机提供集成AI；作者报告后半段使用者每周邮件时间减少两小时，未检测到任务数量/构成变化。','C002;C005;C011','中等：本次核对摘要及版本；使用者子群不是全体ITT；不证明独立工具需求。',sample='66企业；7137人',label='Reported Evidence',coi='Microsoft Research及合作企业',counter='E003')
ev('E003','METR early-2025 developer RCT v2','https://arxiv.org/abs/2507.09089v2','research_paper','2025-07-25','metr-productivity-2025','作者报告早期2025工具条件下任务时间增加19%，而参与者以为提速。','C005;C010;C011','中等：历史工具/熟悉的成熟开源项目；摘要已读，不可泛化2026工具。',sample='16人；246任务',label='Reported Evidence',coi='原研究机构',counter='E004;E002')
ev('E004','METR experiment redesign update','https://metr.org/blog/2026-02-24-uplift-update/','research_update','2026-02-24','metr-productivity-2026','后续实验受不愿停用AI的选择偏差影响，作者认为无法可靠估当前提速。','C005;C010','中等：非当前精确提速估计；与E003同机构，不给需求独立性加分。',label='Reported Evidence',counter='E003')
ev('E005','OpenScholar Nature paper','https://www.nature.com/articles/s41586-025-10072-4','research_paper','2026-02-04','openscholar-study','检索增强与引用支持关系评测改善文献综合；作者明确未证明完全自动化综述。','C002;C004;C010','中等：多个基准子集，主要2024年采集；作者系统自评，不是付款调查。',pop='CS/生医/物理等专家与基准任务',label='Reported Evidence',coi='系统作者参与评价')
ev('E006','UK cross-government Copilot report','https://www.gov.uk/government/publications/microsoft-365-copilot-experiment-cross-government-findings-report/microsoft-365-copilot-experiment-cross-government-findings-report-html','government_trial','2025-06-02','uk-copilot-trial','报告自报日均节省26分钟，并描述复杂数据任务限制和敏感资料顾虑。','C002;C005','中等：自报非完整流程计时；获工具人数不是各问卷分母；政府不是个人采购。',region='英国',sample='超过20000人获工具；调查响应分母不同',label='Reported Evidence')
ev('E007','WorkBuddy product guide','https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Product-Guide','official_documentation','Unknown','tencent-product-docs','公开能力包含授权本地材料、办公交付、多Agent、模型切换、MCP与Skills。','C003;C010','高信心仅公开定位；未实测中文格式质量/准确度。',region='中国站；国际可用性另核',conf='high',counter='E023;E024')
ev('E008','Claude Cowork getting started','https://support.claude.com/zh-CN/articles/13345190-开始使用-claude-cowork','official_documentation','Unknown','anthropic-product-docs','官方介绍多步骤成果、项目/连接工具、计划任务；当前页还介绍云端跨设备会话。','C003;C010','高信心仅公开能力；不能沿用早期仅Mac/本地历史报道。',conf='high',counter='E025;E027')
ev('E009','Claude Code subagents','https://code.claude.com/docs/en/sub-agents','official_documentation','Unknown','anthropic-product-docs','自定义子Agent、独立上下文及工具边界已有公开能力。','C003;C010','高信心仅官方能力；不证明权限继承无缺陷。',conf='high',counter='E032')
ev('E010','OpenAI Developers Codex remote guide','https://developers.openai.com/blog/mastering-codex-remote-for-engineering','official_documentation','2026-06-23','openai-product-docs','官方已有主机/工作区范围、worktree、steering、diff/内联审查与权限选择。','C003;C010','高信心针对工作方式；未核Codex价格与性能。',conf='high')
ev('E011','Cursor pricing','https://cursor.com/pricing','official_pricing','Unknown','cursor-product-docs','Individual Pro $20/月；Teams标准$40/人/月，含Agent及MCP/Skills等。','C003;C007','高信心公开页面；USD/税地区另核，配额不等于无限；非成交/WTP。',conf='high')
ev('E012','Claude pricing','https://claude.com/pricing','official_pricing','Unknown','anthropic-product-docs','Pro月付$20，年付$200，页面约$17/月；列任务、计划、Code等能力。','C003;C007','高信心当次公开报价；不等于无限运行或UAW付款意愿。',conf='high')
ev('E013','Elicit pricing','https://elicit.com/pricing','official_pricing','Unknown','elicit-product-docs','读取分支列免费Basic、Plus年付$132、Pro年付$468及导出/综述；其他行业分支不同。','C003;C007','中等：多行业/计费开关，最低分支不泛化；非付款行为。')
ev('E014','Elicit Routines help','https://support.elicit.com/en/articles/17220392-routines-in-elicit','official_documentation','Unknown','elicit-product-docs','计划找新证据、更新artifact、查看来源与运行历史；Pro/Scale/Enterprise可用。','C003;C004;C010','高信心当前文档；周期更新并非竞品空白；局部保持/中文效果未实测。',conf='high')
ev('E015','Google Drive automatic syncing launch','https://workspaceupdates.googleblog.com/2026/05/keep-your-sources-up-to-date-with-automatic-Drive-syncing-in-NotebookLM.html','official_changelog','2026-05-26','google-product-docs','官方宣布NotebookLM Drive来源自动同步并跟随删除/权限撤销。','C003;C004;C010','高信心官方更新；不等于本地任意材料或报告每条结论自动修订。',conf='high')
ev('E016','Gemini Notebook source limitations','https://support.google.com/gemininotebook/answer/16215270?hl=en','official_documentation','Unknown','google-product-docs','当前说明Drive自动更新；不编辑Drive原文件，不导入其脚注/评论；来源复制有边界。','C003;C004;C010','高信心文档限制；不能推出用户愿为该限制另付费。',conf='high')
ev('E017','Google Sheets AI function','https://support.google.com/docs/answer/15877199?hl=en','official_documentation','Unknown','google-product-docs','AI函数已有生成、总结、分类；依套餐/管理员/语言，有使用限制。','C003;C010','高信心公开能力；简单表格分类不是独特缺口。',conf='high')
ev('E018','n8n pricing','https://n8n.io/pricing/','official_pricing','Unknown','n8n-product-docs','Starter年付折算20欧元/月；按完整workflow执行计量，公开Agent、审批和自托管。','C003;C007;C010','高信心公开套餐；能力依套餐；固定任务可能更适合确定性自动化。',conf='high')
ev('E019','OpenCode security model','https://github.com/anomalyco/opencode/security','official_documentation','Unknown','opencode-product-docs','维护方说明权限交互不提供sandbox隔离，需隔离可用容器/VM。','C003;C010','中等：政策随版本变，不能推出UAW更安全。')
ev('E020','V2EX actual AI work','https://www.v2ex.com/t/1141350','community','2025-06-27','v2ex-1141350','第一人称描述表格撤销重试、代码辅助，亦有人保留固定规则小改动手工处理。','C002;C005;C008','中等：自选技术人群、旧版本，无完整计时/账单，不代表白领。',region='中文社区；地区未知',sample='选3条',label='Reported Evidence',coi='身份/商业利益未知')
ev('E021','V2EX Excel annotation DIY','https://www.v2ex.com/t/1139727','community','2025-06-19','v2ex-1139727','作者因家属手动标注Excel任务自制工具。','C002;C008;C010','低：第三方转述、作者有展示动机，无重复采用/付款。',region='中文社区；地区未知',sample='选1条',label='Reported Evidence',conf='low',counter='E017')
ev('E022','V2EX agent maker notes','https://www.v2ex.com/t/1148052','community','2025-07-28','v2ex-1148052','供给侧作者描述办公文件实时预览/干预困难和未发现错误数据。','C002;C005;C010','低：开发者自报，不用其15%说法当准确率。',region='中文社区；地区未知',sample='选1条',label='Reported Evidence',conf='low')
ev('E023','V2EX WorkBuddy mixed experiences','https://v2ex.com/t/1232713','community','2026-08-07','v2ex-workbuddy-1232713','兼有上手/专家团偏好、免费依赖、额度消耗、长模板失败和按任务选工具。','C002;C005;C007;C008;C010','中等：同线程/同作者不算独立组，账单和失败文件未核，不推普遍质量。',region='中文社区；居住地未知',sample='选7条；非独立人数',label='Reported Evidence',counter='E007')
ev('E024','V2EX WorkBuddy incomplete task','https://v2ex.com/t/1224396','community','2026-07-02','v2ex-workbuddy-1224396','回帖报告封面任务耗额度但仍半成品。','C005;C007;C010','中等：有任务细节未查账单；不采用用户积分汇率。',region='中文社区；地区未知',sample='选1条',label='Reported Evidence')
ev('E025','Reddit Cowork Sheets workflow','https://www.reddit.com/r/ClaudeAI/comments/1rxoncj/anyone_actually_using_claude_cowork_with_google/','community','2026-03-19','reddit-sheets-1rxoncj','OP称本地Excel工作有效，想把外部信息更新现有Sheets并减少导出重上传；评论有Apps Script/Gemini替代。','C002;C004;C008;C010','中等：第一人称绕行、历史版本，不能证明当前仍缺连接器；建议非已用。',sample='选OP1条',label='Reported Evidence',counter='E017;E015')
ev('E026','Reddit mundane Cowork tasks','https://www.reddit.com/r/ClaudeAI/comments/1sfhin6/beyond_the_lifechanging_hype_what_are_you/','community','Unknown','reddit-cowork-1sfhin6','OP实际使用整理文件、多PDF取数成表及项目状态邮件草稿。','C002;C008','中等：具体使用但无计时；绝对日期未取得；自动bot总结排除。',sample='选OP1条',label='Reported Evidence')
ev('E027','Reddit finance adoption/verification','https://www.reddit.com/r/ClaudeAI/comments/1s2hz4o/are_people_in_finance_really_getting_daily_use/','community','Unknown','reddit-finance-1s2hz4o','OP试用先去标识资料；回帖认可公式但仍需大量数字核验。','C002;C005;C008;C010','中等：准备成本和核验自报，非法律/采购证明；日期不明；博客推广回复排除。',sample='选2条',label='Reported Evidence')
ev('E028','Reddit developer non-adopter','https://www.reddit.com/r/ClaudeAI/comments/1wbez51/is_claude_cowork_actually_useful_and_what_do_you/','community','Unknown','reddit-cowork-nonuser','已有coding工具的OP不知Cowork接什么任务/权限而尚未采用。','C005;C008;C010','中等：一个非顾客案例；跨帖只计一次，不能推市场大小。',sample='选OP1条',label='Reported Evidence')
ev('E029','Reddit education Elicit concern','https://www.reddit.com/r/PhD/comments/1istbkr/thoughts_on_elicitcoms_research_results/','community','Unknown','reddit-elicit-1istbkr','教育研究OP怀疑领域覆盖与来源选择；其他学科回复也有正面偏好。','C002;C004;C008;C010','中等：印象不证明数据库只含开放文献；名气不等于质量；旧版本；日期未知。',region='澳大利亚（OP自述）',sample='选OP1条',label='Reported Evidence')
ev('E030','Reddit literature workflow','https://www.reddit.com/r/PhdProductivity/comments/1l9mrwr/whats_your_full_literature_review_workflow/','community','Unknown','reddit-lit-workflow-1l9mrwr','回帖描述筛摘要、读全文、Zotero标注及写作时重读摘录。','C002;C004;C008','中等：真实替代流程自述、无耗时测量；日期未知。',sample='选1条流程回复',label='Reported Evidence')
ev('E031','Cursor stale review backlog','https://forum.cursor.com/t/past-agent-suggestions-wont-go-away-even-when-i-ask-nicely/151723','issue_report','2026-02-12','cursor-backlog-151723','用户称大量Agent生成成功后，已提交改动仍有待审差异积压，影响Git。','C005;C008;C010','中等：详细自报未复现；300文件非样本人数；不能断言当前版本未修。',sample='选OP1条',label='Reported Evidence')
ev('E032','Claude permission inheritance issue','https://github.com/anthropics/claude-code/issues/57118','issue_report','Unknown','claude-permissions-57118','Windows用户报告2.1.132子Agent编辑重复审批，附四轮流水线/复现配置。','C005;C010','中等：自报未执行；不能断言当前仍未修或UAW已解决；发表日未读。',sample='选1条issue',label='Reported Evidence',counter='E009')
ev('E033','Toyota Production System','https://global.toyota/en/company/vision-and-philosophy/production-system/','institution_case','Unknown','toyota-tps-case','Toyota说明jidoka发现异常停线、andon呼叫负责人，区分人机工作。','C006','中等：机构实际机制说明，不是独立效果估计；迁移AI收益未证。',region='日本制造机制；全球说明')
ev('E034','NASA requirements verification matrix','https://www.nasa.gov/reference/appendix-d-requirements-verification-matrix/','institution_method','Unknown','nasa-se-handbook','工程指南将必需要求关联唯一ID、来源与验证方式。','C006;C009','高信心方法说明，无UAW需求/效果/付款证据。',region='美国航天工程',conf='high')
ev('E035','WHO safe-surgery checklist','https://www.who.int/news-room/questions-and-answers/item/safe-surgery-saves-lives-frequently-asked-questions','institution_case','2014-08-20','who-checklist-case','WHO描述三阶段团队检查及早期前后试点改善；同页也讨论Ontario强制推广未见改善研究。','C006;C010','中等：早期前后研究及机构总结，非当前医疗建议；正反同页同组；不可外推AI收益。',sample='8试点；前3733/后3955患者',label='Reported Evidence')
ev('E036','WorkBuddy pricing access limitation','https://www.workbuddy.cn/docs/workbuddy/Pricing','official_pricing','Unknown','tencent-product-docs','搜索索引有套餐金额/优惠，直接读取两次失败，当前有效报价未完整核验。','C007;C010','Unknown：索引含9月30日已截止活动，不用金额当已核实价格。',access='inaccessible',label='Unknown',conf='unknown')
ev('E037','PMC Elicit evaluation unread','https://pmc.ncbi.nlm.nih.gov/articles/PMC12483133/','research_paper','Unknown','unread-pmc12483133','验证码，未取得正文，未采信评价结论。','C010','Unknown：不根据推荐链接/标题猜全文。',access='inaccessible',label='Unknown',conf='unknown')
writec('evidence-ledger.csv',F,E)
V=[]
def rv(id,eid,author,text,para,tags,version='Unknown'):
 e=next(x for x in E if x['evidence_id']==eid)
 V.append(dict(review_id=id,text=text,source_name=e['source_name'],original_url=e['original_url'],published_at=e['published_at'],collected_at=D,region=e['region'],population=e['population'],product_version=version,author_id=author,rating='',synthetic='false',evidence_id=eid,paraphrase_zh=para,manual_themes=tags,text_scope='短原文摘录；语义以同页已读上下文为准'))
rv('R001','E020','pigpigxia','做错了就撤销','表格需要纠正，仍偏好不打开IDE。','office;rework;positive;control')
rv('R002','E020','NoobNoob030','离不开 AI 了已经','Cursor辅助Vue/Python，主观高效。','coding;positive')
rv('R003','E020','codingerj','自己手撸了就','固定写法小改动继续手工，自研项目使用AI。','coding;diy;fit')
rv('R004','E021','yekk','手动给 excel 内容标注','因家属标注任务自制工具；第三方转述。','office;diy')
rv('R005','E022','chnwine','实时预览','供给侧作者难在办公文件及时看见改动/干预。','office;verification;control;supplier_bias')
rv('R006','E023','cowcomic','没啥理解成本','喜欢布局、文件夹、专家团，免费触发试用。','positive;adoption;free')
rv('R007','E023','ktyang','之前的设定忘了','易上手却反复解释，限于轻任务。','rework;fit')
rv('R008','E023','Maxwe11','基本上手就能用','日常杂务有用，专注开发更喜欢CLI。','positive;fit;coding')
rv('R009','E023','ButcherHu','没有免费环境肯定就不用他了','免费环境吸引，无免费明确不用。','free;nonbuyer')
rv('R010','E023','v00O','企业会员','自述企业会员对话很快耗完配额，账单未核。','cost;payment_report')
rv('R011','E023','seven777','有标准模板的 PPT','严格长模板交付失败，泛营销较适用。','quality;templates;fit')
rv('R012','E023','cowcomic','等 workbuddy 的免费期过了','同一作者计划换别的免费工具，非新增独立人。','free;switching')
rv('R013','E024','sillydaddy','还是半成品','封面任务耗额度未完成；不采积分汇率。','cost;quality')
rv('R014','E025','Unknown','avoid exporting from Excel and re-uploading','想让外部数据直接更新既有Sheets，减少绕行。','office;integration;diy')
rv('R015','E026','Sacraack','scan 10+ local PDFs','多PDF取数、整理目录、邮件草稿实际使用。','positive;office;research')
rv('R016','E027','Big-Marionberry-7297','de personalise any work files','试用前先去标识公司资料。','trust;adoption')
rv('R017','E027','maxfield-app','still tons of verification to validate numbers','公式有用，数字仍需大量核验。','verification;positive;office')
rv('R018','E028','Unknown','I don’t even know what tasks to give it','已有coding工具，却不知道通用工作台用何任务。','nonuser;adoption;fit')
rv('R019','E029','Brettelectric','results returned by Elicit are often quite obscure','教育研究者担心覆盖，不能把名气当质量。','research;coverage')
rv('R020','E030','Unknown','write your review based on those fragments','读全文/标注/Zotero与写作重读摘录。','research;diy;verification')
rv('R021','E031','Stephen-S-H','the backlog of changes awaiting my review','大量生成后仍需处理审查积压。','coding;control;rework')
rv('R022','E032','Unknown','~10-12 manual permission prompts','四轮流水线重复审批自报。','coding;approvals;rework','Claude Code 2.1.132')
writec('reviews.csv',list(V[0]),V)
X=[{'candidate_id':'X001','url':next(e['original_url'] for e in E if e['evidence_id']=='E026'),'reason':'自动mod-bot共识总结，不是真实用户反馈'},
{'candidate_id':'X002','url':'https://www.reddit.com/r/ClaudeCowork/comments/1wbezit/is_claude_cowork_actually_useful_and_what_do_you/','reason':'与R018同文跨社区帖子，只计一项非顾客案例'},
{'candidate_id':'X003','url':'https://www.reddit.com/r/notebooklm/comments/1wmbqhd/with_30_sources_loaded_most_answers_cite_the_same/','reason':'问题叙述绑定作者Chrome扩展推广，不计独立客户需求支持'},
{'candidate_id':'X004','url':'https://www.v2ex.com/t/1072963','reason':'工具上线/营收提問，缺终端用户采用结果'}]
writec('selection-exclusions.csv',list(X[0]),X)
writej('manual-cleaning.json',dict(candidate_records=26,manual_excluded=4,script_input=22,count_unit='记录，不是独立用户；R006/R012同作者；未知身份不推断',
method='22条结合上下文人工复核；短摘录保留，另有转述/手工多标签；不采用自动关键词统计作为市场结论',
manual_theme_counts={t:sum(t in v['manual_themes'].split(';') for v in V) for t in sorted({t for v in V for t in v['manual_themes'].split(';')})},
limitations='目的性便利样本；同线程保守计一组；版本和发表日Unknown保留；无全量抓取、访谈、账单或代表性。'))
Q=[
'METR experienced developer productivity randomized controlled trial early 2025 AI 19 percent slower',
'site.microsoft.com research generative AI knowledge workers critical thinking survey 2025',
'site.github.com anthropics claude-code issues overwrites changes permission file',
'site.nature.com AI scientific literature review citations researchers survey 2025',
'site.gov.uk generative AI trial 20000 civil servants 2025 26 minutes',
'site.nber.org generative AI work field experiment 2025 6000 workers',
'site.zhihu.com Claude Cowork 文件 办公 核对',
'site.github.com anomalyco opencode issues 中文 权限',
'site.claude.com pricing Pro Max Cowork','site.elicit.com pricing systematic review','site.cursor.com pricing agents','site.manus.im pricing credits',
'site.reddit.com/r/ClaudeAI Cowork excel report actually use','site.reddit.com/r/PhD Elicit verify papers Zotero',
'site.forum.cursor.com agent changes unwanted files review','site.v2ex.com AI 办公 Excel 实际 使用',
'site.microsoft.com Microsoft 365 Copilot pricing $30','site.support.google.com docs AI function Sheets availability',
'site.notebooklm.google plans citations sources','腾讯 WorkBuddy 官网 本地 文件 Agent',
'site.who.int surgical safety checklist implementation mortality 2009','site.boeing.com maintenance records configuration traceability',
'site.toyota-global.com production system jidoka andon','site.nasa.gov systems engineering verification validation requirements traceability',
'Urbach 2014 introduction surgical safety checklists Ontario hospitals no significant reductions',
'site.reddit.com/r/PhD Elicit literature review citations','site.v2ex.com WorkBuddy 实际 用 任务','site.n8n.io pricing workflows executions',
'Codex app worktrees automations review [domains=developers.openai.com]',
'site.support.google.com notebooklm sources sync Google Drive update manually','site.workbuddy.cn docs 费用 积分','site.elicit.com routines research reports updates']
writej('search-log.json',dict(date=D,timezone='Asia/Shanghai',queries=Q,source_candidates_total='Unknown；扩展结果和重复链接未全量计数',
strategy='任务/实际使用/替代/不采用/正反反馈→官方能力价格→跨行业机制与反例→近期更新核对',
access_register='evidence-ledger.csv；只把实际读到正文的事实纳入；搜索发现不升级',
limitations=['无私人访谈/付费数据库/产品实测','知乎转述/宣传不纳入，中文主要V2EX','NBER落地页失败改同研究arXiv v4摘要','WorkBuddy报价两次失败；PMC验证码；不绕过','Microsoft页面促销与原价混杂，未采用旧$30或促销$18作统一价格','Elicit猜测文章URL失败，改已发现的官方Routines帮助页'],
stopping_rule='重复社区材料不能解决UAW付款、实际任务损失、团队可行性未知；转入最小行为验证。'))
dim='pain_intensity demand_frequency unmet_need market_space willingness_to_pay differentiation reachability switching_ease retention feasibility defensibility expansion risk_control evidence_strength'.split()
O=[]
def op(id,desc,known,fatal=[]):
 a={k:dict(value=None,rationale='Unknown：缺目标任务行为、付款、获客、成本或团队资源证据；不补零。',evidence_ids=[],counter_evidence_ids=[]) for k in dim}
 for k,v,why,ids,ct in known: a[k]=dict(value=v,rationale=why,evidence_ids=ids,counter_evidence_ids=ct)
 O.append(dict(id=id,description=desc,fatal_risks=fatal,ratings=a))
op('O001','周期业务报告：更新材料后保留人工改动，只修受影响表格/报告并交付依据和异常待办。',[
('pain_intensity',3,'Analytical Inference：有绕行/复核记录，目标子群损失未计时。',['E020','E025','E027'],['E007','E017']),
('demand_frequency',2,'Hypothesis：可能周期发生，但尚无目标用户周频。',['E025','E026'],[]),
('unmet_need',2,'Analytical Inference：整合有摩擦，官方已有大量更新能力。',['E025','E027'],['E007','E014','E015']),
('differentiation',2,'Hypothesis：人工修改保持/异常处理能比较，未证明胜过竞品。',['L003','E025'],['E007','E014']),
('switching_ease',3,'Hypothesis：副本与常用格式可并用，准备成本待测。',['E020','E025'],['E027']),
('defensibility',1,'Analytical Inference：框架可复制，任务/口径积累尚无。',['E007','E014'],[]),
('expansion',2,'Hypothesis：相邻报告任务有线索，学术/开发不能外推。',['E026','L002'],[]),
('evidence_strength',2,'Analytical Inference：多组具体自报，没有UAW试用/支付。',['E020','E025','E027'],['E007','E014'])])
op('O002','学术关键命题：有限论文来源定位、反例检查与既有笔记局部修订。',[
('pain_intensity',3,'Analytical Inference：论文和流程自报支持核验劳动，目标学科未定。',['E005','E030'],['E013']),
('unmet_need',2,'Analytical Inference：覆盖/导入限制存在，专业研究工具已解决大量任务。',['E029','E016'],['E005','E014']),
('differentiation',2,'Hypothesis：中文笔记保持和命题证据联动可测，未证实。',['L004','E030'],['E014','E016']),
('switching_ease',3,'Hypothesis：保留Zotero/Word，以文件并用。',['E030','E013'],[]),
('defensibility',1,'Analytical Inference：检索/引用本身不能提供壁垒。',['E005','E014'],[]),
('evidence_strength',2,'Analytical Inference：问题有支持，中文付款主体/学科未知。',['E005','E029','E030'],['E014'])])
op('O003','开发小改动验收包：保留现有修改，关联diff、真实检查和未覆盖目标。',[
('pain_intensity',3,'Analytical Inference：审查积压/审批有案例，目标损失未计量。',['E031','E032'],['E010']),
('unmet_need',1,'Analytical Inference：工作区/diff/steer/审查已成熟。',['E010','E009'],['E031','E032']),
('differentiation',1,'Hypothesis：可用既有工具配置替代，独立收益未明。',['L003','E034'],['E010','E009']),
('switching_ease',2,'Hypothesis：副本只读验收可并用，但接入仍增加成本。',['E031','E010'],[]),
('defensibility',1,'Analytical Inference：成熟工具易复制。',['E009','E010'],[]),
('evidence_strength',2,'Analytical Inference：版本有限具体问题存在，购买未知。',['E031','E032','E003'],['E004','E010'])])
op('O004','补充式只读核验：复核已有AI/人工成果的来源、口径和重大错误，先用服务验证。',[
('pain_intensity',3,'Analytical Inference：复核劳动有用户/研究支持。',['E001','E027','E030'],[]),
('unmet_need',2,'Hypothesis：现有抽查是否已足够，复核是否重复劳动未明。',['E027','E030'],['E005']),
('differentiation',2,'Hypothesis：小范围标准可透明服务测试，独立购买未验证。',['L003','E034'],['E007','E014']),
('switching_ease',4,'Hypothesis：副本只读/差异并用降低写入焦虑，准备成本未知。',['E027','E030'],[]),
('defensibility',1,'Analytical Inference：方法易复制，暂无独占任务资源。',['E005','E034'],[]),
('evidence_strength',2,'Analytical Inference：问题证据存在，净收益与另付费未知。',['E001','E027','E030'],['E005'])])
op('O005','三类群体同时驱动完整通用平台首发，以Agent数量和广功能为卖点。',[
('unmet_need',1,'Analytical Inference：成熟替代多，暂无项目行为结果。',['E007','E008','E010'],['L001']),
('differentiation',1,'Analytical Inference：通用能力重叠，不否定细分机会。',['E007','E009','E010'],[]),
('evidence_strength',1,'Analytical Inference：设计和泛任务不足支撑全范围首发。',['L001','L002'],[])],
['当前首发被阻断：三类真实任务、付款和资源均未验证；暂停此首发假设，不否定通用架构长期方向。'])
writej('opportunities.json',dict(opportunities=O,interpretation='探索顺序按证伪成本，评分不是投资概率。'))
M=json.loads((R/'market-model.json').read_text(encoding='utf-8'))
M.update(currency='USD',year=2026,disjoint_segments=True,disjoint_reason='只建模O001唯一付款账户，承担周期业务报告的中文用户；同人多任务只计一账户，不把办公/开发/学术相加；人数Unknown。')
for s,p,c,cac,fix in [('conservative',144,156,60,12000),('base',180,96,40,12000),('optimistic',240,72,25,12000)]:
 t=M['scenarios'][s]['segments'][0];t.update(id='O001-unique-paying-account',region='全球可合法接入/付款中文用户；国别可用性Unknown',population='周期业务报告唯一付款账户；人数Unknown')
 for k,v in t['parameters'].items():v.update(value=None,label='Unknown',evidence_ids=[],reason='缺符合定义的地域/任务/渠道数据，不能借全球知识工作者总量推断。')
 for k,v in dict(units=1,annual_price=p,retained_customers=0,annual_variable_cost=c,cac=cac,annual_fixed_cost=fix).items():
  t['parameters'][k].update(value=v,label='Hypothesis',reason='商业压力情景，非市场事实/产品报价。费用须含失败重试、搜索、存储、支持和支付，以实际账单/工时替换。')
writej('market-model.json',M)
writej('artifact-assembly-summary.json',dict(ledger_rows=len(E),included_reviews=len(V),queries=len(Q),opportunities=len(O),synthetic_rows=0,note='未执行访谈、产品实测、付款或发布；情景Hypothesis并非假冒观察的测试证据。'))
print(json.dumps({'evidence_rows':len(E),'review_records':len(V),'queries':len(Q)},ensure_ascii=False))

