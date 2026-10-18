# 普通回答的增量读取

沿用原认证会话与HTTP传输。`GET /v1/conversations/{id}/events?after_seq=N`只返回该会话在固定页水位内序号大于N的事件。N默认0、必须为非负整数且不超过所属历史；分页cursor绑定所有人、会话、原起点和水位，续页不能改变起点。超前、缺历史、过期cursor要求重新读取快照。`items`快照不接受事件起点。

正文检查点仍是`item.updated`，携带同一`InteractionItem`的完整正文前缀和递增revision，而不是要求客户端拼接字符串。先读原Item快照，再按事件序号应用新版本；重复事件和旧版本不会重复正文。刷新和读失败仅GET恢复，不重新提交Run或模型调用。

`in_progress`表示收到部分实际内容，`completed`仅由原Agent/Model/Run完成事务发布。中断的Item为`failed`，保留原前缀；不能引用为最终答案。模型接收完毕并不表示Run完成；取消后若缺usage，原费用和预留保留待核，Run可能仍为stopping。正式成果的核验、登记和本人接受保持原契约。

内部严格[ConversationStreamRecord](objects/ConversationStreamRecord.md)关联原Run、输入版本、invocation、attempt、上下文及固定模型。只有conversation-v1的reply正文可显示；JSON、隐藏推理、工具参数、提示词不进入此消息。提供方不兼容时保留具体失败，不换模型或模拟正文。

原`RunPresentationView`增加可选`stopped_reply_ref`。只有原Run已请求取消、原后台job已blocked、首步的唯一普通回复流及实际调用均已失败停止、原输入/消息对应且没有工具上下文时，才返回这份只读证据。网页重新读取该证据后可清除本地原请求查询锁，让新会话提交新问题；它不会释放服务端预留、结算费用、修改Run或允许旧Run续跑。来源缺失时仍保留原锁。

接口生成支持显式`node scripts/generate.mjs --working-tree`供提交前预览，来源manifest标记`contract_commit:null/release_ready:false`。正式部署仍需生成器绑定准确已提交接口SHA，再生成类型与运行时schema；预览不能当成固定发布证据。

[设计及目录](../implementation/MS-I2m-A18.md) · [事件接口](interfaces/http--events-read.md)
