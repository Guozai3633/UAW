# MS-R2i 同包阶段：当前挑战的私有 registry 去重

2026-10-11，E:/UAW/.worktrees/runner /dev/runner。干净fetch tags、远端核对 ms-i2l-a4-source=e05b15801c0ef8104de740e5ef61ad03ffe92ce6，ms-i2l-a4=22de5d590256b77e428fc4b75750598b4d18e2df；只读消费公开 source，无浮动合并/标签移动、无reset/rebase/stash。原共同ms-i2l-start和所有源码/失败/清理保留。

阶段源码 **4c4cefe52e3bee59884498af2a1575e3678c83d1**：Runner ipc/channel_source.py、native_confirmation.py，D integration test_native_current_boundaries.py。公共 ports/read/authenticated_principal/session、ReadOnlyHelper构造/start/execute均无签名变化，A不需新接口/依赖/DTO或schema缓存，直接消费原RegisteredNativeChallenges（含installed的独立A挑战）即可。原15/90/120和更早Ticket/登记/grant期限不变。

策略：ConnectionRegistry._snapshot 是仅供同一current调用内部的纯元数据复制，不await、不IO、不缓存许可；验证字典仍指向原session、Ref/full device/角色、closed状态，构造现有严格RunnerChannelSnapshot。每次RegisteredNativeChallenges.current先registry.session真实check，取一次固定握手快照；独立owner/OS检查后再次取当前完整owner（序列化固定字段，避免借用adapter对象），最后真实session.check查双方当前登记/角色/key撤销/进程/期限，重新读原本机Ticket指纹、取同session快照和新clock复核。前后Ticket/full owner/channel snapshot任意不同均拒绝，原时间交集保持。没有执行许可或unchecked公共reader；外部registry入口仍自己检查，BootstrapNativeChallenges依然前后本机current +独立A current +fingerprint交集。

实际Windows/随机OS keys/原双进程IPC＋明示受控账号/current owner/challenge端口：单次完整Bootstrap挑战11次session.check；第二次仍新查累计22次，随后撤销device key立即拒绝/关闭原pipe，不拿第一次结果。静态原图20次降为11次是通道检查次数，不是SQL耗时/本人授权完成。本轮增强owner前后复核，固定A4旧实现预计登记get方法调用约113降86；该静态数不是实测SQL或性能收益，实际A source成本测量仍归A。

阶段63不同节点通过：stage-2 60/58.80s（38新增等待边界+原22bootstrap）及stage-4 4/4.11s（其中3新增、1重跑），不累加重复。first/final owner真实await期间角色/key/进程/主体/pairing/Ref/登记移除替换/原Ticket撤销过期/channel expiry/断连/取消全拒绝；实际OS实例错配拒绝；严格私有快照缺id/kind拒绝；冻结Principal故障注入不能改写基线。没有native肯定UI、用户文件或真人请求；自有进程/随机凭据finally清理。Ruff、77格式、Mypy34源码、diff通过；最终全面Runner兼容回归继续。

失败全部保留 ignored tests/.artifacts/D/MS-R2i-current-dedup：stage.xml/log 53pass/1fail，测试current owner替身在await前捕获并在await后返回旧对象，仅改变独立owner却不改变真实登记；修正为port在模拟IO后读当前值，保留原拒绝断言，另加故意早捕获owner但真实登记同时变化的前后两边界拒绝。stage-3.xml/log 3pass/1fail，正常Principal本来frozen，故障注入直接赋值被模型拒绝；改为明确绕冻结的测试故障注入，非正常source行为，stage-4复跑4通过。没有删安全断言、减少字段/末检或用permission cache隐藏问题。

```powershell
.venv/Scripts/python.exe -m pytest -q tests/integration/runner/test_native_current_boundaries.py tests/integration/runner/test_bootstrap.py --basetemp=tests/.artifacts/D/MS-R2i-current-dedup/temp-stage-2 --junitxml=tests/.artifacts/D/MS-R2i-current-dedup/stage-2.xml
.venv/Scripts/python.exe -m pytest -q tests/integration/runner/test_native_current_boundaries.py -k 'mutable_owner or missing_principal or full_bootstrap' --basetemp=tests/.artifacts/D/MS-R2i-current-dedup/temp-stage-4 --junitxml=tests/.artifacts/D/MS-R2i-current-dedup/stage-4.xml
```

A第四次本人“已选目录并确认只读”但journal1/grant0/原deadline失败保留。阶段并未续期或恢复旧grant，没有文件/模型通过声明；先受控source复跑测量，暂不反复要求本人点击。A4已交当前来源，A SQL profile setup因Docker不可用未到授权逻辑，不能当D失败或通过。D继续同包原Windows/native/root/IPC/读取/journal回归，SQL installed单列真实可用情况。A如要跨组件优化公共接口仍先明确提案，不偷改shared/A实现。

## 阶段候选接受阻断与修复（2026-10-11）

A实际消费者 m2-d-late-authority-before.xml/log 复现4c候选：最后state.get await时撤销control key，不改变device root Ticket，纯末尾metadata快照仍返回挑战。D自己late-before.xml/log同样1fail/2pass复现；这是D遗漏有效角色边界，不是fixture问题。4c候选及其11次check结果未接受、不能称权限验证完成。全面回归full.log已中断/superseded-full.json记录未通过，缺XML不算成功。

修复源码 **f0b397bbffa9c1202dd696b81664a433a87a4349**：最终Ticket读取后追加真实session.check，保留先前本机Ticket指纹与owner前后值，最终角色/进程/当前key/通道/期限检查结束后只做同步严格快照和新时钟判定。单次RegisteredNative.current为3次完整check，完整bootstrap真实测量14次（第二调用累计28且后续撤销拒绝），仍少于原5/静态20；不强锁11次数字。没有无限原子快照声明，returned challenge不是grant；恰在最后角色check中改变Ticket由原PairingVerifier批准/current revision/CAS拒绝，不开启UI或建立grant。

修复5节点通过/5.12s：final Ticket await中的control revoke、原Ticket revoke、取消；最后role check中的Ticket revoke不能批准/产生grant；14次真实bootstrap全量交集/新调用复查。原63不同阶段节点与新增4去重共67，完整最终源码的全面回归继续；不累加4c被中断的部分通过。

旧候选回归中断后，本session temp-full有57个实际IPC随机namespace，56有正常cleaned报告、1正在运行helper无finally报告；已确认无该temp-full自有Python实例残留，按唯一own helper-input中的随机namespace/两个handle和键库路径（必须位于本session temp-full）清除2自有凭据并复查缺失，撤销两role key，单独interrupted-cleanup JSON保留原退出为interrupted，不冒称正常退出0。未枚举/操作任何其他用户凭据或按通用进程名kill。全部旧清理/失败记录保留，新全面回归用temp-full-final。

D55435本轮TCP probe unavailable，SQL installed6节点尚未运行，不能将组件回归或A Docker profile setup失败称SQL通过；不启动其他session数据库。前轮真实SQL回执保留。这轮没有本人/文件/模型新通过声明，A先消费f0固定修复再测受控source，旧原本人确认journal1/grant0仍未绑定。

## 最终源码、回归与未通过项

最终生产源码 **f0b397bbffa9c1202dd696b81664a433a87a4349**，阶段文档62ae9258e80771d1bdf5832bb1a08c39c1b80941；前候选4c/静态11次目标保留为未接受历史。本轮无公共/A/锁/schema/factory/HTTP/flags编辑；7份原公共repository hash逐一一致。末尾真实role/pipe check仍是最终await，Ticket在该check内随后改变由原approve/current revision/CAS拒绝，不能将current返回值视为grant。

实际全Runner运行 **689不同节点：688通过、1失败、0错误/跳过，347.43s（XML347.260s）**。新增45等待边界均通过；原native/crypto/signature/current owner/根身份/期限/取消/并发/Admission/读取/重启签名content journal兼容均纳入此运行，不能与阶段节点或旧644重复累加。

唯一失败是既有 test_helper_first_start.py::test_installed_hidden_selector_reads_actual_session_d_postgres，在helper factory的sql-check首次读取UAW_TEST_DATABASE_URL时本轮未供给环境，helper bootstrap失败，尚未进入授权逻辑；同时D55435 TCP probe不可用。6个test_installed_first_start.py的真实SQL/Web节点明确未运行，合计7个SQL来源门槛未验证；不是权限测试跳过或用fixture冒充SQL。

```powershell
.venv/Scripts/python.exe -m pytest -q tests/unit/runner tests/integration/runner --ignore=tests/integration/runner/test_installed_first_start.py --basetemp=tests/.artifacts/D/MS-R2i-current-dedup/temp-full-final --junitxml=tests/.artifacts/D/MS-R2i-current-dedup/full-final.xml
# 真实SQL补验前只供给D独立环境，不使用A/B/C数据库：
. ./ops/start-dev-db.ps1 -Session D
.venv/Scripts/python.exe -m pytest -q tests/integration/runner/test_installed_first_start.py tests/integration/runner/test_helper_first_start.py::test_installed_hidden_selector_reads_actual_session_d_postgres --basetemp=tests/.artifacts/D/MS-R2i-current-dedup/temp-sql --junitxml=tests/.artifacts/D/MS-R2i-current-dedup/sql.xml
```

本轮已实际尝试上述Session D启动；Docker setup无响应、没有ready，D55435仍不通，未启动SQL pytest/无SQL XML。停止仅本次自有setup，sql-setup.log与sql-unavailable.json记录interrupted/not_passed，不算启动成功，不触及其他session DB；既有前包真实D SQL回执仍保留。外部Docker engine恢复并真实D库迁移就绪后才能补7节点；不以缺源改变授权策略。

最终Ruff通过、77文件格式、Mypy34源码、diff通过。ignored MS-R2i-current-dedup下 full-final.xml/log/checks.json/nodes.json/ruff-final/format-final/mypy-final.log/public-hashes.json；前候选中断full.log/无XML、stage/late-before的实际失败、late-after5通过、SQL setup未通过全部保留。371个不同保留随机namespace清理回执全部cleaned=true，完整与被中断回归236个配置namespace均被实际清理覆盖；无本session full-run helper进程残留。中断时1个own namespace补清理并标原退出interrupted，不能改成正常退出0。

A报告精确合入f0后的消费者源码4e303d01f8f1d90af45f380d8c319c8b261c4161，原最后Ticket/control revoke复现通过、74不同受影响消费者通过/45.57s、A Ruff/196源码Mypy通过；这部分是A的交接结果，不加入D688，也不代表A真实SQL/本人绑定或全产品验收。A5仅当前源/Windows边界阶段接受，D不合并浮动integration。当前actual caller构造/接口不用修改；A保持真实current/source查询与原更早期限，不做permission/schema cache。

本人第四次“已选目录并确认只读”证明窗口显示与本机decision，原journal1/grant0仍未bind、文件/模型0；此次组件修复没有新本人窗口或用户目录访问。A SQL profile/真实source性能及以后本人新确认由A继续，缺生产source503，不重发unknown命令，不从decision恢复旧grant或延长Ticket。写入安装exec/flags关闭，不决定D01/D03/D06。最终文档与独立handoff提交、工作区干净后停本包。
