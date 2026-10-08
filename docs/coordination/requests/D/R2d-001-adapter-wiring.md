# MS-R2d：控制签名阶段版与授权根装配契约

日期：2026-10-08；分支 dev/runner；固定基线 ms-i2g-start / `0bd8e2b8387a46e16435dc033956c2b69bb1a859`。
前两里程碑可审阅接口，下半包继续当前基线，不等待最终集成。未选择 D01/D03/D06，不开放 IPC/配对V2/文件动作/安装写入exec。

## 阶段版接口（里程碑1/2）

```python
ControlKeyBinding(device_id: str, key_id: str, credential_handle: str)
ControlCommandSigner(
    bindings: tuple[ControlKeyBinding, ...], *,
    directory: CurrentKeyDirectory, signer: ProtectedSigner | None,
    clock: Callable[[], datetime] | None = None,
)
await adapter.sign(draft: JsonObject, *, device_id: str) -> JsonObject  # RunnerCommand
await adapter.verify(command: JsonObject, *, device_id: str) -> None
```

实现已有 `RunnerCommandSigningPort`。绑定只由可信构造源固定，每设备唯一 key/handle，immutable mapping；不在 draft 添加选择 key/handle/owner 的字段。严格 schema 校验 RunnerCommandDraft，完整深拷贝，只增加 signature；不改 command正文/用户模型/期限/fence。
当前目录与 ProtectedSigner 必须同源，key_id/device/角色control/撤销均复核，control与device分离。sign 检查 expires_at/ctx.deadline，在 key/OS await 后及返回前重取时钟；取消直接传播，不把已在OS线程完成的读取视为执行授权。verify 不读取私钥，重新查询当前control key，真实验签并复核key；为了已接受恢复链，不以历史command期限拒绝 verify，它不是准入。
ProtectedSigner 改为 off-loop 当前key查询并提前复制 document，保持现有域/角色/私钥公钥匹配与当前key再查；没有OS/credential port无明文回退。签名 adapter本身不证明用户归属，只有可信服务装配才调用；A的 RunnerCommands 仍须独立登记/设备/Run/政策/闸门/lease/fence 全链检查。

```python
# 这些值来自独立可信控制服务登记，绝不来自模型/命令请求体。
store = WindowsCredentialStore(private_service_namespace)
protected = ProtectedSigner(current_key_directory, store)
adapter = ControlCommandSigner(
    (ControlKeyBinding(actual_device_id, registered_control_key_id, protected_handle),),
    directory=current_key_directory,
    signer=protected,
)
command = await adapter.sign(actual_registered_draft, device_id=actual_device_id)
await adapter.verify(command, device_id=actual_device_id)
# container.runner_commands.signer = adapter 由A在真实服务构造点注入。
```

缺device绑定/ProtectedSigner/credential backend为unavailable；当前key错误/撤销/签名或绑定错误拒绝；过期为deadline_exceeded。control绑定替换需要由A在可信构造/版本发布点更新，不能从任意签名选目录里的另一个control key。
OS随机命名空间仅测试；生产现有credential port无create-only CAS，provision_private仍须可信单owner随机handle，不能对既有用户handle执行覆盖/删除。

## 阶段实际回执

`uv sync --frozen`成功（按指令未选agent-engine extra，移除本工作区27个可选包，不修改锁）。
阶段命令：

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/runner/test_control_signing.py tests/unit/runner/test_real_keys.py tests/integration/runner/test_windows_control_keys.py --basetemp tests/.artifacts/D/MS-R2d/tmp-stage -q --junitxml tests/.artifacts/D/MS-R2d/stage-junit.xml
```

实际 **27 passed，0 failure/error/skip，1.85s**。其中1项真实 `keyring.backends.Windows.WinVaultKeyring`，随机 namespace/handle证明原来不存在→ProtectedSigner生成→OS保存/读取→真实sign/verify→重建store/目录→再签→撤销→finally删除并证明不存在。`tests/.artifacts/D/MS-R2d/windows-control-receipt.json`只含backend/status/随机namespace和handle/cleaned，无私钥/凭据/签名内容；真实OS成功且cleaned=true。其他26项为实际密码学配合明确memory vault fixture，不替代OS回执。不访问已有用户凭据，没有用户项目文件动作。

阶段源码SHA与单独交接SHA在D handoff/Git记录，随后继续里程碑3/4。生产trusted channel、native确认和正式key登记生命周期仍待A。
