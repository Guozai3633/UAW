# MS-I2j 开工包准备记录

日期：2026-10-10。范围：开发安排和目录归属；不计入 Runtime实现或产品验收。

## 本轮分工

| 会话 | 工作包 | 结果 |
| --- | --- | --- |
| A | MS-I2j | 本机浏览器会话、实际用户API/单Agent后台执行、文件桥接和逐包集成 |
| B | MS-U1 | apps/web真实前端、协议客户端、事件恢复和成果/审批/取消页面 |
| C | MS-T2g | file.read工具执行/核验、文件观察及原结果恢复 |
| D | MS-R2g | Windows本机确认、目录选择、只读根授权及撤销生命周期 |

共同固定标签 `ms-i2j-start`，精确开工SHA通过标签commit核对。准备前integration为 `00e59becd78118911b49e607809f14e0e2721b71`，本次安排保持运行代码、契约、测试、ops和Python锁与 `30566c62f7440b363d188910cdc14a8d69b940be` 一致。

## 状态与依据

B/MS-C7、C/MS-T2f、D/MS-R2f已按组件和A实际消费者接受，旧完整MS-I2i回归仍在运行。准备时有1256项完成原JUnit通过回执，另435项未收尾；有一组原失败因测试未预建回执目录，A已补准备目录，复跑结果未发生前不能写通过。

本轮安排明确：A先完成原来源回归再修改自己的运行代码；B/C/D在独立worktree开发。新增apps/web归B，根Python锁/后端/契约归A。三个worker分支只读核对干净，均为准备前integration的祖先，可自行快进；没有修改其工作区或发送聊天消息。

## 已完成的准备

- [四份可转发提示词](../coordination/MS-I2j-messages.md)。
- [详细范围、接口责任、目录、四里程碑和验收](../coordination/requests/A/MS-I2j-parallel-packages.md)。
- planning/parallel_catalog.py为维护源，生成当前机器计划、各session页和并行总入口；本次43包、5份session模板（E仍可选未派发），目录互斥和依赖无环检查通过。
- DISPATCH、NEXT_WAVE、文档总索引和目录说明同步。旧派发和原验收回执保留，未把MS-I2i记为完整通过。
- [实际准备检查](evidence/ms-i2j-preparation.json)：文档链接、生成计划、运行来源未变和worker ancestry检查；不是代码行为测试。

## 发布与下一步

提交准备文件、创建新固定开工标签，atomic推送integration与该标签，并用远程refs核对。旧标签不移动；用户分别转发提示词后各会话自行开工。准确commit以Git标签和远程实际refs为准。

API入口不能只靠删掉当前Origin拒绝来开放浏览器。A需要实现本机会话/Origin/CSRF与用户管理员分离；C实际文件调用不自授根权限；D真人确认尚未发生时保持明确pending。当前默认全局flags及写入/安装/exec保持原状态。
