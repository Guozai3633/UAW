# MS-C6 阶段接口（里程碑 1/2）

基线 ms-i2h-start / f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8；Session B 在 E:/UAW/.worktrees/context、dev/context。仅 B 允许目录；新 port 在 context/ports.py，建议校验在 readers.py，不新增公共 schema。

```python
class RegisteredRuleAssessor(Protocol):
    async def assess(self, candidates: tuple[RuleCandidate, ...],
                     ctx: TrustedExecutionContext) -> RulePlan: ...

provider = RegisteredRuleProvider(inputs, assessor=fixed_model_assessor)
# 旧构造 RegisteredRuleProvider(inputs) 保留，空/单规则无需 assessor。
# 多规则无 assessor -> CapabilityUnavailable("context.rules.conflict_assessment")。
components.rules.provider = provider  # 示例；生产应在 A 的可信组装时注入。
```

A adapter 使用实际固定用户 Model，不导入私有 ProviderRequest。candidates 和 ctx 均深复制；返回 RulePlan 必须包含全部候选，实际 rule 正文/级别/作用域/完整 Ref、原选择顺序及 targets 不能改变。候选最多 64，topic/value 单字段最多 4096 UTF-8 bytes，语义 metadata 总量最多 256 KiB。受控评估器只验证协议，不证明 LLM 判断质量；B 不解释正文词典。

输出示例（相同语义格式建议）：

```python
RulePlan(tuple(replace(c, topic="answer_format", value="plain", critical=True)
               for c in candidates), assessment_complete=True)
# 显式澄清：conflict_refs 只能是固定 candidates 的完整实际 source_ref。
# 后来的 user_current 修正：同 topic，order 为实际较后顺序，supersedes=(旧 rule.id,)。
```

平台/能力政策候选必须保持 critical=True，不允许跨级覆盖；即使语义同值，解析器保留全部平台和能力政策正文。actual Runtime 当前权限仍由独立来源检查；assessment_complete/critical/topic 均不授权。所有候选（包括被覆盖的低优先级候选）仍作为 snapshot dependencies 复查。

失败：格式/metadata -> context_assessment_invalid；不完整 -> unavailable 或 context_assessment_incomplete；重复/未知/非完整 conflict Ref -> context_assessment_reference_conflict；改身份/顺序/targets 或输入变异 -> context_assessment_identity_conflict；不支持覆盖 -> context_assessment_override_denied；重要冲突 -> rule_conflict，evidence_refs 为实际完整候选。材料、规则、配方、工具、实际 Run 原文/patch、当前权威、固定模型、取消和期限在模型 await 前后复查；来源变化拒绝，模型异常后仍复查。任务取消直接传播；公用组件包装已有取消结果；stalled assessor 受可信 deadline 整体限制。

语义 adapter 同一固定候选若给出不同语义 metadata，会使现有 InstructionSet version/snapshot 校验失败，不能借旧快照继续生成。A 接线需提供稳定的实际语义建议，并处理澄清/不可用。下一阶段继续测量真实 SQL/Reader/assessor 成本，不缓存模型建议或授权状态。

阶段验证和源码 SHA 见 B handoff。阶段不是完整链或 P1 验收；继续本包里程碑 3/4。
