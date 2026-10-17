# H02-I01 B：终态纠正反馈与窄屏成果修复交接

2026-10-17。请求固定提交 `fdc7b30c26defa4bebd5a0096de9e5f30c9de6ed`，只读读取其中 `requests/A/H02-I01-B-terminal-correction-feedback.md`。本次为原 MS-U4 本人反馈定向修复，不是下一包或 H02 整轮接受。

## 来源与提交

- 实际原目录 `E:/UAW/.worktrees/context` / `dev/context`；原干净 HEAD `f37265a5d4fc7f5545a0591ab91057e45b29d84c`。app绑定checkout为另一个detached目录，没有改动/创建替代worktree。
- 自行fetch tags、只读远端DISPATCH，核对 `ls-remote` 的 annotated tag解析及本地 `ms-i2m-a8-source^{commit}` 同为 **`fd50359ccd0c99f3416b5c0aeaf2375847f60dca`**。执行正常 `git merge --no-edit ms-i2m-a8-source`；A8已包含全部B旧提交，实际快进且HEAD等于准确A8。旧MS-U4/handoff祖先检查通过，无reset/rebase/stash/浮动integration。
- `uv sync --frozen` 和原pnpm冻结离线安装通过。公共API/schema/锁不变，生成器继续锁A6的相同公共契约，再生成无diff。
- **阶段及最终源码 `500d292937b511dbced4e674e3486b84213a2de6`**。定向回执到即在本聊天交阶段SHA后继续原完整回归；本页及handoffs/B.md为随后独立文档提交，准确handoff SHA见最终回报。

## 行为与接口

1. `ConversationPanel`按同原Run/conversation的实际Run来源选择最新revision，避免旧accepted回执里的queued覆盖较新的终态。patch仍accepted但当前Run终态时显示“已收到；本次未生效，任务已结束。”，分别明确失败/取消/完成，失败不会说本人主动取消；不写patch状态、不伪造applied。实际applied及applied_at仍如实显示，原input_ref/request/CAS历史不改。
2. 新增纯展示 `TaskUnderstanding({run,frame,draft,inputRevision?})`。ConversationPanel可选新增 `onInputRevision(inputRevision,runRevision)` 回调，只从已校验当前读图发布版本。Workspace绑定当前身份/conversation/Run并要求读图revision不旧于当前Run；失源或版本滞后时不认作当前版本。终态无当前summary不再持续等待，显示本次没有生成新的任务理解。旧输入summary保留原文并标“旧版本任务理解，仅供查阅”，版本未核对则明确标已保存未核对。本人新草稿保持原输入基准；不生成假理解。
3. <=1150px在聊天header显示“查看成果 · N”，打开单份原Review抽屉；1050/390px可查看真实来源返回的完整正文、Artifact版本、来源Refs和逐项核验。原布局将成果放在整屏聊天之后，缺少可见入口；现在抽屉可滚动、关闭/Escape恢复焦点，宽屏仍原侧栏，同一时刻只挂载一份Review。没有第二套正文或接受实现。
4. Review显示成果对应的proposal Run修订和当前Run修订；stale或修订不符明确提示此前版本仅供查阅，不能作为当前补充结果接受。原 `canAcceptDelivery`、读前重查、Ref/hash/合同/未知对账/取消守卫保持，终态/旧proposal/stale接受均禁止；不把Ref.version推测成input_revision，不把旧Artifact升级为新结果。

公开HTTP/DTO、HttpConversationPort.submit/read等签名不变；可选展示回调兼容旧调用方。不新增路由、授权、后台提交/重试/自动接受。原身份/原文/草稿、刷新GET、原request_id恢复保持，缺源不猜字段。

## 实际验证与失败保留

原工作区锁内node24.21.0、pnpm10.17.0；外层引导node22发engine提示，依赖脚本用本地node24。Vite原chunk>500kB提示保留。

| 命令/检查 | 真实回执 |
| --- | --- |
| `uv sync --frozen` | exit0；h02-i01-b-uv-sync.log |
| `pnpm --dir apps/web install --frozen-lockfile --offline --store-dir apps/web/.store` | exit0；h02-i01-b-install.log，无锁改动 |
| `pnpm --dir apps/web generate` + generated diff + 公共schema/锁diff | exit0，无diff；h02-i01-b-generate.log；30路径/204完整defs保留 |
| `pnpm --dir apps/web typecheck` | exit0；h02-i01-b-final-typecheck.log |
| 定向 conversation-panel/task-understanding/review 单元 | 24不同节点通过；h02-i01-b-target-unit.log/.xml |
| `pnpm --dir apps/web test --reporter=default --reporter=junit --outputFile.junit=.test-results/h02-i01-b-regression-unit.xml` | **107不同单元/21文件，0失败/错误/跳过**（原96＋新11） |
| `pnpm --dir apps/web test:e2e h02-terminal-feedback.spec.ts` | 构建/7定向受控节点通过；h02-i01-b-target-browser.log/.xml |
| `pnpm --dir apps/web test:e2e` | 构建/ **60不同受控Chromium，0失败/错误/跳过**（原53＋新7）；h02-i01-b-regression-browser.log/.xml |
| `git diff --check` / 原B HEAD祖先检查 | exit0 |

自身ignored `apps/web/.test-results/h02-i01-b-receipts.json`保存节点名、来源/SHA、日志/XML/hash；定向24/7不再加到107/60。新增11单元：三终态accepted、applied不降级、六理解版本/终态/草稿、旧成果只读；新增7浏览器：三终态、applied及旧理解、1050/390px成果、非终态但旧proposal拒绝。合成协议DTO不使用本人真实报告或源正文。

初次定向浏览器5通过/2失败：1050和390px正文/版本/旧接受禁用已通过，但关闭未将焦点还给入口。补显式onCloseAutoFocus后7/7及60/60通过；保留原断言与5000ms期望，不删除或放宽测试。原h02-i01-b-browser-initial.log/.xml、h02-i01-b-browser-initial目录trace/screenshot保留；此前所有MS-U4失败与handoff不覆盖。截图 h02-i01-b-1050-old-artifact.png /390-old-artifact.png已目视核对，仅受控数据。

## 准确构建、文件及A接线

A只读复制 **`E:/UAW/.worktrees/context/apps/web/.test-results/h02-i01-b-dist/`**，不执行B环境。源码500d292；与最后成功build的dist字节/hash一致：

| 文件 | bytes | SHA256 |
| --- | ---: | --- |
| index.html | 411 | 2bb4cfe3a59dca6c72d7fdd0d5e1b36875b9fbbc8a930525ba6bfff83e42b5a0 |
| assets/index-BqL45bof.css | 20480 | 40e08da4c5b490bdbab11b1bdd9b42d0accba7cc4a1cf803ff0f521557b87270 |
| assets/index-CfUSTHXz.js | 850761 | 51598b4bbfbb2e1f9a704f9a644ad011bff2154b42232e3cacc478b4eefd2643 |

相对固定A8仅以下10个apps/web文件，加本B最终交接及handoffs/B.md；不改共享、后端、锁、flags或其他worker：

```text
src/features/conversation/ConversationPanel.tsx
src/features/review/Review.tsx
src/features/workspace/TaskUnderstanding.tsx
src/features/workspace/Workspace.tsx
src/styles.css
tests/e2e/controlled/h02-terminal-feedback.spec.ts
tests/setup.ts
tests/unit/conversation-panel.test.tsx
tests/unit/review.test.tsx
tests/unit/task-understanding.test.tsx
```

A按原五HTTP/RunConversationView/TaskFrame/RunDeliveryView接线即可；没有新增接口缺口。A独立修输出容量、finish_reason=length/截断失败分类与真实report→correction链；B没有修改这些后端行为或本人Run/费用/原Artifact。

**真实复验pending A**：已知本人H02-v2服务5183存在，本修复未访问/登录/交换新launch，未切换服务或dist，也没操作本人提交/重试/确认/授权/成果接受。A合入并核对上述dist/hash后在原Page切换及复验；原失败/用量/旧Artifact保持，真实新版成果、用户满意、SQL/模型新调用均不作为B本次通过项。107/60只是工程门槛，不宣称MS-U4/H02整轮accepted。修复源码和handoff分开clean交付后停止，不自动扩包。
