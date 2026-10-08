# 下一轮安排：交付边界与依赖

日期：2026-10-08。当前固定集成版本 **ms-i2f2**；准确代码SHA、原开工基线和接受见[DISPATCH](DISPATCH.md)。MS-C4/MS-T2c/MS-R2c已按组件接受，A已实跑SQL并完成登记命令Reader和缓存可选组装。

## 当前不重复派发旧包

B/C/D保留各自原worktree/分支，当前没有新代码包派发。三个包已经完成，其完整Runtime接线依赖实际来源，不能把这些缺口当作现有port已实现。A先补真实来源契约/适配器和动作关联，再按互不依赖的输入输出分包。

## 可发给B/C/D的同步说明

```text
你本轮组件已由A合入和接受：B/MS-C4 174单元＋35真实SQL，C/MS-T2c 135单元＋70真实SQL，D/MS-R2c 250组件/原公共检查。全量841项通过，无失败/错误/跳过。
继续在自己的原worktree和分支。工作区干净后git fetch origin --tags，再git merge --ff-only ms-i2f2；核对HEAD与ms-i2f2^{commit}一致，按uv.lock同步自己的环境。失败先报告，不reset/rebase或覆盖公共文件。
读docs/coordination/DISPATCH.md及requests/A/MS-I2f2-integration.md。D journal已由A统一为content固定Ref，Container.runner_receipt_commands提供登记命令恢复Reader；默认生产channel/signer仍缺。缓存可选注入，默认关闭；Tool Lookup/Reader/executor仍待接线。
保留原提交和handoff，不重做已接受包，不自动进入完整MS-T2/MS-R2或开放flags。当前未派下一包，等待A发布实际输入输出、允许目录和依赖。
```

A没有代为切换worker分支或向其他聊天发送消息；用户按需转发。同步标签是在已完成包的边界接收集成结果，不代表新包已经派发。

## A下一项依赖与后续分包原则

| 领域 | 下一步必须有的真实来源 | 交给worker前的要求 |
| --- | --- | --- |
| Context | 当前通用composition authority与具体材料Reader | 明确来源、完整主体、版本/hash、撤销和缺失语义 |
| Tool | 生产Lookup/Reader、原action-attempt与实际执行记录关联 | 不能从Runner ok推断applied；固定效果/费用证据与恢复边界 |
| Runner | 可信认证channel、用户配对、本机根/OS密钥及IPC | 先发布可信身份与撤销契约，D03未定不开放安装/写入/exec |

完整MS-I2f/MS-I2继续，P1闭环和D01/D03/D06门槛保留。详细包/目录/接口入口见[MS-I2f2设计](requests/A/MS-I2f2-integration.md)，实际证据见[实现记录](../implementation/MS-I2f2.md)。
