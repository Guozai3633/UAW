# MS-I2l：A3 父端当前通道与可选本人目录选择

这是内部安装生命周期消费，保留 `ms-i2l-start` 与既有公开四个 enrollment HTTP。
本阶段没有新增 HTTP、native 批准字段、文件路径请求或默认开启 flags。

## 入口与来源

```python
launch = await PreparedEnrollmentLaunch.prepare(
    container,
    owner=current_authenticated_web_user,
    python=actual_base_python,
    state_directory=explicit_internal_installed_state_directory,
    currency="USD",
    environment=trusted_installed_environment,
    root_workspace=fixed_workspace_ref,  # 可省略；省略时绝不弹目录窗
)
try:
    await launch.start(on_progress=original_first_start_observer)
    channel_ref = await launch.connect()
    connection = launch.connection
    # connection.registry/devices/session/peers 是本次自有连接的当前来源。
    # connected/device active 仍不是根授权或 file.read 通过。
finally:
    await launch.close()
```

`python` 必须是实际进程解释器。Windows venv forwarder 的 PID 与最终子进程不同，仍按原独立 OS 门槛拒绝；部署可用 base Python + 固定安装库目录，不跳过 PID/创建时间检查。

`connect()` 不收 ready/address/owner/proof body。它只能消费本对象真实 start 存下的 ready，用当前原 enrollment/双方实际 OS 实例、当前角色公钥与 OS 私钥、原 native journal 进行签名握手。控制端登记实际 ConnectionRegistry 的精确 channel；D connected 事件必须同 pin；RunnerDevices.bind 使用原 controller、当前来源和 expected_revision=0。最长30秒初始化，原 pipe10秒/session60秒/enrollment期限均保留；没有延长原授权。

close 取消并 drain 自有在途连接，再关闭 session/registry/helper/proof、撤销自有角色 keys、删除随机 OS 凭据。SQL bind 若已经提交后才取消，close 按原 channel 与 owner 定位并撤销自己的 binding；不撤销其他通道。资源清理失败明确报错，不以“关闭了部分”当全部完成。journal 留存；关闭后的 key/连接不能继续提供数据权限。

## 本人目录入口

内部 protected InstalledLaunch 兼容原准确字段；可额外有一个 `root_workspace`。它必须是固定 workspace Ref，无 location/access_scope/path/approved；null拒绝。此 pin 只是此次可信本机装配请求绑定的逻辑工作区，不构造公共项目所有权或读取用户目录。无此字段行为不变。

`PairedInstalledFactory` 有该 pin 时提供 D 既有 `HelperApplication.on_connected` callback。只有真实握手完成并当前 bootstrap/owner/key 有效时，callback 独立登记原 LocalState root Ticket。期限取当前 session/enrollment 的较早者，随机 code 和 device 私钥证明仅内部流转；ticket 持久写入取消时 drain。然后走 D `NativeReadAuthorization.select`：本人在原生窗口选择目录与确认只读，原 journal → RootSelection 签名 → auth.bind 原 workspace。此步骤不由前端/模型传批准或原始路径。

返回前再次复核实际 bootstrap。重连不再开 UI，也不认为第一次必定通过；每次后续 command/recover 都由 D 当前 owning RootSource 检查原 grant/用户/角色 key/版本/期限，第一次拒绝后没有 grant 的读仍拒绝。callback 记录是否尝试过只控制弹窗次数，不缓存当前权限。

## 可审阅的真人验证入口

`ops/check_installed_readonly.py --settings <本机私有部署配置> --state-directory <绝对内部状态目录>` 只验证真实账号/设备首确认与父端连接。可额外 `--workspace-id <内部固定逻辑工作区ID>` 触发上述本人目录流程；不给目录路径，也不读取任何项目文件正文。

诊断使用实际用户 bearer 认证与临时 Web session、实际固定 installed 模块、原 SQLite/SQL/native journal；核对原 consumed root ticket/device 签名和本人 owning decision。输出只含状态/摘要/清理范围，不输出验证码、私钥、实际路径或正文；finally 关闭自有 launch 与临时 Web session。它不等于页面 onboarding 已接好，不留一个持续授权实例，不开文件 flag，不执行模型调用。

## 验证与当前缺口

32不同聚焦节点通过：14新控制/root单元、9原 selector 单元、2新真实SQL/Windows protected selector节点、7原 installed SQL/Windows兼容。native/root肯定和负例 callback 在单元受控；SQL案例不进入 native。196源码 Mypy，Ruff通过。测试不能证明父端实际正向握手或真人目录链已通过。

实际本人设备首确认历史已通过，但当次实例已关闭。新父端握手/本人目录尚待新实际实例验证；普通60秒 session 可能限制本人操作和后续长任务，不能擅自延长旧授权。localhost installed 生命周期入口、root/file route、实际 file Tool/预算与固定 Model 尚需接线。

另一个实际阻塞已定位：ConfigurationService._check 当前拒绝所有 enabled feature_flags，包括 local_files。默认保持关闭；后续要通过正式配置与当前来源门槛实现有限开放，不能直接写SQL flag绕过校验。本阶段不称完整文件/产品/新全量通过；学术原失败成果仍保留，不重新调用模型抹掉失败。
