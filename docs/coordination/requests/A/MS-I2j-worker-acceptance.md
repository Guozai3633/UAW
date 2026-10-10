# MS-I2j 三组件审阅与合入

日期：2026-10-10。**按组件审阅合入，实际产品链仍待接线验收。**

| Session | 最终源码 | 独立交接 | integration 合并 | 已核对原回执 |
| --- | --- | --- | --- | --- |
| B / MS-U1 | d2ece8d1682a4ae1de2ed811fc24e304e3584569 | 1649a35a6ad5269e1c6390549fbbe6765b3dccf4 | 06ad3ac | 33 单元、11 受控 Chromium |
| C / MS-T2g | 5b7749d0e80f7576362dd5736e0d89ac779e01a5 | 780d3c47b62338ce90642f9cc47bb8f3bbe258c1 | 69b46de | 358 单元、219 不同真实 SQL |
| D / MS-R2g | d0ea31b7a05885806e9a72b9afff283ddc703122 | cc75c36df7f02ff08913aee47ea140cd09b3764e | fd0091b | 550 项、64 份 OS 清理记录 |

逐份检查 worker HEAD/工作区干净、相对固定开工基线的允许路径、源文件字节与最终 commit 相等。C 的 219 SQL 按原 XML 和索引最后回执去重，不宣称一次全通过。三次普通 merge 无冲突，保留原提交及交接，不操作 worker 分支或目录。

审查记录：[来源与原回执](../../../implementation/evidence/ms-i2j-worker-review.json)。原失败、修复和原生人工 pending 保留。组件通过不等于 P1、完整 Tool/Runner 或页面 accepted。

## 实际接线差异与处理

1. C 要求原 command.request_ref 为 tool_call 并固定 ValidatedCall 摘要；A 旧 RunnerCommands 使用 check/RunnerRequestRecord 摘要。A 在 b23dde9 增加独立 RunnerToolRequestRecord 和 register_tool_request，消费原 ToolLedger，保留旧 check 接口。
2. C 要求完整原 Tool ctx；工具预算存于独立账本，旧 Runner 要求 ctx 内预算引用。A 从原 dispatch intent/reserved/dispatched 读准确预算，不修改原 ctx；缺原发送账本拒绝。49 项实际 SQL/签名登记回归通过，新增两项在其中；初次两轮 fixture schema/可选字段错误保留。
3. RegisteredFileBridge 和显式 assemble_file_tool 已实现，5 项真实 SQL/签名/原快照与 C owning Reader 检查通过；传输及账号/root 来源为明确受控注入，不声称真人授权。66 项受影响组件与真实 Windows 双进程兼容检查通过。whole 原快照边界保留，分页不能靠重读补造。生产当前数据 Reader、设备/root 来源仍缺，不注册测试提供方。
4. B 仅消费 A1；A2 已公开列表、原请求查询和成果接口，默认页面的 RecoveryPort/ReviewPort 尚缺适配。真实浏览器联调 pending。
5. D 有真实原生取消/超时和持久授权组件；首次账号/设备/通道挑战来源以及本人实际点击仍 pending。

## 历史停止点与恢复

A 的 M2 已发布 ms-i2j-a2/e6db7f9，实际办公/学术 Web 后台链 6 次 DeepSeek 调用、2 个完成样例，费用 pending。随后上表三组件合入本地；其验证来源和合并历史随 ms-i2k-start 发布，不移动原标签。

原 RegisteredFileBridge 静态/类型检查因自动审批服务额度不足未执行；未绕过。服务恢复后重新经原审批入口执行并修复实际结构/类型错误，176 个核心及 Runner 文件类型检查通过。localhost TCP 后端已实际启动验证，原检查失败和停止点保留。

MS-I2j 尚未完整 accepted：B 默认列表/RecoveryPort/ReviewPort、生产首次配对/当前根和真人点击、文件完整 Agent/成果及最终全量仍待完成。MS-I2k 是已验证组件来源的开发派发，继续这些明确缺口；不要求缺口反过来成为所有 worker 开工前提。详见[新包](MS-I2k-parallel-packages.md)及[固定输入](MS-I2k-input-contracts.md)。
