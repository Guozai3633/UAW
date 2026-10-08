# MS-I2f2：组件接受与恢复 Reader 接线范围

日期：2026-10-08。负责人 A，目录 `E:/UAW`，分支 `integration`。本包依赖 MS-I2f1、MS-C4、MS-T2c、MS-R2c；完整 MS-I2f 的产品来源接线仍按原门槛推进。实际结果见 [实现记录](../../../implementation/MS-I2f2.md)。

## 1. 包定义、目录和接受范围

| 功能包 | 代码目录 | 本次接受的最小能力 | 后续依赖 |
| --- | --- | --- | --- |
| B / MS-C4 | `src/uaw/context/cache.py`、`selection.py`、`model_input.py` | 有界纯计算缓存；当前权限、来源、规则、窗口和最终复查仍逐次执行 | 通用 Composer 的真实 authority 与能力 Reader |
| C / MS-T2c | `src/uaw/tool/facade.py`、`ports.py`、`reconciliation.py` | 原尝试 Lookup、统一 reconcile、重新核对来源的 read_outcome | 生产 Lookup/Reader、动作与执行器的实际登记关联 |
| D / MS-R2c | `apps/local_runner/uaw_runner/receipts.py`、`workspace/contracts.py`、`ports.py` | 签名终态 journal，去重/冲突、当前源与密钥复核、进程重启/并发 | 可信 IPC、真实用户配对、OS 密钥和实际执行 |
| A / MS-I2f2 | `src/uaw/run/runner_receipts.py`、`composition.py` | PostgreSQL 原命令到 journal Reader；默认关闭的缓存可选注入 | 登记服务的真实 channel/control signer；不替代执行 authority |

包定义源是 `planning/parallel_catalog.py` 的 PACKAGES；session 页定义可写路径。本包的组件接受不将 P1-02/03/04、P4-04 或完整 MS-T2/MS-R2 标为 accepted。

## 2. Reader 契约与来源

内部方法：

```python
RegisteredReceiptCommandReader(commands: RunnerCommands | None)
await reader.resolve(command_ref: Ref, *, authenticated_principal: Principal)
# -> RegisteredReceiptCommand(command: RunnerCommand, device_id: str, owner: Principal)
```

`command_ref` 必须匹配平台登记的固定 `content` Ref（版本、摘要、命令 ID）；`authenticated_principal` 来自可信适配器，不读取模型或 receipt 中自报的身份。

顺序为：实际 `commands.read` → 独立 `devices.owner` → 再读 command → 再读 owner → 检查一致性 → 严格复制 RunnerCommand。原命令、原请求、当前完整主体/session、设备归属、当前控制签名和固定摘要由登记服务核对。返回的 owner 来自设备源，再与命令 ctx 比对，不能从命令声明生成 owner。

单次读取限时 30 秒；恢复不借用已过期的旧 command deadline。缺命令源返回 `capability_unavailable`；固定引用、当前设备/密钥/主体变化按登记服务错误拒绝，前后来源不一致返回 `runner_receipt_source_changed`。取消和超时传播，journal 不伪造回执。该方法只读原登记元数据，不授予文件读取或重新执行权限，也不 reserve/dispatch。

组装根提供 `Container.runner_receipt_commands`。journal 显式注入该 Reader 和真实签名协议；组装根不创建 journal 文件或自动注册为公共工具。默认登记服务仍缺真实 channel/signer，因此产品调用继续明确不可用。

## 3. 缓存接线与关闭

```python
cache = PureComputationCache(max_entries=128, max_bytes=2097152)
container = compose(settings, context_cache=cache)
```

同一实例注入理解 Context 的 selection 和通用模型输入 formatter；默认 `context_cache=None`，任一容量为 0 时缓存不保存条目。缓存只复用当前检查之后的计算结果；不缓存权限、旧 Reading 或模型答案。键包含主体/Run、固定模型/权限及完整实际输入、元数据与算法版本，摘要缺失则绕过。容量按条目和字节有界；字节容量计入结果和摘要键，Python 容器额外开销由条目数限制，这不是整个进程的内存上限。异常重算，不把旧值作为授权回退。

本次没有增加用户配置或新的 capability flag。通用 Context/Tool/Workspace/Agent Runtime 仍未绑定。这里的收益是本地重复格式化/估算次数减少，没有验证提供方 prompt cache、真实 Token 或端到端延迟收益。

## 4. 回执 Ref 类型裁决

D 原交付使用合法 `artifact` 容器，原提交及 handoff 保留。A 在集成分支将 journal 固定输出统一为既有 `content`；`runner_receipt` 只作为 ID 命名空间，签名回执不是用户成果登记。更新实际单元和跨模块断言，无 RefKind/schema 变更。

这是产品开放前的接口修正，不提供 `artifact` 到 `content` 的透明别名。原测试 journal 不是已部署用户数据；若后续需要导入旧试验数据库，应显式重新验证并迁移固定引用，不能把两种 Ref 当成同一个 pin。

## 5. 退出条件

- A 实跑 B 的 35 个 PostgreSQL 用例和 C 的 70 个 PostgreSQL 用例，包含原回归；D 的真实 Ed25519/SQLite/进程检查保留。
- A 新增真实 SQL 登记 → Reader → 签名 journal 的恢复测试，覆盖固定 Ref、重启/去重、取消/过期后的原数据、当前设备/密钥/主体拒绝和默认组装边界。
- 全量检查无失败/错误/跳过；记录实际源码摘要和固定新标签，旧标签和 worker 分支不改写。
- 不把 Runner ok 推导为 Tool applied，不把 failed/cancelled 推导为 not_applied 或零费用。本轮没有实际文件动作、IPC、配对或 Agent 任务执行。

下一项依赖先由 A 补真实来源契约和可消费适配器，B/C/D 保留交付边界；新的开发包在发布明确输入输出后派发。
