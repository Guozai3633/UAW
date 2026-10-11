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
