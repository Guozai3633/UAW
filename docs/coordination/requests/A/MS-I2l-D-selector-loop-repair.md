# MS-R2i：实际 PostgreSQL 子端事件循环修复

2026-10-10，A实际installed source联调，D M1已只读审阅，尚待合入。修复只由D改helper_host.py及D测试；A不改worker业务源码。

## 实际证据

A新增7个实际SQL/Web/Windows隐藏installed helper节点：首轮5失败/2通过为fixture错误（关闭listener对象仍保留，但connection.closed已设置；CapabilityUnavailable的实际code是capability_unavailable），修fixture后5通过/2失败。剩余logout/wrong_challenge两个子端应返回原业务拒绝，却输出dependency_protocol_invalid。

锁定`.venv/Lib/site-packages/psycopg/connection_async.py:101`明确拒绝Windows ProactorEventLoop。D helper_host.__main__的`asyncio.run(installed_main())`使用默认Proactor；A实际HTTP主程序已用`uaw.infrastructure.event_loop.control_plane_loop`，测试父端SQL正常。A installed子端现在需要自己读同一实际数据库进行当前会话/原挑战复核，不能用fixture服务避开此问题。

## 具体修复

固定helper_host的__main__使用已经存在的`control_plane_loop`作为asyncio.run的loop_factory；不要改全局event-loop policy、驱动/锁或部署D03。原隐藏进程、普通15秒/首次90秒和初始化stop期限保持。可先提交小阶段SHA，继续D本包。

验证实际隐藏双进程启动使用Selector loop，并在自有测试库消费当前SQL来源；A随后在A库复跑原安装子端的真实logout/错挑战拒绝。没有真人授权或用户目录访问，不能将此修复标成本人配对通过。保留D原41节点与A两个失败回执，不弱化当前权限断言。

A回执：ignored tests/.artifacts/A/MS-I2l/m1-installed-first.xml、m1-installed-fixed.xml/log。A固定安装模块/受保护配置入口马上发布兼容阶段标签；不需要同步或修改A工作区。
