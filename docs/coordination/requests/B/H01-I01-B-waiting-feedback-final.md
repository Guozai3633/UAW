# H01-I01-B-waiting-feedback 最终接线

2026-10-13。本项为原轮具体UI反馈修复，不是新大包、真实H01已部署或整轮accepted。

## 工作区、固定来源与提交

核对当前app checkout `C:/Users/郭丰硕/.codex/worktrees/2da6/UAW` 为干净detached HEAD `70f2fcccb88650c616920a5630d2caa45d94ad45`。原B `E:/UAW/.worktrees/context` / `dev/context` 干净，原HEAD `1b0fe02440d6f1929f42a797f30c51b39953d7c3` 与上次交接一致；已先报告关系，继续实际原B分支，没有修改app checkout或其他session。

fetch origin --tags后只读origin/integration最新DISPATCH的A30正式派发与固定请求；核对本地与ls-remote：

| 固定来源 | SHA |
| --- | --- |
| ms-i2l-a30-source | ad11ce70c50684ef304b4c137f7ea52eecb5f4ae |
| ms-i2l-a30-dispatch | 08352c774ed6a46930935e7218443e913d5dab46 |

只merge --ff-only准确source，开工HEAD完全相等；source内“待发布/待授权”为准备历史，依正式DISPATCH处理。没有合浮动integration、reset/rebase/stash或丢旧B提交/交接/回执。uv sync --frozen及原pnpm store冻结离线安装成功，锁未修改。

阶段源码 `170bac1086b5124653c593bef6f7542d0cd32540` / 阶段文档 `cc3076c4a84717f551832ce37623807d57dfe3f7`，4定向单元与类型通过后交付。A已审阅阶段范围和原消息/引用/读取指引无阻塞。最终源码 **db0a6981c1c925ad46283c765cef5a08d2c8cfcf**，准确提示已限定为同Run澄清/补充输入，不误称真实审批不能继续；本页及B handoff为随后独立docs提交，交接准确SHA见最终回报/git log。

A后续另报告8不同SQL节点、215源码类型与ms-i2l-a30回执；它是A独立来源，没有改变本修复固定source，也没有算作B测试。B没有同步该回执或操作A数据库/原H01环境。

## 页面行为与接口

1. waiting_for_user默认“任务等待处理”，实际RunStatus未变。真实ApprovalRequest仍用原卡“仅批准本次/拒绝”；完整RunDeliveryView仍用原合同接受校验。没有这些实际来源，不创造确认卡、成果或成功。
2. 原agent_message完整Markdown正文与原item版本保留，原resource_refs显示原kind/id/version/hash/location，不重写引用。空白正文明确“服务端未提供这条消息的正文，请重新读取原运行。”；缺消息/交付源没有猜测问题或成果。文本中的“批准/接受”等词不解释为权限或动作。
3. 新纯显示组件RequestGuidance({run,recovery,activeId,stopping})消费现有Run、原Recovery查找和当前会话标识，不调用API。解释为何原请求未结束/待对账时发送新请求不可用；textarea仍可编辑保存草稿，草稿字节、模型固定选择和原输入保持。
4. 当前没有同Run内steer/澄清恢复。仅指引本人自行停止、读到实际cancelled（已取消）后，将原问题和补充整理为新请求发送；不自动取消、合并猜测或提交，不称继续原Run。停止Acknowledgement与unknown不当cancelled。原Controller既有GET读到匹配Run终态后解除Recovery，本修复未改调度/控制协议。
5. cancelled后的说明明确新请求不会继续原运行；显示/刷新/reconnect本身均只GET。测试中新提交仅由模拟用户明确点击触发，body等于用户最后草稿原文，没有程序拼接。

Workspace/Controller/Review原公开签名不变；没有新route、schema/port/锁或flags。核对A8与A30的InteractionItem、RunRecord、ApprovalRequest、RunDeliveryView完整定义均一致；沿既有固定生成物，不更新公共契约或客户端endpoint。FrameRepository唯一理解Item由A负责，本UI只读原列表，不按正文文本合并/删Item或造另一份理解。

## 验证与准确计数

```powershell
uv sync --frozen
pnpm --dir apps/web install --frozen-lockfile --offline --store-dir apps/web/.store
pnpm --dir apps/web typecheck
pnpm --dir apps/web exec vitest run tests/unit/waiting-feedback.test.tsx
pnpm --dir apps/web test
pnpm --dir apps/web test:e2e # 内含tsc/build与受控Chromium
```

最终82单元（原78＋4新定向）和43受控Chromium（原36＋7新定向）各0失败/错误/跳过，原Markdown/Review/Recovery/权限/身份/当前生命周期回归保留。不累计阶段4或首次82/43复跑次数。最后文案修订后重新跑82/43；测试断言/原5秒或30秒时限未放宽。

定向覆盖缺信息waiting无审批交付、实际审批、完整实际交付、空文本、缺消息源、三个原Ref/版本/摘要、草稿持久恢复、手动stop仅Acknowledgement仍不能发送、实际cancelled GET才解除限制、手动新请求body原文不变、lost stop刷新先GET零自动取消/派发。原理解Item唯一的fixture/UI断言仅验证B消费，A后端去重SQL不是本测试的证明。

所有新增来源均为明确受控HTTP/projection与DTO，不是LLM、Runner、SQL或真人批准/接受。实际H01本人Run仍cancelled，B没有读取私有配置/key或操作其停止/提交/native/成果接受。

自身ignored `apps/web/.test-results/h01-i01-*`：baseline.log、uv-sync/install/typecheck.log、unit-stage.log/.xml、unit-final.log/.xml、browser-final.log/.xml、receipts.json、live-pending.json、受控waiting.png，以及前一组82/43回执。精确节点、原loghash与dist哈希在h01-i01-receipts.json；原U3/U3b所有失败/回执保留，未覆盖为本项通过。本定向修复无测试失败；辅助rg未发现AGENTS返回1不是测试失败。宿主Node22.13/锁定脚本runtime的engine warning和>500KB chunk警告保留，不报性能验收。

受控页面截图h01-i01-controlled-waiting.png已目视核对：问题/限制、3个引用、等待与发送说明、可编辑草稿、缺成果时没有接受按钮。截图不是H01真人页面/满意度回执。语义限定修改前后验证全部通过，不需以重复次数扩大覆盖。

## 最终三文件构建与A消费

准确源码 db0a6981c1c925ad46283c765cef5a08d2c8cfcf。A只读复制 `E:/UAW/.worktrees/context/apps/web/.test-results/h01-i01-dist/`，先校验三个文件；不执行或安装B环境：

| 文件 | bytes | SHA256 |
| --- | ---: | --- |
| index.html | 411 | 5489e365723a9b16e9aabbcfe29161b224e3f17635c8c555139a56352b73b9df |
| assets/index-B45RsHQP.js | 815220 | cc29c0d6f9e518fc1a4926279b5b304e7e9b79e756c48fc4f9523eddec5f1c57 |
| assets/index-CrD7HuLW.css | 17976 | 9338a965fbd284799b9337881ec1444ad0a61ad455ed9128567a56499b6bd7bb |

构建主JS815.22KB/gzip232.49KB，CSS17.97KB/gzip5.08KB，warning未隐藏。此构建只供A新固定版本审阅/部署；H01-v1仍为A29旧准确快照，不能把A30/B源码当已热部署，也不能覆盖其旧dist/回执。

A需将已复核原finished operation/Model owning Reader的补充agent_message、waiting事务和唯一FrameRepository理解Item与本B源码一起合入，再固定新体验入口。原3个来源Ref与text由A owning source给出；UI不补缺后端正文、不推断权限。A负责后台SQL/来源回归、真实新入口及原会话上下文的只读复验、最终新本人体验与汇合。不同来源回执分计，A不代改B业务源码。

## 真实未通过项与停止边界

真实认证只读联调pending：A尚未给本修复的新固定页面入口/原浏览器上下文，本项没有运行认证脚本或旧H01-v1本人页面。需要A明确提供新已部署版本、当前可见会话/原Page，仅GET/刷新并读实际原消息/引用/Run状态；不创建新会话接管旧实例，不代点旧任务停止/提交、审批/native/成果接受。该pending不因受控43项或A SQL回执而变成通过。

原本人Run保持cancelled、不复活、不重发，旧费用与模型两次成功来源由A保留。本包零真实Model/文件调用、零本人决定；无SQL实跑声明。缺源/空正文不当成功，真实用户满意仍待本人反馈。新同Run澄清/steer协议须另行固定输入版本/调用/取消/成本，不在本UI修复中自行设定。

没有扩Context或多Run、没有改公共schema/ports/contracts/锁/A-C-D源码/权限/flags/默认模型/D01/D03/D06。最终源码及独立handoff提交后clean停止，不自动扩包；A负责审阅合入、公共冲突、实际部署和完整回执。本项不标完整MS-I2l/H01/P1整轮accepted。

## 精确改动清单

- `apps/web/src/features/workspace/RequestGuidance.tsx`
- `apps/web/src/features/workspace/Workspace.tsx`
- `apps/web/src/styles.css`
- `apps/web/tests/e2e/controlled/waiting-feedback.spec.ts`
- `apps/web/tests/unit/waiting-feedback.test.tsx`

另含本B阶段说明、本页及handoffs/B.md追加记录；其他工作区未改。
