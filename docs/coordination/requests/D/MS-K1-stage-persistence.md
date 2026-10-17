# MS-K1 M3 与 A6 实际消费阶段

实际 E:/UAW/.worktrees/runner / dev/runner，基线与M1/M2见MS-K1-stage-clock.md。
阶段源码 **3f58011e0a8464b8a8d90b63b2d046a6a061c344**，M1/M2原81d8f998/aae77f0保留。

## 真实SQL与D修复

41不同D组件节点最终通过23.90秒：8纯计量＋33真实D55435 SQL。
覆盖原conversation事务clock/binding CAS同expected单赢家、同键原回执、外层失败全回滚；
两次1200/1800秒可信模拟等待、重启不重领原主动额度、超额stop真实保存与不能恢复；
取消/终态、owner/input/question/item/pin/原上限变化、缺库存/nonNone/异常/取消、await后来源变化。
单独隐藏Windows新进程并发2次CAS及第3进程重启读取，1赢家、1个409，全部自有进程finally退出；
标准库subprocess在工作线程等待，不阻塞control-plane事件循环、不调用运行时asyncio.run桥接。

D新增修复：waiting clock在Run已终态时仍能stop；原问题/Item/decision/hash/input所有当前来源
独立严格核对，不能用ClarificationView强制开放问题只存在于waiting状态而阻止如实计时收尾。
问题仍open时绝不恢复active；不把终态stop当成问题已answered。构造和A/D port字节不变。
Ruff/新源码Mypy通过，所有初轮测试/样例/类型/格式失败保留。

## A6实装边界和输入

D新增test_actual_consumers.py消费A实际SQL队列、RunIdleEffects、Model/预算库存、补充受理/applied、
ExecutionSegments及终态收尾。HTTP模型回复/服务时间明确受控，无真实模型新调用、本人操作或native窗口。
首批5passed/62.76秒：真实库存的known billing_pending可pause；held/claimed/unknown拒绝。
其中所谓late answer仅部分A服务采用未来时间，不足以证明严格跨墙钟。
已加严：conversation_resume也采用同一未来可信服务时间，原成功断言不改，
在A6已知条件位置返回503/conversation.new_active_execution_segment，1 failed/12.42秒。
原41组件通过独立保留，不把此失败列成功或删除。A已说明自行修复A期限条件并将发布固定A7；
D不改A源码、不加时、不绕过原source；待准确A7正式发布后同包消费复验，不等新业务包。

M1/M2固定装配仍是ExecutionClocks(records,effects=RunIdleEffects())，同A提供原tx写clock和binding。
A默认Container/正式服务与真实长等待/模型/本人H02仍pending；当前受控测试不是产线验收。
ignored回执tests/.artifacts/D/MS-K1包含component-final.xml、m4-first.xml、m4-a6-strict-wall.xml、
全部red/失败/子进程检查；旧Runner/A21/失败和cleanup不修改。继续M4，不扩本机链/flags/子Agent/DAG。
