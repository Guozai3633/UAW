# MS-I2k A2：原审批恢复、资料来源与组件集成

日期：2026-10-10。阶段接受，不是本轮全量或产品整轮完成。

## 实际实现

- 原待审批 Agent step 只读取原 approval/context/action，pending 不改变 Run 版本；实际批准经原 grant/当前政策复查后恢复同一个 step。拒绝仅恢复推理以记录 denied，Tool独立审批/预算/取消仍决定是否发送。未知效果不构造新尝试。批准与拒绝实际队列均交付成功，受控模型仅证明协议。
- FileToolBindings 暴露 C 的原资料 Adapter。FileContextMaterials 只保存现有 TrustedExecutionContext/Ref，当前正文每次回 C owning Reader；片段、完整文件、资料信封三个hash不混用。重启后读取、原文件删除后原快照、跨会话/撤销拒绝有实际SQL/签名回执。FileAwareContextInputs 保留原Context授权与封存recipe，混合批次不把文件Ref当普通Blob，正文始终external/material。
- 独立 WindowsEnrollmentConfirmation 在原设备OS实例复核账号/当前角色key/原控制证明后打开现有Windows默认取消窗口，再签同一登记文档并发布严格native journal；Reader只读原journal并复核原challenge，不递归，也不重开窗口。该producer未绑定默认服务，窗口的正向本人流程未验；本阶段只验错误OS在窗口前拒绝、受控journal的持久当前来源。账号绑定不授予目录。
- B/MS-U2、C/MS-T2h、D/MS-R2h最终源码和独立交接逐包合入，未改worker分支；目录、源码字节、原XML和清理回执独立核对。[逐包范围](../coordination/requests/A/MS-I2k-current-integration.md)。

## 验证范围

63个不同节点最终通过：54个合并后A原Windows管道/新D bootstrap-helper/C资料单元边界，4个实际SQL后台队列，1个原文件资料SQL链，2个混合批次单元，2个native来源SQL/OS拒绝节点。后台4项采用03原3通过加04拒绝复跑；不累加重试。185源码Mypy和Ruff通过。

实际localhost TCP 后台启动、登录、精确Origin、读取、退出失效及native缺源503/伪approved422通过，自有probe服务器已关闭。这不是浏览器页面或真人确认回执。

初次后台测试 RegistryEntry.spec 方法和必需reason遗漏、declined结果误期待failed，全部保留；按实际合同修正，不放宽权威、安全或正向效果断言。类型/导入检查原失败保留。原始XML、来源、准确执行时期差异与停止点见[阶段证据](evidence/ms-i2k-a2.json)。

## 继续工作

默认生产首次launcher/current候选及保护交付尚未组装，native missing-source仍不可用；真正D用户目录与原Ticket/current channel链继续。文件资料已能进入Context来源，但真实文件→固定Model→成果/当前撤销整链未验。实际B登录后页面、DeepSeek场景、真人确认与四组件汇合后一次全量继续；旧1691、准备120、A1的15及旧6模型调用均保留来源，不算本阶段重新执行。

自动审批拒绝A前端开发依赖安装，原因是“安装保持关闭”，已经明确向用户申请开发环境例外，未安装/未旁路/未改B环境。若使用B已交付构建物联调，将单独记录实际页面来源与范围。未开放子Agent/DAG/写入安装exec或默认文件flags。
