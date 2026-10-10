# MS-R2i M1：固定首次启动接口

2026-10-10；D worktree E:/UAW/.worktrees/runner，dev/runner。远端正式 DISPATCH 与标签核对后 ff-only 到 ms-i2l-start / 8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0；uv sync --frozen 成功。原 MS-R2g/MS-R2h 提交与失败/清理记录保留。

M1 源码 f400a928614805ab752ef648a4ac59d5b0090ee7。消费固定 src/uaw/shared/runner_bootstrap.py，不改公共契约/锁/flags。

```python
# A 在可信安装 factory 注入发送适配；不是请求参数。
progress = HelperBootstrapProgress()  # uaw_runner.helper_host
factory = FirstEnrollmentDeviceFactory(..., progress=progress)
# 父端 policy 只能由 A 当前原 challenge 复核后构造。
process = await HelperProcess.prepare(python=installed_python,
    assembly_module=installed_module, environment=trusted_environment)
try:
    ready = await process.start(first_start=original_policy, on_progress=observer)
    # waiting 回调不等于 ready；只有实际 ready 才返回。
finally:
    await process.close()
```

兼容普通 start() 为15秒；首次 policy.remaining(current UTC) 仅计算一次，最长90秒、不超过原挑战。一个绝对 monotonic deadline 覆盖写 start、锁、帧、observer；帧/回调后再查墙钟期限。on_progress 单独不能开启首次模式。prepare 的实际身份检查仍15秒。

waiting 仅四字段 event/stage/expires_at/challenge_hash，stage=enrollment，UTC expiry 与原 policy 完全相等；一次且最多4096 bytes。重复键、NaN/Infinity、错 UTF8、额外字段、错 hash/expiry/stage、普通模式 waiting、重复 waiting、EOF/closed/假 ready 拒绝并 close。failure 保留原 code，返回 DomainError；旧将所有失败折叠成 CapabilityUnavailable 的测试更新为原错误断言。close 仍5秒正常退出后只回收自有 Popen。

PipeLineReader 使用实际自有匿名管道 PeekNamedPipe + 仅可用字节 ReadFile；每个短读通过线程，取消排空短读，不留 blocked readline。下一阶段 host 初始化 stop/EOF 将复用它；本阶段 host factory 初始化取消尚未完成。

验证：python -m pytest tests/unit/runner/test_helper_first_start.py tests/integration/runner/test_helper_runtime.py：41 passed /56.96s，0失败/错误/跳过。最新源码单元22 passed /0.41s。Mypy34源码、Ruff、diff通过。回执 tests/.artifacts/D/MS-R2i/m1-final.xml/log、m1-unit-final.xml、m1-mypy-fixed.log。真实 Windows 隐藏 helper/OS随机角色凭据/IPC和原 journal 恢复；账号/owner/authority/native Yes 明示受控，非本人确认。

原失败保留：unit identity double 写成嵌套 __dict__，直接 pytest 启动找不到 tests 包，旧5节点错误类型预期冲突，单文件 Mypy 缺源码路径及 IO/UTC offset 类型、格式前长行；修正后全部通过。没有删除当前权限和签名断言。

A 仍需真实每次启动的安装配置/locator/full account/current key 登记及 paired factory。基线 FirstEnrollmentDeviceFactory/EnrollmentProofClient 已有实际源端口，但本阶段未造生产配置；缺源503。本人点击 pending，写入/安装/exec关闭。本包继续 M2–M4，不自动进入下一包。
