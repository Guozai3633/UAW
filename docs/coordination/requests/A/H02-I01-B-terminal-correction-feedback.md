# H02-I01：本人成果纠正失败后的终态反馈与窄屏成果入口

2026-10-17。原 MS-U4 真实体验反馈修复，B 所有 apps/web；A 不代改前端。固定输入基线为 `ms-i2m-a8-source` / `fd50359ccd0c99f3416b5c0aeaf2375847f60dca`；保留 B 自身原交付与记录，不合浮动 integration。具体本请求的发布提交由 A 消息给出。无公共契约变更，不新增后台操作或自动重发。

## 已定位的实际问题

本人 H02-v2 会话先请求 AI 对就业影响报告，随后原 Run 纠正“尤其关注大学生就业”。第一版成果已登记；第二次模型输出实际 `finish_reason=length` / 2048 tokens，被错误归为 agent_request_invalid。原 Run failed、纠正保持 accepted，页面却继续写“已收到，尚待生效”，底部理解停留“正在等待实际任务理解”。A 负责输出容量与截断错误来源；原失败/用量/Artifact 保留。

## B 的修复及边界

1. 原 Run 已 failed/cancelled/completed 且 patch 仍 accepted 时，保留 received 的历史事实，但用当前权威 Run 终态说明“本次未生效，任务已结束”，failed 明确失败；不得继续暗示会自动执行，不把失败写成用户主动取消，不伪造 applied。
2. Run 终态后尚无当前输入版本 understanding，不显示持续等待或 loading；说明本次没有生成新的任务理解。旧版理解如展示必须标旧版本，不假装最新。
3. 检查 1050px 左右宽度下实际 Artifact 是否可达。本人截图只有“成果已登记，正文在成果栏”，未看到成果栏；提供窄屏也能打开的成果入口与实际只读正文/版本/核验展示。当前输入纠正失败后，旧成果仍为旧输入版本，不允许把旧 Artifact 接受为新结果。
4. 不替本人提交问题、重试、确认、目录授权或接受成果；不清除原输入/草稿。沿用当前 Page/session 和原去重机制。

## 验证与交付

定向单元/受控浏览器覆盖：accepted+failed、accepted+cancelled、accepted+completed，applied 正常保持；无 understanding 的终态；窄屏旧成果可读及 stale 接受禁止；刷新不重发。保持契约生成一致、类型、构建。阶段源码及独立 handoff 到达即给 A，保留原失败。不宣称整个 MS-U4 或 H02 本人验收通过。

当前真实服务为 http://127.0.0.1:5183；A负责可用性、原 Page 和最终 dist 切换，B 不自行登录/交换 launch 或代本人操作。
