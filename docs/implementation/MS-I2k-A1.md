# MS-I2k A1：当前账号与设备登记

日期：2026-10-10。阶段接口发布，MS-I2j/MS-I2k均未标整轮接受。

## 实现与边界

新增 begin/get/confirmation/revocation 四个实际 HTTP，沿用精确 Origin、当前 Web cookie、CSRF和请求去重。客户端只提交候选 ID 或版本，不接受 approved、路径、PID、密钥或签名作为授权。

服务端保存原账号、两角色 OS 实例、当前公钥摘要、随机 nonce、原期限。确认前后复查来源，两角色独立签署同一个原文档；当前本人确认 Reader 缺失返回不可用。短 SQL CAS 管理确认/撤销，同账号容量上限和回执重放不会覆盖旧记录。已确认登记不授予目录或文件读取权限。

EnrolledPeerRegistry 对接 D 的当前注册/账号映射端口，实际 Windows API 复核 PID、创建时间、SID/logon及存活，随后再核对当前角色 key 和原登记。内部 challenge 读取避免 native 结果 Reader 递归，自身仍检查当前账号/候选/期限。Python安装同时提供 uaw_runner，不再靠测试修改导入路径。

完整输入、签名域和状态在[接口说明](../coordination/requests/A/MS-I2k-enrollment-v1.md)。默认生产 candidate/native 来源尚未组装，明确503；不开放任何文件、写入、安装、exec旗标。

## 证据

15个不同真实 PostgreSQL/Web/Ed25519 节点最终通过，按每个节点最后回执去重。包含实际 Windows 父子进程存活/退出和角色撤销；候选及本人确认 Reader 为受控来源，不能称真人配对已通过。15节点并非一次全量命令。

原导入失败、OS退出错误泄漏和测试错误码预期失败均保留。修复安装入口、明确失效OS身份拒绝、按实际422协议修正测试预期；未放宽权限或正向断言。严格 Ruff和178源码 Mypy通过。原始 XML、源码 SHA及失败历史见[阶段回执](evidence/ms-i2k-a1.json)。旧完整1691、准备120和旧真实模型6次调用保留各自来源，不算本阶段覆盖。

## 待完成

首次配对需要独立受保护启动与实际本人窗口，随后才能启用已配对 helper/root 流程。当前 D helper 要求已配对身份，不能把 pending 伪装 active 解除循环。B登录后真实页面、C资料进入 Context/成果、真人目录选择及当前完整回归继续由本轮完成；worker组件通过不替代这些门槛。
