# MS-I2l：网页本机生命周期 v1

2026-10-11，A7 兼容新增接口。准确阶段源码与标签以 DISPATCH 发布为准；不移动 ms-i2l-start，不发新包。

## 入口与部署

| 操作 | 请求 | 返回 |
| --- | --- | --- |
| `POST /v1/runner/local` | `{meta:{request_id,schema_version},payload:{}}` | 202，`HttpRunnerLocalBeginResult`，payload 为 `InstalledLaunchView` |
| `GET /v1/runner/local/{launch_id}` | 原启动 id；无查询参数 | 200，`HttpRunnerLocalGetResult` |
| `POST /v1/runner/local/{launch_id}/stop` | `{meta:{request_id,schema_version,expected_revision?},payload:{}}` | 200，`HttpRunnerLocalStopResult` |

原精确 Origin、HttpOnly cookie、CSRF 规则不变；CLI bearer 不能启动 native。无部署来源明确 503。启动 payload 不收 owner、路径、approved、module、公私钥、期限、工具或模型设置。配置仅由管理员的本机安装配置给出 `installed_state_directory`（绝对内部状态目录）和 `installed_workspace_id`（逻辑工作区 ID），两项必须同时配置并有实际 Web/数据库来源。普通配置默认没有这两项；不是功能 flag。

固定已安装模块和实际 base Python、当前包/库目录构造子进程环境；不转发模型/admin/数据库环境凭据或测试 import selector。原 protected vault locator 仍独立交付每次当前配置和 OS 角色 keys。

## 状态与页面消费

`starting → waiting_device → connecting → selecting_directory → ready`；拒绝/当前来源变更/超时为 failed，用户停止为 closed，原通道期限或后端进程丢失为 unavailable。

`ready` 必须等 A 子端 native callback 最终 bootstrap 复查完成的私有进度 marker，再独立核对当前通道、原 consumed ticket、owning native journal、选择签名、只读 grant、精确 owner/workspace 和 device binding。进度文件不授权；每个 Tool、Run、预算与 RootSource 仍独立检查。

页面只消费 id/request_id/revision/state/workspace_ref/created_at/updated_at，以及可选 enrollment_id/device_ref/expires_at/failure_code。不显示 native 路径或 proof/code/key。202 是启动已登记，不是本人已批准；GET 不重新弹窗，刷新沿原 id 查询。同一原 Web session/request_id 重试只返回原历史，不创建第二个 native 实例；未知响应先查原 id。原同账号新 session 不可接管旧实例。

## 资源与恢复

一个后端仅持有一个自有实例。后台有界执行，当前用户仍有效才能开始，普通15秒/首次90秒、原角色/挑战/根120秒较早期限不变。等 callback 时缺进度不重复进行整套角色 IO；收到 marker 后必须做完整独立复查，没有权限缓存。

stop/退出 Web/服务退出取消并 drain 自有后台任务，走原 PreparedEnrollmentLaunch.close：自己的绑定/通道/helper/proof/OS keys 与随机凭据。重复 stop 不重复取消正在清理的任务；worker 尚未调度就停止也不分配 native 资源。日志与状态只保存有界错误码，保留历史。重启只读原 SQL 历史，无法找到实际内存实例时改 unavailable，不恢复旧进程、keys 或 grant。

## 本阶段范围

这是 A 的网页 installed 生命周期。尚未开放 local_files 或原 Runner 文件 action gate/provider、未接 C 文件执行到固定模型或 B 新入口按钮；这些继续在本轮 M3/M4 完成。真实本人第六次回执单独保留，不以受控 UI/组件测试替代页面本人授权。
