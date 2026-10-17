# MS-U4 M1 精确0.2客户端与原Run读图

2026-10-17。实际E:/UAW/.worktrees/context / dev/context，原干净HEAD c13232bd8b8af813e448c14b8d39b8e4789662ba。git worktree list确认原B归属，未使用app绑定的detached checkout或新建替代目录。

fetch tags后只读origin/integration DISPATCH核对正式记录、local/ls-remote准确SHA；依次只快进ms-i2m-start / 1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe、ms-i2m-a6-source / b16c69a92d81124c00fb859ce8123748f56df054，两次HEAD分别相等。无自有新阶段需merge，旧提交完整保留；没有浮动integration/reset/rebase/stash。uv frozen/pnpm原锁离线成功。A6-wiring在source内不存在，已只读远端正式发布元数据补齐，没有为取文档合浮动源码。

M1源码 **1e3447853b4d068955728b43099beb07d74ffac9**。生成器锁A6 tag，30路径/33方法/204完整defs；原业务description、JSON Schema if/then与约束完整逐定义对照。公共schema、依赖/锁、后端、原Context不改。

client.runConversation/clarification/answer/correct/continuation精确五HTTP；GET带X-UAW-Schema-Version:0.2，新写meta严格ConversationRequestMeta(schema_version:0.2,request_id,expected_revision>=1)，正文payload不重复path ids。旧submit/control/approval等原meta仍0.1，不强转。conversationMeta(revision)一次生成ID，原文不trim/改写。

```ts
const port = new HttpConversationPort(client); // 默认同源内存Web身份/cookie/CSRF
const view = await port.read(actualRun, signal); // RunConversationView，问题只取这里
const scope = {runId:view.run.id, conversationId:view.run.conversation_id};
await port.question(scope, view.question!.question.item_id, signal);
const meta = conversationMeta(view.run.revision); // 本人提交一次创建，unknown只查询原id
const receipt = await port.submit(view, 'clarification_answer', exactUserText, meta, signal);
await port.lookup(scope, meta.request_id, signal);
// 运行中纠正kind='correction'；终态不能提交续跑，仍走原新turn。
```

ConversationPort.read/question/lookup/submit保持显式原scope。read复核Run id/conversation/current revision，question必须open+waiting且原run/input/question关联一致；不会猜最后消息或文本。submit先冻结原view/meta/text，重读view；回答另读原问题，Run/input/question CAS变化/终态拒绝，双击只一write。回执核对原run/conversation/request/kind/base input/question versions，accepted不改applied；applied需公开schema真实applied_at。每次等待后identity/Abort复查，不缓存权限或输出；port无后台进程，无自动写入。

M1类型通过，88单元通过（原82+新6），0失败/错误/跳过；旧0.1回归/严格生成器字段保留与新双击/身份/CAS/来源校验覆盖。自身ignored ms-u4-start-sync/a6-sync/uv-sync/install.log、m1-generate/typecheck/unit.log/.xml。测试DTO/transport为受控，无实际模型/SQL/生产clock证明。

M2将组件接原Workspace，问题/原因/候选与自由输入绑定原Run；受理/生效/替代分别显示。M3按identity+conversation+run保存用户草稿和pending request lookup/CAS，只GET原回执恢复，不自动换ID/停止/重发或接受。M1交SHA后继续本包，不等新小包。

A6明确没有新服务URL、D真实clock尚未安装，H01-v5保留；实际M4认证/长等待/固定模型仍pending，不能把旧服务404或受控通过当实际验收。真实入口到达只按A固定新版本和原Page消费，不替本人提交/授权/接受。
