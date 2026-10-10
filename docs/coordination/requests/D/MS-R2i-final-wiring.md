# MS-R2i 最终构造与验证

2026-10-10；实际E:/UAW/.worktrees/runner /dev/runner。D等待/取消组件及A实际installed来源消费已完成；本人首次批准、根选择和真实授权读取仍pending，不声称完整MS-R2或产品整轮接受。

## 固定来源和提交

初始干净→fetch tags→只读origin/integration正式DISPATCH→ff-only ms-i2l-start→HEAD精确8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0→uv sync --frozen64包。旧待发布准备字样未再导致停工。原MS-R2g/MS-R2h提交、失败/清理保留，没有reset/rebase/stash。

M1源码f400a928614805ab752ef648a4ac59d5b0090ee7、交接01c674dd5ea30d26ed269f89c821e98a995bf125；M2源码f37d44589ab874ebb3c8dca0f4806e06bde75a2f、交接0705e07bac4f407a41932279a2d89f274732694f；A实际SQL loop修复67154f807a9c7aa69139a34af190a1ec058819b0、交接ba003ebd0f5727caf34b7cbe4a645f7f78fe7eec。M3临时根恢复测试/本人指南f8bbeb7（完整SHA见handoff）。

A正式交接后核对远端ms-i2l-a1-source /9f2d41085728df5488a4850cc9c7433ede28512b、ms-i2l-a1 /348df5ae3032f898def9bd72a1b7e22cc21fe8c4；保存D新增提交、工作区干净后合并**准确A1标签**，merge250de348054fc109952189500afde4aabdc38573，无冲突，保留双方历史；再次uv sync --frozen64包。阶段非快进合并保留已经新增的D提交，不合并浮动integration或覆盖公共冲突；开工标签不移动。

## 接口和生命周期

```python
# 固定可信安装组装，不是模型/HTTP请求字段。
process = await HelperProcess.prepare(python=installed_python,
    assembly_module=installed_module, environment=trusted_environment)
try:
    ready = await process.start(first_start=original_checked_policy, on_progress=observer)
finally:
    await process.close()
```

兼容start()普通15秒；FirstStartPolicy原expiry/hash、最长90秒。一次monotonic deadline覆盖start写入、锁、全部帧和observer；await后复查UTC期限，不延长。on_progress单独不启首次模式，prepare身份仍15秒。成功仍只能actual ready，waiting不授予授权。

HelperBootstrapProgress.waiting(policy)一次四字段event/stage=enrollment/UTC expires_at/challenge_hash；≤4096字节，严格拒绝重复键/非有限值/错UTF8/额外字段/错hash或期限/重复waiting/普通模式waiting/EOF/closed/假ready。原failure code保留；旧event只传code，因此不猜原HTTP status。详见MS-R2i-stage-interface.md。

PipeLineReader用自有匿名pipe Peek+仅available字节ReadFile，短读在worker，取消先排空，不留blocked readline。host在factory.create前监听stop/EOF；取消初始化/native/服务，迟到helper在stopping下不listen且close。close共用清理任务幂等，已EOF stdin不写stop，原5秒正常退出后只回收自有Popen。固定host使用既有control_plane_loop的Selector loop_factory支持锁定psycopg，不改全局policy/锁/D03。详见MS-R2i-stage-cancel.md。

## A真实installed构造

```python
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
launch = await PreparedEnrollmentLaunch.prepare(
    container, owner=actual_authenticated_web_principal,
    python=installed_python, state_directory=installed_runner_data_directory,
    currency=actual_configured_currency, environment=trusted_install_environment)
try:
    ready = await launch.start(on_progress=observer)
finally:
    await launch.close()
```

固定uaw.infrastructure.installed_helper；环境仅protected namespace/launch selector。原配置/服务设置在OS凭据库，proof经真实EnrollmentProofServer/Client，SQL/Web full session、独立候选、当前role keys、实际OS实例复查，FirstEnrollmentDeviceFactory注入D进度，paired factory为A真实PairedInstalledFactory；不用body/SID/PID approved授权。子端Container/SQL和原pipe及4个random protected handles/2role keys由实际adapter关闭/撤销/删除。

新增6不同实测用固定模块、D55435实际SQL/Web身份及OS保护配置/证明/current keys：waiting后stop/EOF/父cancel/Web logout/key撤销原code，以及重启新OS实例/candidate/enrollment/challenge。账号是临时development认证账号，不是当前本人验收；未点击Yes，仍pending无pairing_ref，未读取用户目录。

A1仍缺：实际根Ticket签发/受保护交付、on_connected本人select/bind、父端RunnerDevices/Root/FileRoute/Tool当前authority。**缺源明确不可用，不用fixture补生产**。本人指南MS-R2i-human-guide.md；--run-human未执行，默认pending，旧手动harness也明确受控。真实本人根/read整链继续等待A输入和本人操作。

## 只读及恢复证据

D既有RootBindings、独立owner/authority、ReadOnlyRunner/签名journal保留。临时根fixture的账号/owner/challenge/authority与肯定UI明确受控；OS protected keys、UTF8临时读取、Ed25519、SQLite/CAS/一次journal真实。

成功：首次waiting后的原固定已登记command实际读取并设备签名。丢回复：先持久原receipt，丢弃transport回复，断线/新进程/新channel，删除文件并取消Run后只recover相同完整command/receipt/content Ref，attempt仍1。拒绝：unknown recover明确不可用、attempt为0；等待中owner/session或device key改变permission_denied，根Ticket未消费。原key/Root/lease/fence/版本/flags/当前数据权限复查，恢复不新准入或重发；不从Runner ok推Tool applied，不推failed/cancelled为not_applied/零费用。

## 准确计数和回执

644不同节点最终通过，0失败/错误/跳过：full638 /398.91s为A1合并前D最新运行逻辑；A1 installed新增6 /38.74s；合并后受影响72 /167.09s全部复跑，不重复累加。新增53=unit22+Windows startup/read25+installed6。未加入A19或旧产品1691。nodes.json按(classname,name)存最后通过回执；Ruff通过、格式71文件、Mypy34源码、diff通过。

```powershell
. ./ops/start-dev-db.ps1 -Session D  # 自有loopback55435
.venv/Scripts/python.exe -m alembic upgrade head  # 首次核对自有端口后
.venv/Scripts/python.exe -m pytest tests/unit/runner tests/integration/runner tests/unit/shared/test_contracts.py tests/unit/test_runner_signatures.py -q --require-postgres --basetemp tests/.artifacts/D/MS-R2i/full-temp --junitxml tests/.artifacts/D/MS-R2i/full.xml
.venv/Scripts/python.exe -m pytest tests/integration/runner/test_installed_first_start.py -q --require-postgres --basetemp tests/.artifacts/D/MS-R2i/installed-temp --junitxml tests/.artifacts/D/MS-R2i/installed.xml
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_helper_first_start.py tests/integration/runner/test_helper_first_start.py tests/integration/runner/test_helper_runtime.py tests/integration/runner/test_installed_first_start.py -q --require-postgres --basetemp tests/.artifacts/D/MS-R2i/post-a1-temp --junitxml tests/.artifacts/D/MS-R2i/post-a1.xml
.venv/Scripts/python.exe -m ruff check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m ruff format --check apps/local_runner/uaw_runner src/uaw/workspace tests/unit/runner tests/integration/runner
.venv/Scripts/python.exe -m mypy src/uaw/workspace apps/local_runner/uaw_runner --cache-dir .cache/mypy
git diff --check
.venv/Scripts/python.exe -m tests.integration.runner.helper_manual  # 默认pending，无UI
```

ignored tests/.artifacts/D/MS-R2i：full/installed/post-a1.xml/log、checks.json/nodes.json、ruff/format/mypy-final.log、public-hashes.json、human-pending.json/manual-default.log。7个原公共/锁/签名/组装hash不变；A1公共变化仅已交接标签导入，不是D修改。

当前保留174个不同random IPC namespace清理JSON均cleaned=true；installed两轮14个launch清理报告验证每次4 handles删除、2role keys撤销、自有process退出0、proof pipe关闭（重启节点两launch）。IPC回执文件名加namespace避免重复覆盖，已有副本cleanup-before-final保存，副本不重复计数。

原失败：初始unit identity double嵌套（raw工具历史＋m1-first-failure.txt）、直接pytest找不到tests包、旧5节点错误类型预期、单文件Mypy源码路径及IO/UTC offset类型；M2 EOF后重写已关闭stdin；SQL初始未迁移；M3期望漏command_ref；格式前长行/闭包、手动默认编码/文案长行。原m1.xml/log、m1-rerun.xml/log、m1-mypy.log、m2.xml/log、selector-sql.xml/log、m3.xml/log、manual-default-first.log与通过修复回执保留，没有删权限/签名断言、隐藏失败或重写原提交。A Proactor原两失败保留A回执，D自己用实际SQL验证修复。

只改D允许Runner/测试/requests/handoff；workspace四文件无需改。无新增依赖/公共DTO/RefKind/HTTP/IPC wire/配对V2/flags，不决定D01/D03/D06，不开放写入安装exec，不碰用户项目。实际最终源码SHA见独立D handoff；干净交付后本包停止，A负责真实根输入、本人、Tool/Model/页面和最终汇合接受。
