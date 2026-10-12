# A21 D M1：联合 native 根观察阶段接口

实际目录 E:/UAW/.worktrees/runner，分支 dev/runner。
固定源码 ms-i2l-a21-source / 88e7078cc0b7aee66136ebd44ec0d057e184b209；
远端 tag 与 origin/integration DISPATCH 精确一致，干净快进并 uv sync --frozen（64包）。
M1源码 **3a2e145a08043686837ac7d2e43d2317e5ec53f2**。保留 A20及全部历史失败/清理证据。

## 构造及消费

原 NativeRootSource 构造不变，新增可选内部能力：

```python
async def checked_current(
    self, device_id: str, workspace_ref: Ref, ctx: TrustedExecutionContext,
    *, check: Callable[[JsonObject], Awaitable[None]],
) -> JsonObject: ...
```

复用原 current 私有核心：原独立 owner → 原完整 _read → 脱离引用的完整 root
→ await 恰好一次 metadata callback → 原独立 owner → 原完整 _read → 完整比较/新时钟 → 后观察。
旧 current 不调用 callback，原验证不删减。_read 的 consumed SQLite ticket/grant、
当前 device-role Ed25519 proof/selection signature、OS目录身份、scope、最终重新读取均保留。
不读取文件内容，不确认用户，不执行、不登记或dispatch；callback不提供执行许可。

callback非callable/非None返回拒绝503，输入或原请求腐坏拒绝409；根/owner/key撤销、
完整root变化或较早期限拒绝。异常、TimeoutError、CancelledError原样传播，没有fallback。
原调用方10秒reply及更早context/root/lease deadline不延长，无allowed缓存或公共契约变更。
A现有两Gate/check_root及Runner控制器可直接发现此方法；不需要改装配或新参数。

## 真实验证与限制

D独立临时目录内真实SQLite consumed-grant、Ed25519和实际目录；owner/native确认为明确测试fixture，
不是本人确认，也不是生产账号来源。定向85通过32.55秒（33新＋52原native root）；最终源码
33新边界复验通过8.08秒。Ruff/格式及36 D/workspace源码Mypy通过。

命令：`.venv/Scripts/python -m pytest tests/integration/runner/test_checked_native_root.py
 tests/integration/runner/test_native_root_source.py -q --basetemp=tests/.artifacts/D/MS-I2l-A21/native-final-temp
 --junitxml=tests/.artifacts/D/MS-I2l-A21/native-final.xml`。
回执 ignored tests/.artifacts/D/MS-I2l-A21，native-final.xml、m1-final.xml、m1-mypy-final.log。
初轮83通过/2测试准备失败：冻结DTO直接赋值触发Pydantic异常，改为明确对抗性内存腐坏；原日志保留。
初轮格式及类型校验失败也保留；没有删检查、延时、跳过或改公开源码。

继续同包 M2：实际installed SQL/OS来源两Gate联合/legacy测量、拒绝和原journal回归；
M3：原首次链完整成功断言仅跑一次，失败透明记录并清理，再独立handoff停止。
flags/checked_metadata/子Agent/DAG/写入安装exec保持关闭。本人确认pending。
