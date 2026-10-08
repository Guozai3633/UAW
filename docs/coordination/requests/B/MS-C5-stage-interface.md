# MS-C5 阶段版：可信登记与当前来源接口

日期2026-10-08，B / dev/context，固定基线ms-i2g-start / 0bd8e2b8387a46e16435dc033956c2b69bb1a859。前两个里程碑提交后继续同包后两个，不等待A最终合入。公共wire/schema/锁无变更。

## 固定构造签名

```python
RegisteredContextInputs(
    *, controller: Principal, records: RecordStorePort, blobs: BlobStorePort,
    transactions: TransactionalStore, runs: RegisteredRunSource | None,
    tool_validator: RegisteredToolValidator | None = None,
)
RegisteredCompositionAuthority(inputs)
RegisteredContextReader(inputs)
RegisteredRuleProvider(inputs)
```

runs结构消费已发布`RunContextSources(records, execution_policy_port)`的authorize/read/is_cancelled；records同时读取实际run.bindings/run.input_sets并校验schema、固定模型及原文集合。controller必须完整service Principal，authenticated_service来自可信适配器，比较全部字段（kind/id/auth_session_id/delegated_by），不能从body生成。注册时绑定实际内部ctx的完整Principal/Scope/Run/model/policy/agent/node，读取和修订比较这些字段。operation/trace/attempt/deadline/budget reservation不改变登记身份，但每次仍执行实际Run/政策/取消/期限检查。此服务不提供HTTP/模型认证；真实入口由A接线。

## 登记和消费

按A指定的三个签名：

```python
material_ref = await inputs.register_material(text, ctx,
    authenticated_service=controller, expected_revision=0, meta=meta)
rule_ref = await inputs.register_rule(rule, ctx,
    authenticated_service=controller, expected_revision=0, meta=rule_meta)
recipe_ref = await inputs.register_recipe(request, rules, tools, ctx,
    authenticated_service=controller, expected_revision=0, meta=recipe_meta)
current = await inputs.recipe(ctx)  # RegisteredRecipe(ref,request,rules,tools,owner)
reading = await inputs.read(material_ref, ctx)
await inputs.revoke(material_ref, ctx, authenticated_service=controller,
    expected_revision=1, meta=revoke_meta)
```

material ID稳定为material-＋hash(Run, ctx.operation_id)，同一operation对应同一材料CAS lineage；不同request_id表示更新请求，不能改变operation来更新同一个材料。正文不strip，1..65536 UTF-8 bytes，固定material/external。SQL存ContextBlock（Ref摘要定位主体blob），正文写主体隔离BlobStore。

rule.id由可信控制入口分配；source_ref必须kind=rule、id=rule.id、version=str(expected_revision+1)，无location/access_scope，若提供hash必须匹配正文。返回实际hash pin。scope必须当前conversation，task/project如提供必须一致，无resource scope扩展；platform/capability_policy/user_current/user_preference/role支持，project/skill未知祖先/激活明确不可用。InstructionRule SQL schema要求正文，故SQL也有确切rule.text，Reader再比对主体blob，不保存无约束Object。

recipe按Run＋agent_step固定ID。request.expected_epoch是本次expected_revision CAS前置条件；保存的ContextRequest.expected_epoch由实际SQL结果revision（expected+1）替换。调用方build使用`current.request.wire()`，不能凭模型猜epoch。返回content Ref摘要覆盖完整request/rules/tools/完整owner，工具来源是同ID/revision的configuration Ref，hash覆盖实际ModelToolSet序列化。request.sources自动补全全部Run原文/补充输入，preserve.required_refs自动保护全体实际原文；不改Run input。

rules.scope_paths/activated_skill_refs尚无真实来源，拒绝；user_instruction_refs作为明确登记rule pin选择列表，每个InstructionRule保留其登记level，平台规则来源只可能是控制入口的rule登记，材料不能进入列表。RuleProvider当前支持空或单规则，不假造多规则语义冲突判断；多个真实规则保留登记，但build明确conflict_assessment unavailable。

工具使用新增B类型`ModelToolSet`严格遵守既有同名公共schema。空工具集合显式登记合法。非空必须注入`RegisteredToolValidator.check(tools: ModelToolSet, ctx) -> None`，查实际trusted discovery/固定版本及当前role/flags/权限；缺port始终unavailable。B不自造Tool目录/executor，也不消费C未交接代码。A后续提供此真实port。

上下文构造中新增内部可选`CompositionBinding.request: ContextRequest | None`，默认None保持原组件语义；registered authority提供实际精确request，B Composer.binding拒绝任意参数不一致，cache键也包括该字段。不是wire/schema变更，不改A src/uaw/composition.py。

## 明确SQL状态和接线

命名空间：context.registered.materials(ContextBlock)、rules(InstructionRule)、recipes(ContextRequest)、recipe_rules(InternalContextRulesRequest)、tools(ModelToolSet)、bindings(TrustedExecutionContext)、catalog(InternalContextSourcesRequest)。相关写在同Run advisory lock事务内、CAS/幂等，owner初次固定revision1；blob先存不可变内容，失败可能留下未引用blob，不授权读取/不伪造成功。材料/规则最多64个每Run登记ID（保守生命周期上限，不靠撤销恢复quota），配方最多64条来源/规则/tool，单登记JSON256KiB。无新表/迁移。删除tombstone拒绝历史版本读取，不复用ID。

可执行接线样例在B测试`tests/integration/context/registered_fixture.py::assemble`，只做构造，不使用fixture CompositionAuthority/Reader/RuleProvider。实际组成：RegisteredContextInputs＋RegisteredContextReader＋RegisteredRuleProvider＋RegisteredCompositionAuthority＋ContextRepository＋FixedModelWindow。controller由可信适配器提供，production channel/authentication仍由A负责。

阶段实际回执：7项真实B PostgreSQL/FS blob通过（50.76s），原Context174单元通过（13.00s），Ruff及Mypy7源码通过。B在自己PowerShell执行`. ./ops/start-dev-db.ps1 -Session B`及alembic，独立55433，无A配置复制；XML保存在tests/.artifacts/B/MS-C5/stage-sql.xml/stage-unit.xml。首次SQL发现binding.request未接线（6通过/1失败），修正后7通过。新whole-operation deadline wrapper随后加入，最终包会复跑。

成功：真实CSV部门预算材料→material/external Ref＋真实平台分析规则→revision1配方/epoch1和当前binding；拒绝：不同controller session、材料冒充rule、非空tools无验证port均失败；重复：同meta材料登记原Ref，并发重复仍revision1，两份CAS修订只有一个成功。这里无模型网络/Runner调用，不声称LLM成果质量。

A可读取本阶段commit提前接线，最终接受仍等同包快照/引用/模型输入及全面SQL回归。P1整轮不因此accepted，flags/D01/D03/D06保持。
