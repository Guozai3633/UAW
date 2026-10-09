# C / MS-T2f M1：实际办公纯参数工具

日期：2026-10-09。分支 dev/tool，worktree E:/UAW/.worktrees/tool。
基线 ms-i2i-start = d8023eb07e1460961782f297697da7428f6ad247。
M1 源码提交：63857e4d684ef3d9581778dc443126a5b84f3f03。

## 固定接口与参数

- `providers.arithmetic.arithmetic_spec(provider_ref: Ref) -> JsonObject`
- `calculate(args: JsonObject) -> JsonObject`
- `ArithmeticExecutor(source: ToolResponseStore, *, provider: Principal, currency="USD")`
- `ArithmeticVerifier(provider_ref: Ref)`
- `arithmetic_estimates(currency="USD") -> JsonObject`
- `providers.json_data.json_data_spec(provider_ref: Ref) -> JsonObject`
- `inspect_json(args: JsonObject) -> JsonObject`
- `JsonDataExecutor(source: ToolResponseStore, *, provider: Principal, currency="USD")`
- `JsonDataVerifier(provider_ref: Ref)` / `json_data_estimates(currency="USD")`

两种executor均沿用 `execute(call, spec, ctx)`、`check(call, spec)`；验证器沿用
`verify(data, call, spec, ctx)`。只实现确切 v1 Spec 和完整 ToolRef/hash/provider；
完整 Spec 包含闭合 input/output schema、read、tool.invoke、no-automatic-retry。
源码公共 helper 位于 tool/providers/local.py，不修改 shared。

arithmetic.calculate@1：参数仅 operation、operands。操作 add/subtract/multiply/divide/percent；
2..32 个 ASCII 普通 Decimal 字符串，每个最多64个数字、67字符，无空白/正号/指数/NaN/Inf；
减法左折叠，除法恰好2个数且分母非零，percent(base, rate) = base * rate / 100，恰好2个数。
独立 Context 精度34、ROUND_HALF_EVEN；每步拒绝溢出、下溢和非零结果 adjusted exponent
超出[-128,128]。输出 value 为无指数 Decimal 字符串，precision=34、rounding、rounded、inexact
记录实际上下文；不偷偷扩精度或把舍入说成精确。没有 eval/表达式/脚本。

例：`calculate({"operation":"divide","operands":["1","8"]})`
返回 `{"value":"0.125","precision":34,"rounding":"ROUND_HALF_EVEN","rounded":false,"inexact":false}`。

 data.inspect_json@1：参数仅 text、可选 required_keys。UTF-8原文1..16384字节；
最多16层容器、1024个节点（值和对象键分别计数）、每容器256项、键256字节；
required_keys最多64个唯一字符串，仅用于顶层对象。拒绝重复键（含转义同名）、非有限数、
超界数值token（128字符且非零数量级[-128,128]）、超深/超大和孤立代理字符，不修复原文。
输出 root_type/count/keys/missing_keys/nodes/depth/utf8_bytes/sha256。
keys按Unicode码点排序；missing_keys保持请求顺序；scalar count=1，空容器count=0；
depth仅计容器层数（标量0、根容器1）。仅结构检查，不声称专业数据准确性。

例：`inspect_json({"text":"{\"a\":1}","required_keys":["b"]})`：
root_type=object/count=1/keys=[a]/missing_keys=[b]/nodes=3/depth=1，hash来自实际原文字节。

## 接线样例和当前限制

```python
spec = arithmetic_spec(local_provider_ref)  # A登记的合法本地提供方，不是聊天API
# registry.register(spec, binding=可信AdapterBinding, expected_revision=当前revision)
executor = ArithmeticExecutor(source, provider=authenticated_local_service)
verifier = ArithmeticVerifier(local_provider_ref)
source.verifier = verifier
invocation = ToolInvocation(registry, ledger, budget, approvals,
    access=current_access, executor=executor, estimates=arithmetic_estimates(),
    prepare=executor.check, results=actual_results)
```

estimates均是固定本地免费tariff：tool_calls=1、wall_time_ms=1000、money=0.00/USD、其他维度0。
执行回执记录实际计时及原attempt_id，需ToolResponseStore实际blob/SQL和当前恢复来源。
参数或输出绑定冲突拒绝；纯函数参数失败ValueError，经原invoke映射invalid_arguments；
结果重算不一致tool_output_invalid；缺实际来源仍由原ports明确不可用。

允许变更：src/uaw/tool/providers三个新文件、tests/unit/tool/test_office_calculations.py、
本C requests/handoff。text.inspect不改；目录/角色/provider/组装/API/flags均由A登记和接线。
M2随后提供完整Ref有限路由；M3提供纯参数资源来源与原账本恢复；M4独立55434真实SQL。
本阶段不可宣称完整链路或Task完成，不注册受控测试能力为产品。

## 实际回执

- `pytest tests/unit/tool/test_office_calculations.py -q -p no:cacheprovider`：75 passed。
  ignored tests/.artifacts/C/MS-T2f/m1-unit-fixed.{txt,xml}。
- 初次 `m1-unit-initial`：73 passed、1失败、2环境错误；Decimal.traps测试不能clear，
  pytest自动参数ID超过Windows环境长度。修正测试上下文写法及短ID；原失败原样保留。
- ruff check/format和mypy providers：通过。
- SQL/新进程恢复尚待M3/M4实跑；受控依赖不能证明真实模型选择质量。

## M2 阶段源码与有限路由（继续M3/M4）

M2源码 SHA：5387624a69db68297bed78297bcb414463e25fe0。新增
providers/multiplex.py、parameter_sources.py、tests/unit/tool/test_office_routing.py。

```python
ToolExecutorBinding(tool_ref: Ref, provider_ref: Ref,
                    executor: ToolExecutorPort, prepare: Callable[[JsonObject, JsonObject], None])
ToolOutputVerifierBinding(tool_ref: Ref, provider_ref: Ref, verifier: ToolOutputVerifierPort)
ToolExecutorRouter(bindings: tuple[ToolExecutorBinding, ...])
ToolOutputVerifierRouter(bindings: tuple[ToolOutputVerifierBinding, ...])
PureParameterResourceReader(registry, access: ToolAccessPort | None, tool_refs: tuple[Ref, ...])
PureParameterRecoveryAccess(resources, ledger, *, authority: ToolRecoveryAccessPort | None = None)
```

最多128个路由，重复id/version（含不同hash）拒绝；构造期pins严格Ref合同，
缺hash、location/access_scope、错误kind拒绝。调用期严格Spec/hash/provider/input/arguments_hash，
真实adapter自身check再核实原版本/provider及有界计算。真实receipt仍须原attempt/usage.attempt_id。
路由不赋予权限、选择模型、不动态import；受信代码构造binding，不能从LLM响应生成。

```python
# 已由A显式注册确切三种Spec，并提供原 SQL/blob source 及当前独立数据权限。
ex = ArithmeticExecutor(source, provider=local_service)
bindings = (ToolExecutorBinding(arithmetic_ref, local_provider_ref, ex, ex.check),)
router = ToolExecutorRouter(bindings)
source.verifier = ToolOutputVerifierRouter((ToolOutputVerifierBinding(
    arithmetic_ref, local_provider_ref, ArithmeticVerifier(local_provider_ref)),))
resources = PureParameterResourceReader(registry, current_tool_access, (arithmetic_ref,))
source.access = PureParameterRecoveryAccess(resources, ledger, authority=current_data_authority)
# 原ToolApprovalAuthority(..., resources=resources, policies=实际ExecutionPolicyPort)
# 原ToolInvocation(..., executor=router, prepare=router.check,
#                    estimates=arithmetic_estimates(), results=实际ToolResults)
```

同一source限定一个provider；三工具可绑定同一合法本地provider，路由按完整工具Ref区分。
多个不同provider的路由也逐binding精确核对，但本包没有新增跨provider结果source复合路由；
A应按原attempt/provider选择对应source/facade，不把错误提供方交同一个source。
新恢复authority沿用已有ToolRecoveryAccessPort：必须从独立当前Run/owner/session/model/scope/
角色与provider来源复核数据可见性，允许取消后原尝试会计恢复不等于新执行授权。
C仅核实实际已登记的纯参数Spec、固定call/attempt和当前authority，不调用新执行snapshot。
A可适配既有Run数据来源；未注入返回dependency_unavailable，不使用ctx或历史批准自授权。
资源Reader仅三种实际精确Spec可返回空资源；没有通用空Reader。

M2累计新单元94通过；m2-unit-final.{txt,xml}。初次m2-unit和m2-unit-fixed保留：
受控单元receipt误写transport_state/缺currency以及构造错误类型已修正，未放宽公共合同。
当前stage仍待新工具实际SQL恢复验收；原124项SQL已在自身55434启动，本包继续。
