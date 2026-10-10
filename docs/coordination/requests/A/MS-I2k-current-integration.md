# MS-I2k 当前集成与余下门槛

日期：2026-10-10。共同基线仍为 b7b79b150470a80f37b28fd52a2177f6de5b3124；A1已正式发布，不安排下一包。

## 已逐包审阅合入

| 包 | 最终源码 / 独立交接 | A合并 | 独立核对的worker回执 |
|---|---|---|---|
| B/MS-U2 | ab14fe3 / 0b6d9ed | b24baf1 | 44单元、19受控Chromium、1实际匿名TCP浏览器；5登录后场景pending |
| C/MS-T2h | 3ed6ef3 / c9853b2 | 758ecf8 | 369单元、81不同实际SQL；原219仅受影响45复跑，其余174未作为本轮重复覆盖 |
| D/MS-R2h | ba798ad / 1ff88c5 | 101c7c8 | 591不同节点、105随机凭据清理；本人确认及A生产bootstrap pending |

已独立核对允许目录、固定基线祖先、源码/工作区字节和原始XML节点，没有合并冲突，未修改worker分支/环境。详见[审阅证据](../../../implementation/evidence/ms-i2k-worker-review.json)。这些是组件审阅合入，A消费者/整轮产品接受另记。

## A实际消费者

- A当前Web登记协议和OS角色适配已发布ms-i2k-a1，15聚焦节点通过。真实第一次native配对来源尚未绑定，缺失明确503，不能将pending作为D已配对peer。
- 合并后A原管道、新bootstrap/helper及FileMaterial单元边界54节点通过，实际Windows/受控账号根来源分别标记；不是真人授权。
- FileToolBindings提供materials Adapter；可选FileContextMaterials保留原C资料/片段/观察Refs和完整original ctx，原登记只保存现有具名DTO，不复制文件正文。FileAwareContextInputs沿用原Context授权/recipe/ModelInput；普通来源保持原批读，文件来源逐次回C owning Reader。默认没有资料源时不可用。实际文件→Agent→成果/真人整链仍需验。
- 人工审批后的后台恢复正在实际SQL队列验证：只有原审批/原Tool context/原action及实际决定能恢复同一操作；pending不推进Run版本。Tool继续独立审批/预算/取消复查，拒绝不授予调用权限。

## 自动审批停止点

A自身前端固定锁依赖安装被自动审批拒绝，理由是本轮“安装保持关闭”。动作是pnpm固定开发依赖安装，涉及包仓库/依赖安装过程；未尝试旁路、未改B环境，已向用户明确申请这项开发环境例外。后台、SQL和源码接线继续。它不意味着UAW产品安装/exec工具需要或已经启用。

## 继续本包，不发新包

1. A收尾原后台批准/拒绝、当前文件来源消费的受影响SQL，记录全部失败和最终节点。
2. 前端安装仍未获例外许可；已采用获批的只读复制B交付构建物方式，核对源码/日志/构建hash后运行实际localhost页面，不安装或执行B环境。实际办公已运行3次固定DeepSeek，正文/核验可读；真人成果接受被自动审批判定不可代点击，等待用户完成原页面接受。学术草稿保留，原请求终态后继续。
3. 独立受保护首次native配对：原Web账号→当前两OS/key→完整challenge→本人窗口→双方签名owning证据→登记active→D helper；随后根选择/原Ticket-code-proof/current channel方可授予只读。
4. 文件到低信任Context/成果及撤销/丢回应恢复、真实审批拒绝/取消/刷新/合同接受；实际真人未点选始终pending。
5. 四组件与A消费者汇合后一次全量。上次1691和准备120均留旧来源，不当本轮全量。

不开放默认flags、子Agent/DAG、写入、安装或exec；账号设备登记也不是目录授权。
