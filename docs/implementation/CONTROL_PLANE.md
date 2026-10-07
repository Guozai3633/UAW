# 开发控制层操作说明

目前可以管理平台配置、创建会话、提交/取消任务、查看历史和账本。HTTP任务仍保存为queued，没有自动Agent执行器。模型网关已接入，可按[实连说明](MODEL_CONNECTION.md)显式运行一次诊断；实际供应商验收待配置，网页端仍是蓝图。

## 1. 启动

在项目根目录用 PowerShell：

```powershell
uv sync --frozen --extra agent-engine
./ops/start.ps1 -WithPostgres
```

脚本为 UAW 在 Windows 凭据库中准备用户/管理员令牌和独立分页密钥，启动已有开发 PostgreSQL、迁移，再监听 `127.0.0.1:8000`。不会输出令牌值。数据库密码仍保存在忽略的 `.data/dev-db.env`，最终生产后端尚未选定。

- `/health/ready`：显示Run受理与Model协议入口是否绑定；不执行供应商探测，其他五个执行Runtime尚未绑定。
- `/docs` 与 `/openapi.json`：只展示已实现的开发 HTTP 入口；API 需要 bearer 身份。带浏览器 Origin 的调用暂时拒绝，管理操作使用下方本机客户端。
- 没有活动配置时 `/v1/models` 明确返回 configuration_unavailable。不要用示例地址冒充模型连通。

## 2. 管理员操作

另开一个项目终端，建立该进程的开发数据库环境变量（连接信息不会打印）：

```powershell
./ops/start-dev-db.ps1
.venv/Scripts/python.exe ops/admin_cli.py --method GET --path /v1/admin/configuration
```

写操作格式：

```powershell
.venv/Scripts/python.exe ops/admin_cli.py --path /v1/admin/providers --payload-file .data/provider.json --request-id provider-registration-1
```

`.data/provider.json` 的字段示例如下；把地址、模型名换成已批准的配置。以下 `.invalid` 示例不能连通：

```json
{
  "provider": {
    "id": "your-provider",
    "kind": "model",
    "endpoint": "https://provider.invalid/v1",
    "profile_ref": {"kind": "provider_profile", "id": "model.http", "version": "1"},
    "settings": {"model_name": "your-model", "timeout_ms": 30000}
  }
}
```

输入第三方密钥：

```powershell
.venv/Scripts/python.exe ops/admin_cli.py --path /v1/admin/secrets --provider-id your-provider --request-id provider-secret-1
```

终端隐藏输入，只返回 credential_handle/version。登记提供方时通过 credential_handle 引用；如果提供方已经存在，更新需 `--expected-revision 1` 等匹配修订。秘密不能放入 settings、URL、命令参数或 payload 文件。

接着按顺序登记模型、manual 审批政策和开发存储政策；根据返回的引用构建 ConfigurationDraft，再执行 stage → validate → activate。所有 DTO 及约束见[接口对象字典](../api/OBJECTS.md)。关键路由：

| 操作 | 路径 | 本轮限制 |
| --- | --- | --- |
| 登记模型 | POST `/v1/admin/models` | 需已登记 model 提供方；模型上限和能力由管理员声明 |
| 登记政策 | POST `/v1/admin/policies` | manual、开发本地存储、能力政策；其他类型暂不可用 |
| 登记环境 | POST `/v1/admin/environments` | 只登记无执行动作模板，版本为下一修订号 |
| 配置草案 | POST `/v1/admin/configuration/drafts` | 引用应使用实际返回 ID/版本，模型引用 kind 为 model |
| 校验 | POST `/v1/admin/configuration/drafts/{id}/validate` | payload 为 `{}`；expected_revision 为草案当前版本 |
| 激活 | POST `/v1/admin/configuration/drafts/{id}/activate` | 先校验；expected_revision 为校验后的版本 |
| 撤销提供方 | DELETE `/v1/admin/providers/{id}` | payload 为 `{}`；需当前提供方 revision |

例如校验新草案：

```powershell
.venv/Scripts/python.exe ops/admin_cli.py --path /v1/admin/configuration/drafts/实际草案ID/validate --expected-revision 1 --request-id configuration-validate-1
```

客户端返回 request_id 和服务结果。重试保留 request_id 与原参数；修改参数需新 request_id。更新/校验/激活/撤销使用对应资源的预期 revision。配置发布不进行网络探测，不会触发任务执行。

## 3. 用户任务请求

用户令牌仅由本机可信客户端读取并放入 Authorization 头；未来网页入口使用正式会话认证。主体/权限不放在请求正文。

1. GET `/v1/models` 获取平台登记目录。
2. POST `/v1/conversations`，明确 model_choice，关闭未实现的记忆；示例结构见[创建会话](../api/interfaces/http--conversations-create.md)。
3. POST `/v1/conversations/{id}/turns`，正文为 meta + payload；payload 只含 text、attachment_refs 和可选 budget，不重复填写路径 ID。
4. GET `/v1/runs/{id}`、`/v1/conversations/{id}/items` 或 `/events` 查看实际状态；事件载荷可从 `/v1/events/{event_id}/payload` 获取。
5. POST `/v1/runs/{id}/control` 提交 cancel，带当前 expected_revision。

```json
{
  "meta": {"request_id": "user-turn-1", "schema_version": "0.1"},
  "payload": {"text": "用户的原始问题", "attachment_refs": []}
}
```

目前返回queued是正确结果。显式model_probe走独立诊断入口；P1接入任务理解和Agent循环后才会自动领取普通任务。关闭能力或没有适配器时不能手工伪造工具调用绕过限制。

## 4. 验证与回执

```powershell
./ops/check.ps1 -WithPostgres
.venv/Scripts/python.exe contracts/check_interfaces.py
```

测试使用实际PostgreSQL、Windows凭据库及loopback HTTP；注册、权限、协议和记账数字使用受控fixture。测试中的供应商/账单不是真实外部LLM。实际范围见[P0-03](P0-03.md)、[P0-04](P0-04.md)、[P0-05](P0-05.md)。
