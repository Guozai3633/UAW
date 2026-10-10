# B/MS-U1：A 最小接线缺口（2026-10-10）

固定输入 ms-i2j-start / abb4590f2bfe53c601e0f6a4a3b65447ba4ec502；B不改后端/共享契约。

1. 浏览器入口：基线 authenticate 对 Origin 拒绝且只有CLI bearer。请A发布准确
   localhost Origin/HttpOnly用户session/CSRF/退出清理协议、服务地址和能力清单。
   B不放管理员token/模型key到Vite变量/持久浏览器存储，也不通过删Origin绕过认证。
   B客户端 same-origin cookie/no-store；CSRF header名称与值仅由已认证host注入内存，
   默认无header且入口不可用，尚未假定服务端接受任何新header或session字段。
2. conversations.list 未在 routes.py 实现。B侧栏保存本人已创建/打开的非敏感会话ID，
   每次重新GET conversation；完整服务器列表等A清单，不猜路由。
3. 原 request_id 查询缺失：turn提交meta有持久幂等request_id，但没有HTTP按request_id
   查询的路由，InputRecord/Event不带该meta映射。请A发布查询原请求→原Run或明确未知
   的兼容契约。B已知Run可GET，未知发送保持“待对账”且不重发，不用匹配文本猜Run。
4. ArtifactRecord/VerificationReport/CompletionBundle/Acceptance已有schema/领域实现，
   但成果内容/合同读取及整份接受HTTP不在实际路由。请A提供准确读取/接受子集、不可变
   bundle/contract/artifact/report pins与CAS错误。B实现只读预览和可选内部ReviewPort，
   默认不可用、不造URL、不把屏幕文本或Item文案当合同接受。ReviewPort不证明后端存在。
5. DraftPreview仅有schema及事件，无实际预发送HTTP。输入框上方保持浅色自适应框，
   修改草稿立即清理旧提示；发送后消费TaskFrame.summary/understanding事件，不离线
   摘要冒充AI。不新增预览路由。
6. events.read 是固定watermark分页，next_cursor只在该快照内继续翻页。轮询完整新快照
   +seq去重，cursor_invalid/snapshot_required取新Item/Run权威快照。基线无SSE，UI明确
   分页轮询。后续A兼容清单到达再接真实SSE或增量读取，不解析模型文字猜运行完成。

消费方：B Web工程、A认证/API/composition与成果控制。最小变更由A集中发布、契约生成，
按约定里程碑同步；B继续独立工程/页面/恢复/受控测试。真实发送→模型→成果及用户接受、
审批取消、重连联调均pending，不能用mock或现有设计OpenAPI全路由冒充实现。


## 2026-10-10 M4更新（保留上方原提案历史）

A1已公开ms-i2j-a1 / 202544f452c485c84eb7fe08675576e31c75cad3会话协议。
B已消费实际exchange/get/logout、fragment清理、内存CSRF、期限/身份清理与显式保留
Origin的5173→8000代理。源码最终 d2ece8d1682a4ae1de2ed811fc24e304e3584569，不再把会话HTTP列为未发布。
当前实际8000端口不可达、真实试验环境未提供，不能把受控exchange fixture记为真实认证。

剩余最小公共变更及影响：

- A公开原conversation/request_id→Run只读权威查询，保持原主体和idempotency登记。
  B RecoveryPort只消费原Run；无接口时unknown发送始终待对账，不重发或正文匹配。
- A公开本人会话列表。B目前只展示已知链接/创建/本地查找ID，通过GET复查，未伪造列表。
- A发布实际Artifact全文/VerificationReport/固定CompletionBundle及合同决定契约，
  由adapter满足B ReviewPort，保留当前主体、Ref kind/id/version/可选hash、取消和CAS。
  缺适配只显示服务端Item摘要，合同接受不可用；HTTP成功不代表completed。
- A提供接受决定的原request_id/bundle对账或已接受状态的权威只读恢复。
  当前视图派发未知或成功后阻止重复，刷新只GET、无自动POST；不能拿未变化报告当新
  决定许可。适配器须读当前接受登记，不能持久缓存前端审批/接受权威。
- A实际后台固定Model/单Agent/成果控制端运行；B queued/202只当受理。SSE仍无handler，
  B分页轮询不假造流；本机目录授权另走A/D真人选择，网页不接路径授权。

不在本提案指定服务器路径或新DTO字段，不改shared/schema/Run/Model/组装根。
仅A改公共契约及生产适配；B按准确固定发布消费。完整回执[最终接线](MS-U1-final-wiring.md)。
