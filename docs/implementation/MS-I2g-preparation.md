# MS-I2g：完整功能包与独立验证环境准备

日期：2026-10-08。准备标签 `ms-i2g-start`，具体 SHA 见 [DISPATCH](../coordination/DISPATCH.md)。最近已验收运行版本仍为 ms-i2f2；MS-I2g 的完整集成未完成，新 worker 包尚未收到开工回执。

## 实际修改

- `ops/start-dev-db.ps1 -Session A|B|C|D`：分配独立 Docker project、loopback 端口 55432/55433/55434/55435 和数据卷；默认 A 保留原 project/端口。秘密仅生成在调用 worktree 的 ignored `.data/dev-db.env`，不用 A 私有配置。
- `ops/compose.yaml`：loopback 端口可由脚本明确设置，默认保持 55432。未修改数据库镜像、持久化 schema、业务迁移或权限。
- 发布 B/MS-C5、C/MS-T2d、D/MS-R2d 与 A/MS-I2g 的完整功能包，各四个里程碑、两个交付点；明确接口/目录/策略和独立 SQL。阶段版后继续同包，最终逐包接受。
- 更新分工源、生成计划、可转发说明和实际产品进度。用户已报告三位 worker 干净同步 ms-i2f2，不把这个旧同步当成新包已开工。

## 实际验证与证据边界

- A默认入口启动兼容，通过8项真实 PostgreSQL 持久化用例，0失败/错误/跳过；[独立回执](evidence/ms-i2g-db-tests.xml)。
- A/B/C/D渲染后的 Docker project、loopback端口和命名数据卷分别核对。B/C/D数据库没有由A启动或迁移，worker接收新版本后自行在自己的worktree启动；配置检查不冒充运行回执。
- 运行源码、测试、公共schema/ports/contracts、依赖锁、提示词相对ms-i2f2不变；只有两个开发环境文件及文档/计划改变。原841项完整回执保留，本次没有重新运行841项。当前源码摘要的两个环境文件由本次补充检查支持，其余源字节与原回执一致。
- 计划生成器检查31包、目录无重叠和依赖无环；正式50轮状态未扩充接受。新功能包是ready_to_start，不是accepted。
- [准备范围/环境检查记录](evidence/ms-i2g-preparation.json)、[原运行源码/补充检查关系](evidence/environment.json) 和 [完整包接口](../coordination/requests/A/MS-I2g-parallel-packages.md)。

本轮没有修改worker worktree、分支、提交或原handoff，没有向其他聊天发送消息，没有开放产品flags或执行能力。固定标签发布后由用户转发各包说明。
