# MS-I2d：接受 B/D，并实施 A 的租约与输入路由

日期：2026-10-08。固定集成版本 `ms-i2d`，完整 MS-I2 继续 in_progress。

## 本轮代码

| 负责人 | 提交 / merge | 实际范围 |
| --- | --- | --- |
| D / MS-R2b | 5b97247 / 76fbb36；A merge 38492df | 异步准入、当前权威 wrapper、真实签名/本机复核、持久 guarded CAS；A实跑172项通过 |
| B / MS-C3 | 396b548 / 00332fc；A merge 0d6521d | 通用快照→ModelPrompt；107组件、15真实SQL全部通过 |
| A / MS-I2d | 见派发表代码提交 | 持久执行租约/fence、当前状态与清理接口、compose接线、模型输入命名空间路由 |

worker 的源提交与 handoff 均保留，没有修改原 worktree/分支。A 的平台兼容修复与组件提交独立，不改写 worker 原验证结论。

## 修复与发现

- B 首次SQL：15项在准备阶段失败。SQL fixture的Reader对 Ref 做完整对象相等比较，未附摘要的固定引用被判为变化；改用公共 matches_pin，仍检查kind/id/version/location和已提供的hash，SourceResolver继续验证真实内容摘要/访问。
- 重跑14项通过，跨进程用例失败：Windows PostgreSQL Selector loop不支持 asyncio subprocess。改在线程中调用有45秒超时的 subprocess.run；独立子进程仍从真实SQL重建解析器，URL只经stdin传递，不进入argv/回执。单项复验通过。
- A 路由新用例误用了字段 input_snapshot_ref，修正为当前契约 context_snapshot_ref；原生产逻辑未为测试更改。
- 首次完成全量505项通过、1项失败：原组合测试访问旧解析器的understanding属性。路由新增后改为核验legacy分支仍共享同一Intent上下文，通用Context/Tool/Workspace未启用的断言保留，未弱化业务门槛。
- 审查租约发现调用超时与根租约超时应分别处理，补充专门反例；调用过期不改变另一有效租约，真实过期/取消则提交不可复活终态。该修复前中止的全量检查不作通过证据。

## A 的实际功能

ExecutionLeaseService 使用实际 PostgreSQL/现有事务、同Run控制锁、严格CAS、完整holder/session和拥有者scope检查；续约/释放/接管、持久终态、响应丢失重试及当前状态查询均有实现。新接管递增fence，旧回执不能恢复执行许可。仅根lease，node明确不可用。

ContextModelInputs按单次SQL中的实际命名空间选择真实解析器，冲突拒绝、无错误fallback，理解/诊断保留原实现。compose的通用分支因缺真实Composer/authority仍明确不可用。

输入输出、期限、错误与接线条件见 [MS-I2d ports](../coordination/requests/A/MS-I2d-ports.md)。没有新增依赖、迁移、HTTP/模型可调用入口，已实现操作数仍26；公共命名schema增加至1268。

## 验证

- D：A实跑172 passed，含70个新增异步用例；不能将172计作新增。
- B：107个单位用例及15项真实SQL全部通过。
- A：租约15个真实SQL检查及输入路由3个SQL检查全部通过。
- 最终全量 **506 passed，0 failure/error/skip**，耗时585.67秒，见 [JUnit](evidence/p0-tests.xml)、[环境与源码摘要](evidence/environment.json) 和契约检查的发布回执。

验证命令：`./ops/check.ps1 -WithPostgres`，然后 capture_environment.py、contracts/check_interfaces.py、planning/build_plan.py。静态/格式检查132文件、Mypy94源码文件。

## 状态与后续

B/D组件由A接受后暂无新包。C继续MS-T2b/ms-i2c，不要求开发中混入新公共文件。A继续完整MS-I2：设备/通道关系、已登记请求与真实Runner权威接线；不能从command创建自身授权。

Tool/Workspace/通用Context Runtime未完整绑定，真实Provider、可信IPC、Runner私钥OS库实连、实际配对、文件执行与Agent闭环未验收。执行租约仅协调workers，本轮没有真实命令发送或执行，也不声称跨域原子权限。D01/D03/D06和原阶段门槛保留。
