# MS-R2c：终态 journal 的 Reader / 持久化接线与 Ref 缺口

日期：2026-10-08。固定基线 `ms-i2e` / `ba2f3b0d9417e6d695eaa74c2f766217c98b01f1`。
仅 D 组件；不修改 shared/schema/锁/composition/API。完整 MS-R2、可信 IPC、配对 V2、D01/D03/D06 继续等待。

## 已消费的内部接口

```python
@dataclass(frozen=True)
class RegisteredReceiptCommand:
    command: RunnerCommand
    device_id: str
    owner: Principal

class ReceiptCommandReaderPort(Protocol):
    async def resolve(
        self, command_ref: Ref, *, authenticated_principal: Principal
    ) -> RegisteredReceiptCommand: ...
```

定义在 D 的 `workspace/contracts.py` / `workspace/ports.py`，与 A 第4节批准的字段完全一致，无私有 wire DTO。
Reader 是独立登记源：必须先验证实际注册的不可变命令、固定版本和摘要、设备到用户的真实关系、认证通道及当前恢复数据权限。
不能从 publish 的 Ref、receipt 或入站命令拼出 owner/command。fixture 只是受控登记源；生产实现由 A 提供。

Journal 再验证完整登记 owner 与 command 的 principal 一致、设备与构造时协议 device 一致。
user 通道的完整 Principal（含 session/delegation）必须与登记 owner 一致；runner 通道必须由 Reader 独立验证实际归属，不能用 runner 字符串/命令自报主体作证。admin/service 未有本包授权。
命令的 Run 取消、历史期限、当前执行 flag/lease/fence 不触发新准入；恢复数据、设备或 key 撤销仍拒绝。Reader 不可用时无本地权限回退。

## 可选构造与调用例子

以下是内部接线示例；`trusted_registered_reader`、`current_keys` 和 `verified_channel` 都是 A 的真实适配器，不是本包提供的服务：

```python
protocol = RunnerProtocol(
    device_id=registered_device_id,
    bindings=root_bindings,
    admissions=admissions,
    signatures=Ed25519SignatureAdapter(current_keys),
)
journal = ReceiptJournal(
    private_development_directory / "terminal-receipts.sqlite",
    protocol=protocol,
    reader=trusted_registered_reader,
)
# 实际命令 Ref 来自登记源，完整 RunnerCommand wire 的固定 SHA256。
# received_utf8_json 是实际收到的已签名终态，绝不能由 admission 生成。
fixed_receipt_ref = await journal.publish(
    actual_command_ref,
    received_utf8_json,
    authenticated_principal=verified_channel.principal,
)
original_receipt = await journal.read(
    fixed_receipt_ref,
    authenticated_principal=verified_channel.principal,
)
assert original_receipt.attempt_id == original_attempt_id
# 完全相同、重新验证通过的内容返回原 Ref，revision 仍是 1。
assert await journal.publish(
    actual_command_ref, received_utf8_json,
    authenticated_principal=verified_channel.principal,
) == fixed_receipt_ref
```

缺 Reader 的默认分支：`ReceiptJournal(path, protocol=protocol)` 的 publish/read 都抛 `CapabilityUnavailable("runner.receipt_command_reader")`，不接触 SQLite。缺 signature verifier 也返回 unavailable。
可执行拒绝与冲突分支示例（需要实际收件，不新签 fixture 回执）：

```python
from uaw.shared.errors import CapabilityUnavailable, DomainError

try:
    await ReceiptJournal(private_path, protocol=protocol).publish(
        actual_command_ref, received_utf8_json,
        authenticated_principal=verified_channel.principal,
    )
except CapabilityUnavailable as exc:
    assert exc.status_code == 503  # 默认缺 Reader，不保存也不恢复。

try:
    await journal.publish(
        actual_command_ref, another_actual_signed_terminal_json,
        authenticated_principal=verified_channel.principal,
    )
except DomainError as exc:
    assert exc.failure.code == "revision_conflict"  # 同 command/attempt 不同已验证内容。
```

签名/越权/撤销拒绝；相同唯一身份的不同已签名内容 `revision_conflict` 409；找不到实际记录 `receipt_missing` 404；waiting 为 `runner.receipt_progress_journal` unavailable。
`ok/failed/cancelled` 不合成 Tool outcome；Usage 原样保留 pending 和所有未知维度，不补 money/tokens 的零。

## 固定 Ref 与最小公共缺口（由 A 决定）

**ms-i2e 的 `RefKind` 枚举没有 `runner_receipt` 或 `runner_command`。** 本组件返回现有合法容器：

```json
{"kind":"artifact","id":"runner_receipt-<实际唯一身份SHA256>","version":"1","content_hash":"<实际RunnerReceipt完整wire的SHA256>"}
```

这是 journal 中确实存在的记录引用，内部 namespace 为 runner_receipt；不是未发布的 kind，也未绕过 Ref/schema 校验。
ID 是 `[owner.kind, owner.id, device_id, command_id, attempt_id]` 的 canonical JSON SHA256；content_hash 是完整公开 receipt wire（**包括原 signature**）的 canonical JSON SHA256。
Canonical 为 UTF-8、sort_keys、separators=(",",":"), ensure_ascii=False、allow_nan=False，无 Unicode 归一化，不删除显式字段。JSON排版不改变内容；原始首次 JSON 文本仍存入 SQLite。
命令 Ref 的 content_hash 同样针对完整公开 RunnerCommand wire，包括签名；Reader 必须独立核对实际 version/id，Journal 额外核对完整内容 SHA256。
只接收 whole Ref：必需 content_hash，不接收 latest/current/*、location/access_scope；读取必须等于保存的完整实际 Ref。

**请 A 确认现有 artifact 封装是否用于生产接线。** 如要求字面 `kind="runner_receipt"`，最小公共变更是由 A 为 RefKind 发布该值及固定引用/摘要约定、同步 schema 副本/文档/示例，再派发 D 消费新版本。当前不生成非法 kind，不自动升级。
消费方影响：A 的登记 Reader 必须提供上述固定命令摘要；C 的 lookup/Reader 应按实际 Ref 查找来源，不从 kind/name 或 Ref 本身推出权限。ToolReconciliationReceipt 仍须另有明确效果/费用证据，不能把 RunnerReceipt 当作该对象直接读出。

## SQLite 归属、原子提交与中断语义

- journal 与 SQLite key 目录使用独立数据库文件，避免自身重入写锁；共享目录/ACL/凭据由 A 接线，不复制其他 session 数据。
- 显式传入独立私有/临时目录；构造无 DB IO，publish/read 的 SQLite、真实签名/当前 key 查询均在 `asyncio.to_thread`，无 asyncio.run 生产桥接。
- `BEGIN IMMEDIATE` 与 SQLite 唯一约束 `(owner_kind, owner_id, device_id, command_id, attempt_id)`；本地 revision 固定1。完整 owner 的 hash、固定 command Ref、原 receipt JSON、content hash 及必要身份索引存入组件表；不保存命令全文、私钥或凭据。
- 无历史 UPDATE/覆盖/删除方法。并发重复只保留首次实际文本、Ref 和 revision；不同内容/别名命令 Ref 冲突，不能因为 key 换代而覆盖旧终态。
- publish：Reader → 真实签名/绑定检查 → Reader重读比较 → 本地CAS内再次查当前key/签名 → Reader再次重读 → 最终签名/内容复核。read 从实际记录找到固定命令 Ref，Reader/签名/内容检查后再重读源并再次验签。
- 协作取消立即传播 CancelledError；后台 worker 在获得 SQLite 锁后、插入后以及最终验签后检查取消。未提交失败/中断回滚；SQLite busy/IO/数据库错误映射 `runner.receipt_journal` unavailable，没有内存或假回执回退。
- 进程被中止时遵循 SQLite 事务日志恢复；已提交但 caller 未收到结果会保留事实，重新 publish 去重恢复。测试实测受控插入后抛错回滚、新实例/新进程、实际 SQLite 锁下取消；**未宣称测试断电/磁盘损坏或强杀每个机器指令边界**。
- 提交后取消/Reader/key 撤销可能使请求返回失败，但已提交的原记录保留，后续仍按当前权限读取；不伪造 not_applied。线程不能撤销已经完成的真实 commit。
- SQLite CAS、Reader 及 key 目录不是跨服务共同事务；最后查询后的撤销竞争不能仅由此组件证明原子可见。A 需协调真实来源/撤销边界、私有目录 ACL、备份/保留和故障策略。SQLite 是开发组件 journal，不选择 D01、不是执行许可或完整 OS 隔离。

## 必需接线与仍缺能力

A 提供真实不可变登记命令 Reader、真实通道/device/owner 映射、当前 key 目录（device角色与撤销）、固定 Ref 约定与正式持久化策略。根 ExecutionLease 服务进入基线并不授予设备/文件/Tool权限，journal 不消费它来签发执行回执。
不挂载网络端点，不连接 IPC/配对 V2，不开放安装/文件写入/exec，也不启动 Runner 执行。测试中的真实 Ed25519 签名均属于明确受控的协议 fixture，不能宣称收到了实际 Runner 操作结果。
既有 verify_receipt 可比较 file.read 的 workspace version/path；file.list 公共 FilePage 没有 workspace/path 字段，本包不自造签字字段或从 snapshot_revision 推断绑定资源，保持现有校验边界。需要更强执行结果证明时由 A 发布版本。
