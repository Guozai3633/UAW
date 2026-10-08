# C-005：MS-T2d 阶段版接口与只读接线

日期2026-10-08。目录`E:/UAW/.worktrees/tool`，分支`dev/tool`，固定基线`ms-i2g-start / 0bd8e2b8387a46e16435dc033956c2b69bb1a859`。

**里程碑1/2阶段源码：`27d17a3c2f3d2637ce5c7e386ae6eec3d2a9be63`。** C继续同包里程碑3/4；阶段版不是完整包/产品接受。未读取D开发分支，未改公共schema/锁/组装/API。

## 固定内部签名

```python
ToolInvocation(registry, ledger, budgets, approvals, *, access=None, executor=None,
               estimates=None, results=None, prepare=None)
await invocation.invoke(request, ctx)  # 既有 NormalizeCallRequest -> RuntimeToolruntimeInvokeResult
ToolFacade(registry, ..., invocation=None)  # None 保留原缺发送依赖分支

class ToolExecutorPort(Protocol):
    async def execute(self, call: JsonObject, spec: JsonObject,
                      ctx: TrustedExecutionContext) -> JsonObject: ...  # ProviderReceipt

ToolResponseStore(ledger, blobs, *, provider_ref: Ref, provider: Principal, access=None)
await source.save_response(data, usage, ctx, *, authenticated_provider)  # ProviderReceipt
await source.provider_receipt(ctx)  # 实际固定 ProviderReceipt | None
await source.read_raw(ref, ctx)  # 实际 JSON 字节/摘要/绑定及当前访问复查

class ToolRecoveryAccessPort(Protocol):
    async def check(self, call, spec, ctx, *, provider: Principal) -> None: ...
class ToolOutputVerifierPort(Protocol):
    async def verify(self, data, call, spec, ctx) -> None: ...

TextInspectExecutor(source, *, provider: Principal, currency="USD")
TextInspectVerifier(provider_ref: Ref)
text_spec(provider_ref)  # 只返回元数据，不自动登记
text_estimates(currency="USD")
```

阶段`results`是已批准的局部消费port，`resume(call,ctx)`负责真实结果/恢复链。阶段缺规范器，发送后明确dependency_unavailable，不把ProviderReceipt当ToolResult；后续C提供实际实现，不需要A等待或重写。

## A 可提前准备的组装

```python
ledger = ToolLedger(records)
gates = ToolApprovalAdapter(ledger, actual_tool_authority, real_approval_service)
budget_steps = ToolBudgetAdapter(ledger, budgets, gates, state=budgets)
source = ToolResponseStore(ledger, private_blob_store,
    provider_ref=fixed_registered_provider_ref,
    provider=authenticated_internal_text_service,
    access=current_recovery_data_authority)
executor = TextInspectExecutor(source, provider=authenticated_internal_text_service)
invocation = ToolInvocation(registry, ledger, budget_steps, gates,
    access=current_role_environment, executor=executor,
    estimates=text_estimates(), prepare=executor.check,
    results=durable_result_consumer)  # C里程碑3提供规范器/source接线
facade = ToolFacade(registry, current_role_environment, invocation=invocation)
result = await facade.invoke({"tool_ref": registered_text_spec_ref,
    "action_id": original_action_id, "arguments": {"text": "  原文\r\nKeeṕ exact  "}}, original_ctx)
```

当前ToolAuthority仍显式消费ExecutionPolicyPort与真实配置/角色/resource Reader，provider要求A现有active固定版本；不拿测试metadata冒充真实提供方。`prepare`是绑定executor的纯输入/实现能力检查，在预留之前验证精确spec、参数摘要和UTF-8容量；不是审批替代。完整provider Principal固定在可信构造，不从模型/正文传入。恢复Authority须核查当前完整主体/session、原Run/固定模型/作用域/provider及来源数据权限，不能把ctx/旧approval/Ref回显当授权。

## 已实现语义与阶段回执

- normalize/目录access→真实审批waiting/批准recheck→固定ledger→预算reserve→当前gate→持久意图CAS→预算dispatch记账→当前approval/角色/resource复查→仅首次所有者execute。所有外部await在Tool事务锁外。
- 已有send intent只能resume；CAS或幂等重放不授予第二次发送权，不换attempt重发。缺executor/estimate/实现校验器预留前拒绝。只支持effect=read；网络、用户文件、写入/exec不在本包。
- text.inspect version1，唯一参数text；最多32768 UTF-8 bytes，字符串原样不归一化。输出characters(Python字符数)、utf8_bytes、lines(splitlines，尾部分隔符不新增行)、sha256(原UTF-8)。计算是真实本地行为，不是语义复杂度/LLM判断。
- 内部固定免费计算策略：无模型调用、children、网络/提供方收费；tool_calls=1，wall_time_ms测量实际本地计算。零费用来自该本地实现计费定义，未从transport/HTTP/Runner推断。
- 实际JSON保存主体隔离blob；SQL tool.response.refs=Ref、tool.response.providers=Principal、tool.provider.receipts=ProviderReceipt、tool.invocation.receipts=ProviderReceipt。没有无约束Object永久元数据；raw blob不是规范ToolResult。
- C独立Docker project uaw-development-c/loopback55434，当前worktree自生成`.data/dev-db.env`，迁移head成功。**141单元＋3真实SQL passed，0失败/错误/跳过**，Ruff与21源码Mypy通过。实际SQL验证waiting无预留、批准后真实计算/固定响应、并发只发送一次、重复不发、缺executor/非法容量预留前拒绝。权限/角色metadata明示受控组件，text计算/SQL/blob为实际实现，无LLM/Runner。
- ignored回执`tests/.artifacts/C/MS-T2d-stage/{unit.txt,unit.xml,sql.txt,sql.xml}`；无密码URL入回执或文档，未复制A配置/操作其他库。

里程碑3将补严格业务output_schema＋独立TextInspectVerifier核对，再持久publish/Lookup/Reader和ToolResult，接原reconcile/read_outcome；费用响应丢失、取消和未知结果不会宣告工具成功。里程碑4跑完整C独立SQL与原70回归。生产目录、flags、公共Runtime接线仍由A验收，本阶段没有自动注册text工具或开放产品能力。
