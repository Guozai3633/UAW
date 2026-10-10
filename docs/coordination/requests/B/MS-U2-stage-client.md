# B/MS-U2 M1 固定客户端与端口（2026-10-10）

worktree E:/UAW/.worktrees/context，dev/context。正式DISPATCH准确基线/ms-i2k-start
b7b79b150470a80f37b28fd52a2177f6de5b3124；clean/fetch/ff-only/HEAD==tag/uv sync --frozen
成功，全部MS-U1提交/handoff保留；无reset/rebase/stash。M1源码
**fe68599a46bdb7df8d896a073776c6f64cd5c081**，此说明独立提交，立即继续M2–M4。

生成器固定git show正式标签的schema/OpenAPI，18个实际path/21个方法/169定义，新增
conversations.list、turns.lookup、runs.delivery、artifacts.get/content、delivery.accept；
源hash/准确commit在generated/source.json。公共契约/后端/根锁/flags无修改。

UawClient新增公开方法：

```ts
conversations(cursor?, signal?):Promise<ConversationPage>
lookup(conversationId, requestId, signal?):Promise<RunRecord>
delivery(runId, signal?):Promise<RunDeliveryView>
artifact(id, version?, signal?):Promise<ArtifactRecord>
content(id, version, content_hash, signal?):Promise<ArtifactContentView>
acceptDelivery(runId, {bundle_ref,artifact_ref,decision}, meta, signal?):Promise<CompletionAcceptance>
```

POST准确{meta,payload}，run_id仅在path，固定Refs不要求expected_revision或If-Match。
Runtime保留完整schema条件，不能把2xx/queued当完成。HttpRecoveryPort.find只查原IDs，
missing→undefined，其他错误不变匿名或执行重试；结果Run归属必须匹配。
HttpReviewPort.read(artifactRef|undefined,runId,signal)读取真实RunDeliveryView，保留
整份artifact/content/contract/report/proposal及对应固定Refs、stale/requires_acceptance/
实际acceptance。映射到兼容ReviewSnapshot并附delivery，校验正文UTF-8长度/hash和
目标/合同/提案关联；旧hash/错Run/错关联拒绝。accept只有真实view、不stale、无原决定且
requires_acceptance时才发固定bundle/artifact refs。M2默认生产入口将注入这两个实际适配。

WorkspaceController.start/list/reconnect读取实际服务器分页，最多64页×100，固定水位、
游标循环/过期或快照失效明确重读；同ID保留最高版本。原known链接可打开，但不冒充
服务器list来源。分页cursor不持久缓存，身份换源清理；不解析正文猜Run。

M1类型检查通过；37单元最终通过（原33+4实际格式适配测试），0失败/错误/跳过。
自身ignored apps/web/.test-results/u2-generate-m1.log、u2-typecheck-m1-final.log、
u2-unit-m1.log和unit.xml。首次类型误设Contract/DeliveryProposal有id，实际schema拒绝，
删错误假设；测试fetch无参tuple修实际transport签名。原失败log保留，不放宽DTO。

M1不是默认完整页面或真实模型验收。M2继续接默认列表/恢复/成果与真正正文；M3固定
未知接受持久查找ID而非许可、原receipt对账、取消/身份/刷新竞争；无receipt不换ID重发。
A可立即按正式签名审阅。真实联调需A可达后端/短期launch及场景会话ID，已请求转发，
不读A私有配置或model/admin key；缺来源记pending。本包完成后停止，不自动下一包。
