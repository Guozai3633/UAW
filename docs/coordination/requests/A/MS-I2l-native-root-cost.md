# MS-I2l：本人确认后的绑定成本诊断

2026-10-11；同包后续工作，A4来源固定为 `ms-i2l-a4-source / e05b15801c0ef8104de740e5ef61ad03ffe92ce6`，消费证据为 `ms-i2l-a4 / 22de5d590256b77e428fc4b75750598b4d18e2df`。没有派新包或改变原授权期限。

## 已确定的停止点

第四次本人明确已选目录并确认只读范围；原本机 native_roots、native_decisions 各1，root_grants为0。父端原120秒期限结束，子端 private phase=native_select；实例/随机凭据清理完成，角色 keys 撤销。它证明原选择及决定已记录，不能证明当前授权绑定成功，不能恢复旧期限后再授予权限。原失败见 `docs/implementation/evidence/ms-i2l-native-root-visible-failure.json`。

D 对一次完整 challenge 的静态展开约为20次 channel check；当前 EnrolledPeerRegistry 每次 role current 又保留前后完整 get、OS与角色key复查。这是待测量的重复调用放大，不能将静态次数当实测耗时。

## A 测量入口

`tests/integration/agent/installed_diagnostic_fixture.py` 使用独立 web-platform 测试租户、实际 InstalledHelperAssembly/SQL/OS/IPC。默认目录对话返回受控拒绝；没有访问用户材料、没有真人授权结论。可通过测试环境 `UAW_TEST_INSTALLED_PROFILE` 指定 A 自有诊断结果路径；记录函数名/调用次数/CPU累计，以及各系统namespace的get次数和累计等待。没有保存原调用参数、主体ID、路径、凭据或正文，结果不参与授权判断。

复跑入口为 `tests/integration/agent/test_installed_pre_ui.py --require-postgres`。实际运行要求A开发数据库55432与当前锁环境，不能用缺失数据库的setup结果冒充通过。profile会增加开销，因此profile耗时不能直接当未经instrumentation的产品延迟；优化比较应使用同一测量方式，并另保留无profile节点回执。

另已准备 `tests/integration/agent/test_installed_root_binding.py`：在独立测试租户与临时目录中显式提供受控 DirectoryDecision，消费实际当前Web/原OS双进程/keys、原Ticket签名、owning journal、grant和当前channel；首次确认及目录选择都属测试输入。它只验证生产来源装配能完成绑定，不能证明真人同意或实际用户文件已读。原selected目录仅A测试临时目录，测试后排空自有helper并删除随机凭据；数据库恢复后实跑，当前尚未计accepted。

2026-10-11本次profile准备发生SQL ConnectionTimeout，131.37秒，仅setup error，没有进入授权链；原回执 `tests/.artifacts/A/MS-I2l/m2-root-profile-before.xml/log` 保留。Docker Desktop已启动，engine/read-only status仍未响应；当前等待用户核对界面状态，暂不启动新的真人确认。公开schema样例微测100次：Peer0.0189s、Candidate0.0413s、Record0.0500s、Evidence0.0198s。这只说明这些纯schema检查在该样例上成本较小，没有依据先增加schema结果缓存。

## 修复边界

D继续处理自己内部重复channel校验，原公共入口保持自足检查；一次内部挑战只能复用同一实际已登记session的不可变关系，保留完整前后current owner/OS/key/original Ticket指纹和独立A challenge复核。所有等待后、取消、撤销、原更早期限与签名来源检查保持。不能缓存权限、修改old Ticket/grant、延长确认窗口，或以确认记录替代当前grant。

A继续提供实际来源测量、当前安装消费者与逐包审阅；如有A来源优化，仅在A允许路径完成并给准确阶段来源。最终需实际SQL/OS/IPC原链复跑，再请求本人新实例确认；在此之前不重复弹窗，不开放files/exec/write/install flags，也不将本轮标记整轮accepted。
