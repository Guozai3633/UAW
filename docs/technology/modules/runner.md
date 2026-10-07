# 本地Runner：设备、文件与进程 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [uv](https://docs.astral.sh/uv/) | `uv` | Python依赖、锁文件和项目环境 | 稳定版，冻结具体版本 / 基础 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |
| [SQLite](https://docs.python.org/3/library/sqlite3.html) | `Python sqlite3` | Runner本机命令/回执账本 | 随CPython；本机文件系统 / P1 |
| [websockets](https://websockets.readthedocs.io/en/stable/) | `websockets` | Runner向后端发起WSS长连接 | 稳定版asyncio API / P1/P5 |
| [cryptography/Ed25519](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) | `cryptography` | Runner信封/回执签名 | 稳定版，明确签名profile / P1 |
| [RFC8785规范JSON](https://github.com/trailofbits/rfc8785.py) | `rfc8785` | 双方一致的签名/摘要字节 | 稳定版/JCS约束 / P1 |
| [OS凭据库](https://keyring.readthedocs.io/en/latest/) | `keyring` | 设备私钥及本机秘密存取 | 稳定版/批准OS backend / P1 |
| [psutil](https://psutil.readthedocs.io/en/latest/) | `psutil` | 真实进程与资源观测 | 稳定版/平台wheel验证 / P1 |
| [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) | `pywin32` | Windows进程组及退出清理 | 稳定版；仅Windows / P1 |
| [PySide6](https://doc.qt.io/qtforpython-6/) | `PySide6` | Runner可信本机目录选择/托盘 | Qt 6稳定组合 / P1 |
| [Git CLI](https://git-scm.com/docs/git-worktree) | `系统Git` | worktree、差异、三方合并 | 探测实际版本并记录 / P3 |
| [Docker/Compose](https://docs.docker.com/engine/security/) | `系统Docker Engine和Compose插件` | 开发服务编排；可选受控Linux执行模板 | 稳定版/镜像digest固定 / P0部署，任务执行按D03/D09 |
| [PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html) | `pyinstaller` | Runner按目标OS构建安装包 | 稳定版/实际OS构建验证 / P5 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 本机程序形态

Python执行服务＋PySide6小型托盘/目录选择helper，不要求先构建完整桌面聊天壳。Qt主线程管用户交互，执行服务用独立asyncio进程；通过受认证本机IPC传可信选择结果，UI进程不得成为任意路径执行器。

服务主动建立WSS连接，不默认开放匿名localhost执行HTTP端口。SQLite本机账本保存command受理/真实attempt/进程身份/输出cursor/回执及根handle映射；不会把它用作服务端聊天历史的第二个主库。

### 配对、签名和秘密

设备密钥由cryptography Ed25519生成，keyring必须选可验证的OS凭据backend，无可用安全backend时阻断配对而不退为明文。服务签发命令和设备签发回执分别验证。

签名profile主选RFC8785 JCS字节、SHA-256内容摘要、Ed25519签名，命令/回执加不同域标记并覆盖设备/主体/版本/期限/栅栏。rfc8785严格拒绝不支持的数字和类型；超安全整数/非有限数的字段约束在实施轮补进契约，禁止双方各自四舍五入。

RootSelection只由真实本机交互签发，服务和设备绑定revision分别核验。文件访问用解析后的根及文件Handle防链接/竞态越界；路径resolve字符串检查不提供任意进程的OS隔离。

### 真实进程和停止

asyncio subprocess argv路径启动，获准shell命令显式选择对应执行模式。Windows用Job Objects/pywin32管理进程组，psutil观测CPU/内存/退出和进程身份；PID必须结合启动时间，避免重启后误认重用PID。

Linux执行模板用进程组/容器退出回执；任务代码与Runner账本/设备秘密隔离。没有OS沙箱时native模式明确展示范围，Job Objects不是文件/网络沙箱。断线不等于进程停止；重连查原command，不重复启动unknown动作。

### 发布与回收

PyInstaller按Windows/Linux/macOS分别构建和签发包；不把一次Windows构建称为支持所有平台。初期Windows优先，Linux执行模板验证，macOS再做平台验收。升级保留设备身份/账本兼容，任务目录清理先处理后台进程并保留成果。

## 3. 架构子节点的具体技术落点

这是架构边界之外的配套实现分组，按上面的组件分工与相关轮次接入；不创建第八个Runtime或新的任务状态所有者。

## 4. 目录与依赖位置

- `apps/local_runner/uaw_runner/`
- `apps/local_runner/uaw_runner/ui/`
- `apps/local_runner/uaw_runner/platforms/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P1-04 Runner配对与项目授权](../../plan/rounds/P1-04.md) | 让本机项目访问来自真实用户选择和设备授权。 | planned |
| [P1-05 输入快照、隔离、环境和真实进程](../../plan/rounds/P1-05.md) | 运行真实项目检查并保留用户已有修改。 | planned |
| [P3-05 并行写隔离与三方合并](../../plan/rounds/P3-05.md) | 把子工作区修改安全纳入用户项目。 | planned |
| [P4-07 多语言环境、进程回收与可选云后端](../../plan/rounds/P4-07.md) | 增加真实环境能力并保持安装和执行范围受控。 | planned |
| [P5-02 租约、当前权限与安全续跑](../../plan/rounds/P5-02.md) | 恢复未完工作而不重复未知外部写。 | planned |
| [P5-05 单用户工作区受控试用准备](../../plan/rounds/P5-05.md) | 把可用能力交给真实用户，保留账号和设备边界。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

