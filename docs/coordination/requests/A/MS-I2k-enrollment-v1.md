# MS-I2k A1：首次账号/设备登记接口 v1

本阶段不完成真人配对或目录权限；发布实际状态服务、HTTP和D所需当前peer适配。共同开工标签仍 ms-i2k-start，兼容阶段单独发布 ms-i2k-a1。

## 1. 已实现 HTTP

所有端点沿 localhost精确Origin/HttpOnly cookie/CSRF，不接受账号、公钥、PID、code、proof、approved或路径声明。

| 方法/路径 | 请求 payload | 结果/约束 |
| --- | --- | --- |
| POST /v1/runner/enrollments | candidate_id | RunnerEnrollmentRecord，pending；原nonce/期限稳定，同request_id重放原结果 |
| GET /v1/runner/enrollments/{id} | 无 | 原完整Web会话、当前进程/key/native来源，不能跨登录复用 |
| POST /v1/runner/enrollments/{id}/confirmation | {} | 必填meta.expected_revision；独立native owning Reader及双方原签名通过才active |
| POST /v1/runner/enrollments/{id}/revocation | {} | 必填meta.expected_revision；当前原用户撤销，与complete同CAS锁 |

id仅放路径，写请求仍{meta,payload}。拒绝多余字段为request_invalid/422，缺CSRF403，缺实际来源503，版本冲突409；无新公开pair.complete v2。active首次登记不授予file.read/目录授权。

核心默认只注入实际BrowserSessions身份来源，**候选启动/本机确认来源仍为None**，真实begin保持503。不得注入受控测试源作为产品。上游注册实例和访问端点不是已完成的生产账号/OIDC。

## 2. D可以立即消费的固定签名

```python
from uaw.run.enrollment import (
    RunnerEnrollments, EnrollmentCandidateSourcePort, NativePairingEvidencePort,
)

class EnrollmentCandidateSourcePort(Protocol):
    async def current(self, candidate_id: str, *, owner: Principal) -> dict: ...
    # 严格RunnerEnrollmentCandidate；实际受保护launcher/当前OS/角色key观察

class NativePairingEvidencePort(Protocol):
    async def current(self, proof_document: dict, *, owner: Principal) -> dict: ...
    # 严格RunnerNativePairingEvidence；实际本机owning决定journal与当前key

RunnerEnrollments(records, controller, *, authenticate=BrowserSessions.principal,
    candidates=None, native=None, clock=None, capacity=32)
await service.begin(actual_web_owner, candidate_id, meta)
await service.complete(actual_web_owner, enrollment_id, meta)
await service.get(actual_web_owner, enrollment_id)
await service.revoke(actual_web_owner, enrollment_id, meta)
await service.challenge(actual_web_owner, enrollment_id)  # 内部原挑战，无native结果递归
```

原候选包含完整owner、control/device的实际OS实例、角色actor/key Ref/公钥和期限。created用FILETIME十进制字符串签名，转换OsIdentity时恢复int，不能截断/转浮点。key Ref.kind=content，id=key_id，hash=32公钥字节SHA256；两角色key和进程必须不同，SID/logon需相同本机登录。base64公钥为严格32字节；没有私钥/OS凭据handle/bearer/code保存到普通记录。

双方签署同一个RunnerEnrollmentProofDocument。control用原command签名域，device用pairing-proof；含完整原Web owner、候选pin、两OS/key快照、随机nonce、原期限。确认Reader必须返回实际本机决定Ref及同一个proof_document_hash，不得由HTTP approved合成。设备签名只能证明持有key，**本机本人确认来源必须另验**。proof/current接口不得再次调用service.get(active)，使用内部challenge避免递归。

登记最多5分钟且不超过Web/候选期限；同用户最多32个仍有效pending/active（可1..64配置）。当前源失效就拒绝；不无限续旧配对。密钥、nonce、当前身份、版本变化均不能改原记录修复。

## 3. 已确认配对后的当前接口

```python
from uaw.infrastructure.enrollment_peers import EnrolledPeerRegistry
peers = EnrolledPeerRegistry(service, owner=original_web_owner,
    enrollment_id=fixed_id, directory=actual_current_key_directory)
await peers.current(actual_OsIdentity, role='device')  # 原RegisteredPeer
await peers.owner(authenticated_principal=original_peer_actor,device_id=fixed_device_id)
```

直接实现D的PeerRegistrationPort与RunnerPrincipalMappingPort。默认WindowsApi.process核对实际PID/创建时间/SID/logon/存活；复查当前role目录、公钥/撤销、完整用户会话、原native来源和所有固定Ref。pairing_ref为完整**content**固定摘要，兼容D fixed_ref；pending不能作为这个已配对接口的输入。

`pyproject.toml`安装同时提供uaw和uaw_runner，不再依赖测试sys.path。锁/外部依赖不变；安装模块不授予功能。D消费阶段标签后自行uv sync --frozen --extra agent-engine，A未改其工作区。

## 4. 仍待M2的真正bootstrap

当前ReadOnlyHelper/BootstrapConsumer要求已配对peer，不能用它自己证明首次配对。A需要先构造受保护候选/双方角色key和真实OS观察，独立本机配对窗口与owning journal，再complete登记，最后装配ReadOnlyHelper和目录root确认。不能把pending塞入EnrolledPeerRegistry，也不能提供伪pairing_ref解除循环。

A负责候选launcher/current源和本机enrollment证据适配；D负责既有native/隐藏helper实现及当前root source。native初次窗口前的原挑战/一次code/proof必须通过受保护本机控制通道交付，不能公开到前端、argv或回执。最终数据流和来源尚未实连，本机真人点击仍pending。阶段API默认missing-source拒绝，不开放file_access/local_files/安装/写入exec。

## 5. worker阶段审阅

- B M1 fe68599/2c3ac0e：18path/21method的A2客户端、列表、HttpRecoveryPort和HttpReviewPort兼容，37单元回执已读。B继续默认页面/unknown/真实联调，阶段不冒称真实页面验收。
- C M1 5c8854c/815544c及M2 54d474e：FileMaterialReaderPort.export/read原ctx、不可变FileContent/Usage/Refs及每次当前owning Reader与A一致。A后续用material_ref+observation_ref接低信任Context，不能把文本复制Blob后绕过Reader撤销。
- D M1 97da1f3/41ab8da及M2 105dcbf：BootstrapConsumer/ReadOnlyHelper要求原当前RegisteredPeer/mapping/NativeChallenge交集；A当前EnrolledPeerRegistry形状兼容，但初次native来源和保护交付仍须上段M2实现。D继续helper生命周期，不把typed UI double当真人。

各worker继续原包，公共接口版本到达可按约定消费；不重写其提交，不等全包才审查。完整阶段/真人/生产门槛分开。
