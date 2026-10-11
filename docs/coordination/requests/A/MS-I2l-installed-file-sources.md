# MS-I2l A8：A 内部文件来源契约

共同开工标签仍为 ms-i2l-start；本阶段源码与证据固定版本见 DISPATCH。A 继续本包，B/C/D 不需要同步浮动 integration 或重做已交付组件。

## 入口与责任

实现位置：`src/uaw/infrastructure/installed_files.py`；原实例查询：`src/uaw/infrastructure/installed_lifecycle.py`。

| 入口 | 输入 | 输出 / 约束 |
| --- | --- | --- |
| `owned_ready(owner, workspace)` | 可信完整 Principal、精确 workspace Ref | 当前 PreparedEnrollmentLaunch；原会话、当前活跃实例、ready、原根版本/期限，不接受路径或 approved |
| `InstalledFileRoute.current(workspace, ctx)` | 已准入上下文和其中的 workspace | `FileDeviceRoute`；实际设备当前 revision/hash；等待后复查原根和设备；缺源拒绝 |
| `RegisteredFileDataAccess.check(call, spec, ctx, provider=...)` | 原登记调用与原完整 context、内部 provider Principal | None 仅表示当前结果数据权限有效；原 ledger/action/attempt、角色、固定模型、配置和 provider 均必须相符，不代表执行许可 |
| `OriginalFileApprovalGate.check(request, ctx)` | 原 Runner request、原 Tool context | None 仅表示原审批现在有效；context/动作/参数必须逐项相符，缺适配器与 pending/declined 不允许 |
| `assemble_installed_file(container, owner=..., workspace=..., registry=..., tool_ref=..., provider=..., money_ceiling=...)` | 管理端受控注册规格与原会话/工作区；内部 service Principal；真实费用预留上界 | `InstalledFileBindings(control, bridge, tool, route)`；不发布 provider、不修改配置/角色、不开 flags、不发送命令 |

原 session/registry、OS credential handle、原 local state、原 grants/native journal 只能来自 `owned_ready` 的实例。`FileToolBindings.materials` 沿 C 已交付接口消费原内容，后续由 A 登记原 origin；不得把模型提供的正文或 Ref 当真实读取来源。此模块未新增公网接口、公开 DTO 或变更 C/D 协议。

## 消费示例

```python
sources = await assemble_installed_file(
    container, owner=authenticated_browser_owner,
    workspace=admitted_workspace, registry=trusted_registry,
    tool_ref=registered_file_tool, provider=internal_file_service,
    money_ceiling=administrator_file_cost_ceiling,
)
# sources.tool.facade 仍需要真实准入/角色/原审批/预算才能调用。
# sources.tool.materials 仅用于原结果的当前权限复查和材料消费。
# 原 lifecycle.stop/退出仍负责关闭自身 helper/session/keys。
```

## flags 与支持范围

ToolSpec 的 `file_access` 由管理员 `local_files` 唯一治理，固定与当前配置同时允许才有效。声明工具已实现并不启用开关或授予 workspace.process/file.read。当前管理员仍禁止 enabled publication，默认不可用。

当前原 Runner whole text 上限 16,384 字符 / 65,536 UTF-8 字节；不支持此桥接的分页、cursor、project admission 或写入/安装/exec。unknown 只对账原 command/journal，不重新发送。根撤销/期限、退出、新会话、取消和原版本变化仍按各 owning domain 复查；不能换实例自动重试旧动作。

## 验收边界

真实 SQL 原批准/拒绝和撤销已分项验证；完整 OS/IPC 来源装配采用测试临时目录的受控 native 输入。当前无用户文件正文读取、新模型调用或新的真人页面接受。生产混合工具/审批路由、实际文件到 Context/成果及 M4 后续由 A 完成；本阶段不是整轮 accepted，也不是新全量。
