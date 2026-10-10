# MS-I2l D 修复：真人根选择共用60秒 IPC 授权窗口

2026-10-10。当前包真实消费者修复，不派新功能包、不移动 ms-i2l-start。

## 实际问题

A3源码 `ms-i2l-a3-source / 5fbfa752f6d83a3e663b98b6b002eb8a481e8b3e` 已真实跑 installed 首确认→双方 OS/keys→原 native journal→当前父端握手/RunnerDevices.bind。两次本人目录确认均未完成即返回 `ipc_timeout`；正文读取和模型调用都为0，自有实例/随机凭据已清理。

第一次 root Ticket expires_at 是 `2026-10-10T13:43:41.557862Z`，父端结束日志时间 `13:43:42.140433Z`；无 native_decisions 或 root_grants、confirmation_expires_at 为null，自有key撤销把原pending ticket封为revoked。没有把超时当拒绝或通过。第二次回执亦保留。

人需依次看账号窗口、选择目录、看只读窗口；用户还在询问应选择哪个目录时短时连接期限已经到了。现 `ReadOnlyHelper.accept()` 无参地使用 AuthenticatedPipeSession 默认60秒；authorization() 无参地使用 WindowsNativeConfirmation 默认60秒。A不能在旧连接/原grant上加时，也不能在自己的子类复刻D权限/IPC实现。

## D 范围与兼容修复请求

请仅修改 D 当前包允许的 runtime/native 及 D 测试/文档，保留原源码/回执。可读取准确 A3 tag，不合并浮动 integration、不改公共 DTO/flags/锁，不更改原 HelperProcess 普通15秒/first90秒或首次账号 native60秒。

建议在 `ReadOnlyHelper.__init__` 增加两个仅可信装配可供给的关键字参数（默认兼容）：

```python
session_lifetime_seconds: float = 60
native_timeout_seconds: float = 60
```

严格有限数、拒绝bool，`0 < native_timeout_seconds <= session_lifetime_seconds <= 120`。accept 将 session_lifetime_seconds 传入原 AuthenticatedPipeSession；authorization 将 native_timeout_seconds 传入原 WindowsNativeConfirmation。所有会话/native期限仍取当前独立注册来源与原ticket的更早值，重连不延长原根授权。没有开启write/install/exec，没有 native approval/path输入。

A将在明确 root_workspace 的可信 installed 新实例中配置120秒，普通实例保留60秒；父端同一新session也配置120秒，最终握手仍双方较早期限。新Ticket明确展示新期限，不修改旧ticket/grant，也不在错误后自动批准或复用旧确认。

如D发现更合适的兼容签名，请先交阶段接口；实现自己范围中的适配，A跟进消费。需实际测试参数边界、默认60兼容、120注入、短原注册/ticket不得延长、取消/关闭及原read/recover不绕当前期限；pytest节点去重说明、静态回执、阶段源码与独立handoff。模拟native不称真人通过。组件修复后A重新做人真实验收。

## A 当前停止点

没有成功的真人root grant，也没有文件内容/模型/产品flags开放。D修复未到前不反复弹60秒窗口。A继续保存失败、明确workspace目录说明、准备父端与installed子端消费；正向真人验收等待新明确装配后进行。
