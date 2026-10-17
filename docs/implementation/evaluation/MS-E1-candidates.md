# MS-E1 v1 候选题集（待人工核对）

16条候选，修订/保留集各8条，分别保留id/version/split。所有条目 **needs_human_review**，没有人工已审记录、真实模型输出或正式质量通过。不得用受控标签训练/调试后声称保留集已实测；A首次实际导出前先固定suite SHA及策略阈值。

办公3、学术2、普通技术4、缺材料2、合理歧义3、纠正2；覆盖总量/基数/费用未知、虚构学术材料摘要与引文、概念层次、原错误、未知写恢复、必需材料澄清、无谓阻断及纠正保留要求。题目及必要事实逐项在suite.json，事实语义只供独立证据审查，不编码关键词评分或TCC专用分支。

办公、学术和其余材料是明确人工构造的练习输入，不是真实订单、论文或用户会话。关键数值可由原文直接核对；没有补作者、DOI或生产回执。可审不等于已经人工审过。

技术一手资料于 **2026-10-17T02:42:49Z** 实际打开核对：

- [Apache Seata TCC Mode](https://seata.apache.org/docs/user/mode/tcc/)，页面显示v2.6；Overview/Overall Mechanism给业务层TCC、资源预留/锁粒度、TM协调及实现责任的具体语境。
- [Apache ZooKeeper Internals](https://zookeeper.apache.org/doc/current/zookeeperInternals.html)，页面显示3.9文档；Atomic Broadcast、Quorums和Consistency Guarantees分别约束协调/提交与读写语义。

每条primary_source明确具体section/段落、URL、实际捕获UTC和本次核对中文摘要的UTF8 SHA256。该hash只固定选取摘要，不是整个网站、原HTML或外部真伪证明；需要人工按原资料语义核对，不能把机器摘要冒充人工判断。current链接未来可变，本轮只声明此时实际读取；后续刷新需新增suite版本，不能重写旧来源。

TCC/ZooKeeper旧错纳入概念层次与具体实现反例，保留集另有普通读与资源锁/幂等反例；没有把此一题做成通用正确性分类器。其余12条照同一独立review接口处理。字符串只保持原文本/hash，不判断语义正确。

附manifest是 **controlled_fixture/unrun placeholder**；observations/reviews均空，执行CLI必须incomplete/N/A，绝非0错误通过。实际候选/基线的全部失败、用量、pending费用及人审由A提供后才能M4比较，不把本题集或界面文档当实际模型验收。
