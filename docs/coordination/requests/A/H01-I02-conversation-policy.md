# H01-I02：普通交流的合理假设与按影响澄清

2026-10-13，本人反馈：“过于严格，连正常交流都有点没有发散思维，这会让用户体验很差”。

## 原因

H01-v2已经解决问题正文不可见；这次是实际回答策略问题。
原模型将未指明具体事务方案和缺少资料当成必须停止的理由。
原角色描述“evidence required”、目标“using actual evidence”没有区分知识讨论与实际动作。
更深的工程规则是CompletionCoordinator看到任何TaskFrame.unresolved，就直接添加blocked检查。
即使Agent给出清楚的条件式解释，后续也会被机械拦截。

本人原文中未明确要求必须提供文档、先确认具体实现或只能依据资料；不能由理解层追加这些硬要求。
这不证明模型对所有含糊请求都应该猜测；需要根据真正影响决定。

## 新策略与模块链

1. Intent理解：保持原文与精确引文，只提取本人明确限制。假设和未知事项仍记录，但属于提示。
   普通比较、解释、聊天和发散不自动附加资料/引用/联网/先确认要求。
2. 主Agent：先给有用解释，含糊时公开合理假设或少量可能解释，简短邀请纠正。
   不把猜测说成事实；假设不授予读写/发布/删除/安装/付费权限。
3. 澄清：只有缺少的信息实质阻止要求的结果或操作范围、且条件式回答也不能提供有用进展，才wait。
   必须读取指定文件/核对具体原文但材料缺失时仍问资料，不编造内容。
4. 工具：需要时动态使用已有工具；没有搜索工具不必阻止基本知识讨论。
   时效数据、真实引用、文件内容、测试和外部动作必须有其真实来源。
5. 完成校验：移除“unresolved非空→blocked”的机械检查。固定Model语义核验读完整原TaskFrame与Artifact，
   按原用户要求判断不确定性是否实质阻止结果；原要求、结构、来源、工具回执、未知效果、取消、版本、期限和接受保持。
   条件式解释可以passed；缺必要来源、错误概念、隐瞒假设或只要求用户补材料仍不能当已交付答案。
6. 发布：新增root/intent v2资源，新理解选择v2；v1资源原字节保留，旧规则读取按原ID/hash，不冒充v2。
   旧已完成操作不重推理、不回填。固定新版启动后只对新请求生效。

没有分类词典、业务关键词开关或固定“TCC答案”分支；语义影响由已有固定用户模型判断。
没有扩大权限、关闭真实证据检查、替用户接受或引入子Agent/DAG。

## 精确开发范围

- A `src/uaw/resources/prompts/agent-root-v2.txt`、`intent-understand-v2.txt`。
- A `src/uaw/context/intent.py` 理解专用平台规则版本，原B通用Context源码不改。
- A `src/uaw/run/background.py` 根Agent规则与角色描述。
- A `src/uaw/agent/completion/delivery.py`、`semantic.py` 校验策略。
- A integration/unit验证及本反馈说明；B页面/C工具/D Runner源码不改。

## 验证与交付

旧/新规则固定字节与交叉hash拒绝；完整SQL中unresolved/assumptions/原目标保留，
passed和blocked由实际语义结果决定，未核验网页来源仍不通过。
另用真实固定DeepSeek对原普通问题和真正缺指定材料样例验收，记录全部原结果、失败、用量和pending费用。
受控回复只证明接线，真实模型样例只证明该次行为，不保证所有提问都能答好。

当前为A续项开发，source/实际测试/固定体验版本完成后另追加准确回执。
同Run内澄清仍未实现，本项不把waiting强制转respond，也不复活本人旧任务。

## 第一组真实样例与额外质量修正

固定初始source `36ff4e10deb2bd0497b556ad273aff9d3fa13f61`：原比较3次实际DeepSeek调用，
action=respond，得到实际Artifact和passed报告；原unresolved仍保留，说明机械拦截已解除。
缺论文原文样例2次调用，action=wait且问题实际可见，没有编造论文。
这5次调用行为链通过，不代表普通样例文字都准确：人工检查发现假设性方案被表述为常见实现，
并出现过于绝对的锁、性能/可用性概括；固定模型自身passed没有充分发现这些问题。

原样例和1.25 USD pending预留保留，不能覆写为最终质量通过。
根提示词再增加简明核心解释、少量已知候选、保持概念层次、假设实现不当产品事实、依赖实现的保证须限定；
语义核验同样检查这些问题，不设置TCC/ZK专用答案或关键词分支。
修改固定为新的refined source后仅复跑原普通问题，用新测试身份/原固定用户模型。

人工技术核对参考[Apache ZooKeeper internals](https://zookeeper.apache.org/doc/current/zookeeperInternals.html)
与[Apache Seata TCC mode](https://seata.apache.org/docs/user/mode/tcc/)。它们用于A核对样例概念，
不是UAW工具读取的来源，不能作为UAW已联网/有真实文档引用的证据。

## 最终固定与实际边界

最终source bc9458c3fd93d62290cae3ab6cce4c04f968f065 / ms-i2l-a32-refined-source。23定向通过、215类型/7静态格式通过。
8次真实Model行为样例：一般比较给正文、指定材料缺失提问；15744/4417Token，2.00 USD pending预留，原失败与用量保留。
细化复测仍有概念过度对立/TCC无中心裁决的错误，自核验仍passed；人工技术质量不接受，后续真实质量门槛明确保留。
H01-v4实际原用户入口ready/登录刷新，原两cancelled旧任务不变；H01-v3未启动，旧答/快照保持。
两临时测试服务清理完成，数据库与费用记录保留，不操作BCD或代点本人。
[实际反馈与体验](../../../implementation/human-tests/H01-I02.md) · [回执](../../../implementation/evidence/ms-i2l-a32.json)。
