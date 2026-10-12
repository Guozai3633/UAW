# D A20 M1：同次双角色联合登记消费

实际worktree E:/UAW/.worktrees/runner、dev/runner。干净fetch后只读origin/integration DISPATCH正式A20派发，
远端标签ms-i2l-a20 /97681494e173534acc7ac36bf03c48eea233c449与source
ms-i2l-a20-source /46dd884f47fad35da19cd310be4e3aba0d45bc58 peeled SHA核对，
只快进固定source，HEAD精确一致，uv sync --frozen成功；保留c315352/9225919及所有旧记录。
阶段源码 **d32712e4f320b58fb3f313caad19db64f4974c72**。

## 接口与装配

D内部可选协议PairedPeerRegistrationPort（ipc/sessions.py）：

```python
async def current_pair(control: OsIdentity, device: OsIdentity) -> tuple[RegisteredPeer, RegisteredPeer]: ...
# 原构造不变，A20 actual EnrolledPeerRegistry已提供可选方法：
session = AuthenticatedPipeSession(
    pipe=actual_pipe, registration=actual_enrolled_registry,
    directory=actual_current_keys, signer=actual_local_os_signer,
)
await session.check()  # 同一个已握手连接，内部一次current_pair
```

消费者在_check使用该可选源。发现存在current_pair即必须callable并执行；严格type(tuple)、长度2、
各RegisteredPeer及内部OsIdentity/Principal/Ref/datetime类型，固定control/device顺序/真实原OS身份、
完整owner/actor/device/key/pairing/expiry与原握手完整字节逐项对照。nested模型在独立key await前detached。
纯schema/ID固定Ref/aware expiry检查与各返回的独立directory当前role/key/public digest/revoke仍执行。
pipe.live_sync在源等待前后复查，原channel/peer元数据和UTC/monotonic期限等待后再次检查。
有paired错误、非callable、异常、取消或超时关闭拒绝，绝不fallback再找两个current许可。
无paired方法原两个current检查兼容。handshake初次确定双方身份仍使用原单角色current，不能未经双方身份
确定先拼pair；完成handshake末尾check以及send/receive/full watch/effect checks自动消费pair。
check_local私钥/角色/OS/live检查和A15独立native/SQL失效监控、旧journal数据权限完全保留。
原外层send/receive/endpoint较早absolute reply deadline限制pair；A自身10秒上限不续期。

无需A新装配参数/公共DTO/schema/workspace ports/锁，现有A20 EnrolledPeerRegistry对象自动发现。
默认无源继续不可用，OS SID/PID/body不能生成UAW账号权限；flags/checked_metadata不变。

## 实际回执与下一项

m1-final.xml/log **28passed/2.43秒**：真实Ed25519/temp SQLite key directory、注册/OS/pipe为明确unit fixtures。
覆盖tuple/list/dict/单值/缺长度/swap/重复role、错identity/owner/actor/device/key/pair/expiry/类型/非callable、
源await后双方key撤销/live断连/早期限/元数据变化、异常/timeout/cancel均无fallback；旧current两次兼容。
初次sync fixture取loop失败28errors保留，改为async fixture后上述节点全通过，不改成功断言。
Ruff通过/Mypy36D源通过。原单次A测量SQL22→14不是D首次链证明，M1不借用该结果。

```powershell
$env:MYPYPATH='src;apps/local_runner'
.venv/Scripts/python -m mypy apps/local_runner/uaw_runner src/uaw/workspace
.venv/Scripts/python -m pytest tests/unit/runner/test_paired_registration.py -q
```

回执ignored tests/.artifacts/D/MS-I2l-A20。D提交M1后连续继续M2实际Windows/双方key/OS/owner/pipe/取消/期限与
同namespace owning/SQL测量，然后独立新Run原完整首次链成功断言及原journal恢复/清理；不重发unknown、不加时，
不重跑旧695或把组件当真人接受。本续项后停止。
