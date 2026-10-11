# MS-R2i 独立 D55435 SQL补验（2026-10-11）

实际E:/UAW/.worktrees/runner /dev/runner；生产源码仍f0b397bbffa9c1202dd696b81664a433a87a4349，原handoff3a47f79fd21c149f5ec84009413d0115b835b0ec保留。本次仅补7节点，不改源码/flags/锁/公共接口，不重跑688。

干净核对后fetch tags，远端A5 source4e303d01f8f1d90af45f380d8c319c8b261c4161 /metadata7581abde1d979f98abaadb93af8378e8b6bd319b与本机标签一致；没有合并浮动integration或移动start，保留原基线。D installed消费本worktree既有A1固定来源；A消费者回执不计入D。

Docker来源恢复后，仅Session D独立uaw-development-d/55435启动；两个环境URL验证127.0.0.1:55435/uaw_dev，当前worktree现有alembic upgrade head成功exit0。未使用其他session DB/重置/清库；测试只清独立principal/本轮launch，不truncate。秘密未输出。

```powershell
. ./ops/start-dev-db.ps1 -Session D
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m pytest -q --require-postgres tests/integration/runner/test_installed_first_start.py tests/integration/runner/test_helper_first_start.py::test_installed_hidden_selector_reads_actual_session_d_postgres --basetemp=tests/.artifacts/D/MS-R2i-current-dedup/temp-sql-resume --junitxml=tests/.artifacts/D/MS-R2i-current-dedup/sql-resume.xml
```

7不同节点通过/29.57s（XML29.555），0失败/错误/跳过：原未供给DB的sql-check1节点与未运行的installed SQL/Web6节点。与原688通过节点按class/name取并集，最终695不同Runner节点通过；不累计重试/阶段/A74，原689日志的688pass/1fail保持原样，nodes-final-with-sql仅以新同源码回执覆盖失败状态。

实际SQL/Web认证会话、原首次challenge/登记、受保护proof/current roles、隐藏Windows双进程/Selector、原IPC/等待/注销撤销/取消/重启来源验证。肯定本人确认/真实根bind/用户文件/模型/Tool产品验收不由这7项证明；没有自动Yes或新production登记，原本人journal1/grant0失败继续保留。

7个installed launch清理报告逐一验证：各4随机protected handles已删除/复查缺失，2role key撤销，自有process退出0、proof管道关闭；sql-check原IPC fixture亦finally清理，无temp-sql-resume helper残留。首次receipt定位脚本glob根目录漏7个嵌套报告的assert错误保存sql-resume-audit-first；按rglob/resolve去重7份复查全通过，不是测试失败。未枚举用户凭据或泛kill进程。

回执ignored tests/.artifacts/D/MS-R2i-current-dedup/sql-resume-setup/env/migrate.log、sql-resume.xml/log/checks.json、nodes-final-with-sql.json、audit-first.json和嵌套installed-cleanup JSON；旧缺源/中断/候选失败全部保留。源码无变，原Ruff/77格式/Mypy34/7公共hash回执继续适用，本次doc diff通过。

本补验闭合D组件真实SQL门槛；A负责真实source性能、本人根绑定与整链回归。既有接口/构造不变，source缺失503，不从SID/PID/body approved推权限，不延长旧Ticket/grant或cache许可，不重发unknown。content Ref/journal恢复保留，写入安装exec/flags关闭，不决定D01/D03/D06。独立docs/handoff提交、干净停本包；独立D开发库保持供后续明确验证，不删库。

文档首次写入/提交因自动审批服务deadline超时未执行，确认文件不存在后按已有授权重试一次；不是测试失败或被认定不安全，不绕过审批。
