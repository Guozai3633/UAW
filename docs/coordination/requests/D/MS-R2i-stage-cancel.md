# MS-R2i M2：初始化取消与 A 接线输入

D E:/UAW/.worktrees/runner /dev/runner，基线 ms-i2l-start /8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0。M1 f400a928614805ab752ef648a4ac59d5b0090ee7，阶段交接01c674dd5ea30d26ed269f89c821e98a995bf125；M2源码 f37d44589ab874ebb3c8dca0f4806e06bde75a2f。

host 原 HelperAssemblyPort.create(identity)->HelperApplication 签名保留。start 后先订阅自有 stdin stop/EOF，再调用 factory.create；监听贯穿初始化、native 和服务期间。取消 drain factory；factory 晚返回时 stopping 阻止启动 listener，关闭实际返回 helper。原 serve/disconnect/native 自有窗口、线程、OS句柄和管道清理复用。stdin/stdout Peek+短读没有等待输入的阻塞 executor 线程；停止后取消并排空读任务。close 共用同一清理任务；已经关闭的 stdin 不再写 stop，正常等待最多原5秒，强制回收只针对原 Popen。

实际 Windows 隐藏两进程18不同节点通过 /70.67s，0失败/错误/跳过：16秒等待越过普通15秒仍只返回 actual ready；错误hash/期限/stage/额外/重复字段/重复waiting/超长/断帧/退出/拒绝；普通模式不能被observer启用；初始化stop、EOF、父取消、期限、迟到helper关闭；实际 native 窗口仅自动取消，worker排空标记；所有自有进程正常退出0、父streams closed。random vault keys finally 删除后复查，所有临时文件属于D测试根。回执 tests/.artifacts/D/MS-R2i/m2-final.xml/log。Ruff/Mypy34/diff通过。原 m2.xml/log 为17通过＋1 EOF close重复写已关闭stdin失败，保留，修正后全部通过。

## A 必需输入与装配

固定契约不变：A installed assembly.assembly 必须独立提供真实 RunnerEnrollments（完整认证账号/当前候选）、目录及 ProtectedSigner OS handle、原 EnrollmentProofClient locator、WindowsEnrollmentConfirmation 和实际 paired_factory；FirstEnrollmentDeviceFactory(...,progress=HelperBootstrapProgress())。父端只在独立登记/原 challenge 当前复核后构造 FirstStartPolicy，并启动 proofServer.serve_once 与 start(first_start=policy)，最后关闭 server/process。active同原实例普通模式，不重新确认；重启新PID/创建时间重新登记。

A native timeout 必须保持契约最多60秒；证明10秒/进度回调5秒均包含首次唯一90秒期限。A创建源在取消后释放自有SQL/OS/native；D排空返回的helper。拒绝 DomainError code 保留；waiting不是授权/ready。fixture native Yes与生产当前来源不可互换。

截至本阶段再次fetch并只读 origin/integration/DISPATCH，仅共同标签和固定契约，无新 installed locator/可信每次启动配置/完整 paired factory 阶段发布。D不合并浮动integration、不修改A/shared/HTTP/锁、不造生产登记。最小缺口是上述现有接口的可信安装交付示例/模块及来源生命周期，而非新增 DTO。A发布具名阶段后D消费；缺源503。继续本包独立M3/M4：首次等待后的原临时根只读、实际签名journal和丢回复恢复；本人操作pending，不读本人未授权目录、不开放flags/写入安装exec。
