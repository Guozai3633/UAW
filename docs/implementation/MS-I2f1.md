# MS-I2f1：设备、请求与命令登记，以及当前权威组件

日期：2026-10-08。Session A，目录 `E:/UAW`，分支 `integration`；开发基线 `ms-i2e / ba2f3b0`。详细范围见 [MS-I2f1-scope](../coordination/requests/A/MS-I2f1-scope.md)。固定发布与实际代码提交由 [DISPATCH](../coordination/DISPATCH.md) 记录。

## 1. 功能与目录

| 目录 | 实际实现 | 可用范围 |
| --- | --- | --- |
| `src/uaw/run/runner_devices.py` | 平台 PostgreSQL 设备/独立通道归属、完整主体/session、CAS、撤销、到期封存及当前 owner 查询 | 独立 channel port 必须提供真实来源；生产默认没有 |
| `src/uaw/run/runner_commands.py` | 原请求与签字命令不可变登记、原尝试唯一身份、重复请求恢复、固定摘要读取、命令撤销 | 内部认证服务调用；不暴露 HTTP 或模型工具 |
| `src/uaw/run/runner_authority.py` | 从独立登记源重建既有 AsyncRunnerAuthoritySnapshot | root/gate/signer 缺失明确不可用 |
| `src/uaw/run/budget.py` | 一次 MVCC 查询读取真实 ledger/reservation/attempt 与 dispatch 意图 | 查询不授权发送；取消后的原尝试状态仍可读取 |
| `src/uaw/shared/configuration.py` | capability 检查尊重资源限定的 flag 范围 | 管理发布仍禁止开启未实现能力；没有开放 local_files |
| `src/uaw/composition.py` | Container 内部 services 和真实预算/政策/租约接线 | Workspace/Tool/通用 Context/Agent Runtime 仍未挂载 |
| `contracts/interface_catalog.py`、`src/uaw/shared/ports.py` | 13 个严格命名对象、独立 channel/root/action/signature 和 budget execution ports | 加法契约，原端口保留；无新 RefKind/依赖/迁移 |
| `tests/integration/test_runner_control.py` | PostgreSQL 及真实 Ed25519 边界验证 | channel/root/consent 明确受控，不能当作产品配对/本机授权 |

## 2. 状态与执行顺序

1. 内部控制服务身份全字段匹配，Devices 从独立 channel 来源取得 user owner、认证 Runner/session、配对/key/通道引用与期限。设备由平台记录持有；平台分区不是用户读取授权。
2. 同设备只能 CAS 更新；owner 不转移；同 channel Ref 不允许改正文；撤销/观测到期后必须有新的实际配对来源。到期即持久封存，时钟回退不会复活。
3. 原请求保存实际可信 ctx 和参数，版本1。登记 Ref 使用 `check` + 固定摘要；输入 body 不接受自报可信 ctx/owner。
4. 命令从原请求和当前设备构建，检查实际政策、Run、固定用户模型绑定、固定及当前配置、scope、真实预算 dispatch 意图、根和 lease/fence，再由独立 signer 生成签字。
5. signer 不得更改任何正文；真实 Ed25519 验证与当前 control key 状态由独立 signer port 检查。私钥/凭据不进入普通对象或 PostgreSQL。
6. 同原 principal/Run/operation/trace/attempt 只能登记一个命令身份，不能改 command_id 绕过。响应丢失复用实际原签字，重放仍检查当前准入。
7. Authority 将收到的命令仅作精确比对；从平台 command 索引定位原 ctx。两次当前来源收集、登记前后复核及最后 await 后期限检查；版本/撤销变化拒绝。
8. 命令撤销改变状态 revision，保留原签字正文与 `content` Ref。恢复 read 校验当前设备/完整 owner/session、固定原请求/摘要和当前签名 key，允许原 Run 已取消或过期；它只返回原命令元数据，不授予文件内容读取或重新执行。

`reserved` 不等于已允许外发。预算 dispatch 在账务域单独记录意图，仍不能证明外部已执行；未知费用不能据此释放。当前本包只支持 file.read/file.list 的准入核对，实际文件操作仍不可用。

## 3. 并发与失败语义

- 平台 Runner SQL aggregate 统一锁住本 owner 的设备、命令、请求和 attempt 唯一身份；CAS/幂等回执持久保存。
- 不在该锁内嵌套 Run/Budget/Lease 或外部来源调用，避免跨 owner 锁循环。登记前后复查与两次来源收集不能保证跨 owner 原子执行；实际发送/执行器还必须消费当前 fence、撤销与一次使用。
- 登记提交后复查失败可能留下不可准入记录；该记录只说明曾登记，不能据此宣称已发送/已执行。重试仍必须复核，不能换 attempt 推断未执行。
- 当前 owner 和 Runner actor 使用完整 Principal，包括认证 session。跨登录的设备重认证/归属迁移尚无产品协议，本包不会自动放宽 session。
- 登记签名、通道读取和准入来源收集有时间边界；取消向 await 传播，提交中断按持久记录恢复，不合成执行回执。恢复读取不能使用已过期的 command 期限作准入条件；未来恢复适配器另设调用时限。
- 缺真实 channel/root/current role-resource-consent/control signing backend，明确返回 unavailable。清理与原记录恢复不调用新执行 gate，也不新增 reserve/dispatch。

## 4. 实际验证

- 独立 `tests/integration/test_runner_control.py --require-postgres`：**47 passed，0 failure/error/skip，66.64s**。
- 覆盖真实预算意图、签字/实例重建/原响应恢复、服务身份、设备完整主体/session/当前来源、持久撤销/到期、CAS 并发、请求不可变、原 attempt 唯一命令并发、收到的 ctx/参数/fence/签字伪造、根/政策/固定模型/预算取消/flag/key/lease/command 撤销、关键 await 变化及签名后到期。
- 默认依赖缺失、file.list 精确工作区、资源限定 flag、管理发布禁用能力及 composition 未挂载执行也有实际断言。
- 首次独立检查：28 passed 后1个断言失败，测试错写 `dependency_unavailable`，现有统一错误码实际为 `capability_unavailable`。修正测试消费现有错误码；没有放宽实现权限或修改 worker 测试。
- 全量 `./ops/check.ps1 -WithPostgres`：**610 passed，0 failure/error/skip**；JUnit记录 887.28s。Ruff、142文件格式、98源码文件的 Mypy 通过。相比原563项新增47项独立SQL/签名检查，原563项也全部重跑。
- 契约与计划：1281 named schemas、272接口、26原已实现操作，50轮/115节点覆盖、26功能包依赖与目录归属检查通过；生成器不代替运行验收。
- 发布证据：[全量JUnit](evidence/p0-tests.xml) 与 [环境/源码摘要](evidence/environment.json)。独立回执在 ignored `.data/runner-control-final.xml`。

## 5. 当前接续

本子包按开发组件范围接受，完整 MS-I2f 继续开发。生产配对/认证通道、真实本机根、当前角色/资源/审批和 OS 密钥后端仍缺；没有可信 IPC、文件读取执行、安装/写入/exec 或 Agent 闭环验收。D01/D03/D06 及完整 MS-I2、P1 阶段门槛保留。

用户已确认 B/C/D 同时执行 MS-C4/MS-T2c/MS-R2c；各自固定 ms-i2e，不需要中途消费 A 新 ports。A 本包没有修改他们的原 worktree、提交或 handoff，没有向其聊天发送消息。接收其交付时由 A 逐包审阅、合入和复验。

D 包中的 Ref 类型笔误已更正：journal 用现有 `content` Ref，`runner_receipt` 仅为命名空间；见 [当前任务说明](../coordination/requests/A/MS-I2e-next-packages.md) §4 与 [范围勘误](../coordination/requests/A/MS-I2f1-scope.md) §5。
