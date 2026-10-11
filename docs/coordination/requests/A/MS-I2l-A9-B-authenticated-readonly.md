# A9：B 的真实认证只读联调来源

2026-10-11。A 负责准备来源。B 原阶段源码与工作区不变。

## 已核对的契约冲突

`BrowserSessions.exchange` 消费一次性 launch ticket 后创建新的 `web-session-*`。`InstalledLifecycle.record/get` 检查完整原 owner（包含 auth_session_id），而非只检查账号 ID。因此，新 launch URL 与旧本机 launch_id 的组合不能读取旧实例。不得为了联调改成同账号可接管，或把拒绝响应当通过。

B原脚本先交换新ticket，再GET原实例；三个环境变量即使齐全也不能证明来源满足。B最终提交394d785已修为读取原拥有者页面：UAW_U3B_OWNER_CDP_URL、UAW_U3B_WEB_URL与UAW_U3B_LOCAL_LAUNCH_ID，不再交换新ticket。A尚未提供有效原实例来源，也没有运行新的本人连接、目录授权或成果接受。

## 可行的实际准备顺序

1. A 核对真实 localhost 后台和准确 B 构建。
2. 在同一个真实测试浏览器上下文中先交换短期同源 ticket，保留原会话。必须在 ticket 原 120 秒内消费；不能公开 URL、cookie 或 CSRF。
3. 若验证真实本机实例，用户在这个相同上下文中明确点击连接，并完成本人系统确认。A 核对原实例 owner 与当前会话一致。不得把在另一会话创建的实例移交给它。
4. B 在上述同一个上下文中只 GET/刷新，不重新交换 ticket，不 POST 连接/停止，不点 native/接受。原实例当前失败或关闭状态可如实验证展示，但不能称 ready 或文件执行通过。

B已提供apps/web/tests/u3b-readonly/owned-page.ts中的verifyOwnedInstalledPage(Page,id)，以及连接明确原测试浏览器CDP的入口。该页面仅GET/刷新与状态展开，拦截写请求，不点击连接/停止/native/成果接受。A应提供自己测试上下文的原页面，不能导出cookie、复制storageState或连接其他浏览器来冒充原拥有者。组件修改归B；A不代改前端源码。

## 当前执行限制

历史localhost只读探测被自动审批审查因额度拒绝，动作未执行；后续新审批已允许SQL/OS/IPC与localhost检查。当前A实际后台8000已启动，B最终构建的私有副本5173可达、三文件SHA与B交付一致；匿名同源/v1/web/session返回401。后台是A9中途来源，不自动热更新。完成阶段源码后需按准确进程重启。

computer-use当前浏览器清单显示本任务IAB无tab，没有原拥有者页面；旧实例已过期关闭。不能用新会话接管旧launch_id，也不能从服务端复制cookie。需要在同一个真实页面建立新原实例，再由B只读/刷新；A本次没有代点连接、确认、目录授权或成果接受。实际认证只读仍pending。

A9 源码与阶段接线继续；本说明不代表新的产品验收、权限开放或向 B 聊天已发送消息。
