# MS-I2k 开发基线准备

日期：2026-10-10。发布供四会话继续开发，**不是 MS-I2j 产品里程碑 accepted**。

## 实際变化

已正常合入 B/MS-U1、C/MS-T2g、D/MS-R2g 最终源码及独立 handoff，原允许目录、源码字节、XML、清理记录逐份核对。三次 merge 无冲突，未改 worker 分支/工作区。

A 保留原 ToolCall/ctx，把 Tool→Runner request 固定为原 tool_call hash，预算读原独立账本，不修改旧上下文；旧 check 入口兼容。新增 RegisteredFileBridge 和显式 assemble_file_tool，缺真实当前根/设备/数据 Reader/通道/签名来源拒绝。仅 whole 原签名快照，当前16384字符/64KiB边界；丢回应 recover 不发送新的 command，不重新打开变化的文件。

`ops/start.ps1 -Browser -EnableAgent` 新增显式 localhost 后台启动模式。仍须实际管理员已登记模型/办公提供方和 OS 凭据；只将公共配置模板复制到 ignored `.data`，无明文秘密写入文件。默认启动兼容，不开启文件/exec flags。

## 实际验证

- A 受影响 Runner SQL/签名登记49项，通过；新增两项包含其中，原 fixture schema/可选字段失败回执保留。
- 新桥接5项 SQL/实际密码学、临时内容快照/C持久Reader通过；传输、账号/权限来源受控，不计为生产配对/真人确认。
- C/D受影响边界与 A→D真实Windows双进程兼容66项，通过，测试身份明确受控。
- 合计120个不同最终通过节点，来自分组原XML，不是一次全量。Ruff通过，Mypy176核心/Runner源码通过。
- localhost 8000实际TCP后端/Agent装配 ready；真实Web会话、模型/会话列表读取、错误Origin403、退出及旧身份401通过；本次自建服务已关闭，不假装后台一直在线。

原M1 36、M2 23和两类6次真实DeepSeek调用各自保持来源；费用pending。旧ms-i2i全量1691仍独立保留，当前未重新全量。

## 正式派发与未完成门槛

[分包/阶段/任务/目录](../coordination/requests/A/MS-I2k-parallel-packages.md)、[固定输入协议](../coordination/requests/A/MS-I2k-input-contracts.md)、[四份转发提示词](../coordination/MS-I2k-messages.md)。准确开工SHA在DISPATCH，标签推送后远程核对。

仍待实际B页面/默认A2适配、首次账号设备配对源、本机真人目录授权、文件→Agent→成果整链、人工审批/拒绝/取消/接受及汇合全量。四包围绕这些缺口并行，不把夹具或组件数量换算成产品完成百分比。不开放子Agent/DAG/本机写入/安装exec。
