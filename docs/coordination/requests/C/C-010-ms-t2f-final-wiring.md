# C / MS-T2f：办公纯参数工具、有限路由及恢复接线

日期：2026-10-09。目录 E:/UAW/.worktrees/tool，分支 dev/tool。
基线 ms-i2i-start = d8023eb07e1460961782f297697da7428f6ad247；开工干净，fetch/ff-only成功，
HEAD与标签commit相同，uv sync --frozen --extra agent-engine --link-mode copy成功。
M1源码63857e4d684ef3d9581778dc443126a5b84f3f03、M2源码5387624a69db68297bed78297bcb414463e25fe0。
最终源码 SHA：**b09fb7d789026be69a26b5493aa3a7da13649be5**。C组件验证完成，A组合/产品验收仍待接线。

## 实际实现与兼容边界

固定参数/Spec/精度/百分比定义/JSON节点计数见[C-009](C-009-ms-t2f-stage-tools.md)，
M1签名及ToolSpec/hash保持不变。新增arithmetic.calculate@1、data.inspect_json@1的实际纯函数、
executor和verifier；text.inspect代码/Spec不改。每个结果从原参数重新计算，实际CPU计时和
本地免费tariff写严格Usage；原参数、JSON原文及固定模型不改变。

有限路由ToolExecutorRouter/ToolOutputVerifierRouter沿用现有execute/verify签名：
1..128个显式可信bindings，完整configuration Ref/hash/provider Ref冻结用于查找，
重复id/version（不同hash也算重复）、未知工具/改版/提供方不符拒绝。
每条executor binding另提供同步prepare检查；规范化及有界计算发生在预算预留前，
结果schema和确切适配器的语义验证分别执行。不动态import，不通过类别或模型Python路径找实现。

PureParameterResourceReader仅接受三种完整精确ToolSpec/Ref。resolve先验证规范call/hash/参数，
然后读取当前Access，返回空资源前再核对当前注册binding、角色/资源/配置权限。
无Access或未实现的资源工具不返回空列表，不把参数中的路径/Ref当授权。
PureParameterRecoveryAccess核对原已登记action/attempt/spec，委托独立当前数据权限端口，
await后重读原绑定。它不走新执行_access，不reserve/派发/换attempt，不忽略当前数据撤销。
新增ready()仅检查authority已接线；ToolResults.ready可调用这一可选依赖检查，使缺嵌套权威
在预留预算前明确返回dependency_unavailable。ready不是授权缓存，每次实际读取仍完整check。

原ToolInvocation仍唯一拥有一次发送CAS；原Source保存实际Blob/ProviderReceipt，原Results发布
ToolReconciliationReceipt/ToolResult；原Lookup/read_outcome重新核对实际证据/版本/owner/session。
恢复使用同一工具Ref对应验证器及原attempt、固定费用计划。效果与费用独立，unknown保留额度；
无实际回执、超时或未收到返回均不能推出未执行/免费；不自动重试。Local tariff为0仅针对实际
本地纯计算，模型账务仍独立。没有任何Tool会话事务锁跨BudgetService调用。

## A接线样例

```python
# A先登记合法本地provider、完整authenticated_service、当前Role/ToolAccess/Run数据权限。
# 不使用DeepSeek聊天API作为executor，不把受控测试注册映射给产品。
registry = ToolRegistry()
specs = (arithmetic_spec(local_provider_ref), json_data_spec(local_provider_ref),
         text_spec(local_provider_ref))
for spec in specs:
    registry.register(spec, expected_revision=registry.revision,
        binding=AdapterBinding(local_provider_ref, frozenset({environment}), implemented=True))
pins = tuple(Ref.model_validate(registry.reference(e)) for e in registry.snapshot()[1])
resources = PureParameterResourceReader(registry, current_access, pins)
recovery = PureParameterRecoveryAccess(resources, ledger, authority=current_data_authority)
verifiers = (ArithmeticVerifier(local_provider_ref), JsonDataVerifier(local_provider_ref),
             TextInspectVerifier(local_provider_ref))
verifier = ToolOutputVerifierRouter(tuple(ToolOutputVerifierBinding(pin, local_provider_ref, impl)
    for pin, impl in zip(pins, verifiers, strict=True)))
source = ToolReceiptStore(ledger, real_blobs, provider_ref=local_provider_ref,
    provider=authenticated_local_service, access=recovery, verifier=verifier)
executors = (ArithmeticExecutor(source, provider=authenticated_local_service),
             JsonDataExecutor(source, provider=authenticated_local_service),
             TextInspectExecutor(source, provider=authenticated_local_service))
executor = ToolExecutorRouter(tuple(ToolExecutorBinding(pin, local_provider_ref, impl, impl.check)
    for pin, impl in zip(pins, executors, strict=True)))
# 使用真实ToolApprovalAuthority(..., resources=resources, policies=ExecutionPolicyPort)、
# ToolApprovalAdapter/ToolBudgetAdapter(BudgetPort+BudgetStatePort)，均与ledger同源。
reconciler = ToolReconciler(ledger, budget, receipts=source, evidence=source)
results = ToolResults(source, reconciler)
invocation = ToolInvocation(registry, ledger, budget, approvals, access=current_access,
    executor=executor, estimates=arithmetic_estimates(), prepare=executor.check, results=results)
facade = ToolFacade(registry, current_access, invocation=invocation,
    lookup=source, reconciler=reconciler, retriever=optional_explicit_retriever)
# facade.invoke({"tool_ref": pins[0].wire(), "action_id": 已固定action_id,
#                "arguments": {"operation":"percent","operands":["1200.00","7.5"]}}, ctx)
# 先实际waiting approval，批准及当前资源复查后产生value="90.000"。
# facade.read_outcome(action_id,ctx)读实际outcome；不能把confirmed/ok当Task完成。
```

三工具tariff同构，每个实际调用tool_calls=1；用户模型费用另记。重启重建同一Spec/Ref/映射和
Source/Verifier/Results，只读原已持久派发意图，可以不装executor/新执行access/approvals。
缺映射/Reader/current_data_authority明确不可用，不能根据旧approved或Ref生成恢复权。
Source每实例只绑定一个provider，多个provider需A按原attempt/provider选择对应结果Source/facade；
本包不新增通用跨provider结果混合器。路由逐binding允许不同provider且必须准确匹配实现。

## 最小公共/组装请求（仅交A，C未修改）

1. A在composition/目录/角色登记三Spec、精确完整bindings及合法本地ProviderBinding/Principal。
   现行ToolSpec/Call/Receipt/Result/EffectRecord足够，本包不要求新DTO或迁移/依赖。
2. A提供独立当前ToolRecoveryAccessPort：核对实际完整owner/session、Run/固定模型/scope，
   当前角色与数据可见性、原provider身份/版本/状态/固定及当前配置；取消/期限停止新执行，
   当前数据访问仍允许时可完成原费用计划；数据撤销则禁止读取。
   原RunToolRecoveryAccess以PureTextResourceReader声明类型，可由A提取其自身权威逻辑并复用
   C Reader.entry的精确三工具检查；最小改动是A的资源端口类型/显式RunToolAccessSources接线，
   不放宽为任意无资源工具，不让C访问A私有role记录或冒充生产权威。
3. 原可选retriever/index继续默认兼容；真实embedding/缓存由A管理，未生成假向量或注册产品。
   A用固定DeepSeek实际选择可见工具并做Task交付/完成控制验收；C不修改用户模型或聊天发送器。

影响消费方：A组装、目录/角色、Run结果数据权限适配；无B/D开发分支依赖，无API/flag扩展。
没有上述生产来源的默认实例拒绝发送/恢复；测试授权和提供方登记明确受控，不能计实连LLM或
生产能力。工具正确计算、ToolResult.succeeded或outcome.applied均不能代替Task完成。

## 实际验收回执

ignored根：`tests/.artifacts/C/MS-T2f`。自身55434已启动并迁移，SQL新进程Database.check()
实际确认版本`0003_attempt_identity`。没有复制A配置/凭据/共享evidence。
verification-index.json仅原pytest回执索引及最后节点去重，不制作合成JUnit。

| 实跑 | 回执stem（.txt/.xml） | 实际结果 |
| --- | --- | --- |
| 全部C unit | all-unit-final | 316 passed，原218+本包98，19.40秒 |
| 原Tool全部SQL（含检索/索引24） | original-sql | 124 passed，543.42秒 |
| 新工具链首轮 | office-sql-initial | 30 passed/6 failed，455.00秒；3缺嵌套authority提前拒绝、3误用discover签名 |
| 新工具链修复复验 | office-sql-fixed | 36 passed/3 failed，689.78秒；3测试误用candidates字段 |
| 原text最终源码复验 | text-final-sql | 30 passed，340.53秒，不加重复节点 |
| 新进程/无来源/未知/跨主体 | office-recovery-sql | 15 passed，194.55秒 |
| tools字段修复定向实跑 | mixed-final-sql | 3 passed/36 deselected，2.25秒；非skip |

本包新SQL 54 distinct（新工具模块39+新恢复模块15）；原124+新54=**178个最终通过节点**，
没有最终测试失败/错误/跳过。39项模块通过由office-sql-fixed的36通过+mixed-final-sql的3通过
对应节点证明，不冒称一次39全部通过；原30重跑不重复计数。原70+text30+retrieval24仍保留，
旧SQL文件未改。费用回复丢失发生在实际SQL commit之后，重启按原计划幂等恢复；原发送unknown
无回执不换attempt，额度继续held。三个工具覆盖并发一次调用、撤销/取消、参数变化、错验证器、
篡改和费用恢复。新进程读取实际SQL/Blob且未构造executor、审批或新执行Access。
角色/provider元数据和当前数据权限权威明确受控，纯计算、Blob/SQL/审批/预算服务为实际实现；
不计真实LLM选择质量，不注册为产品能力。

静态：Ruff通过、62个C源码/测试文件format-check通过、Mypy 30个Tool源文件通过。
`git diff --check`通过；public-boundary.json核对schema/shared/锁/Run源与基线字节相同。
最初m1-unit-initial以及m2-unit/m2-unit-fixed的测试写法/受控receipt错误同样完整保留，M1/M2
阶段说明已解释；最终正确使用现有transport_status、Usage.currency和DiscoveryResult.tools，未放宽合同。

主要命令（实际每次另有本包独立basetemp、junitxml和重定向）：

```powershell
. ./ops/start-dev-db.ps1 -Session C
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m pytest tests/unit/tool -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests/integration/tool -q -p no:cacheprovider --require-postgres
.venv/Scripts/python.exe -m pytest tests/integration/tool/test_office_tools_postgres.py -v -p no:cacheprovider --require-postgres
.venv/Scripts/python.exe -m pytest tests/integration/tool/test_office_recovery_postgres.py -q -p no:cacheprovider --require-postgres
.venv/Scripts/python.exe -m pytest tests/integration/tool/test_office_tools_postgres.py -k mixed_registry -v -p no:cacheprovider --require-postgres
```

原text最终复验指定test_text_dispatch_postgres.py、test_text_results_postgres.py、
test_text_recovery_process_postgres.py。最初全目录124项是在新增SQL前实跑，随后新模块实跑；
未声称一次全目录178项通过。

交付过程补充回执：自动审批审查曾因额度用尽无法完成提交（无操作执行、不是不安全判定）；
用户“继续”后同范围重新审查成功，源码已提交，未绕过检查。所有测试结束后的额外开发库
启动/版本探查因Docker引擎管道不存在而失败，后续探查脚本未执行；保留
post-verification-db-start-failure.txt，数据库版本采用已通过真实新进程Database.check的证据，
不虚构额外探查成功。复跑须先恢复Docker Engine，再在C工作区dot-source本session脚本。

剩余未验收项：A生产provider/当前恢复权威/角色目录组装及固定DeepSeek真实选择、Task完成控制；
C本包组件边界已完成，完整MS-T2/真实项目交付仍按A整链门槛，不自动扩大范围。
