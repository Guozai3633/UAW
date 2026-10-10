# web.session.get

状态：本机浏览器身份已实现；后台执行与真实页面整链另验收。类别：用户与管理端 HTTP API。所属：运行与会话。

读取当前浏览器用户会话。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`GET /v1/web/session`；认证：`user`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[WebSessionGetRequest](../objects/WebSessionGetRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |

## 输出

[HttpWebSessionGetResult](../objects/HttpWebSessionGetResult.md) 为完整返回结构。`kind=ok` 的payload是 [WebSession](../objects/WebSession.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `principal` | [Principal](../objects/Principal.md) | 是 | 服务器签发的用户和Web session |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 是 | 固定会话截止 |
| `csrf_token` | [Hash](../objects/Hash.md) | 是 | 内存保留，修改请求X-UAW-CSRF |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "principal": {
      "id": "example_001",
      "kind": "user",
      "auth_session_id": "example_001"
    },
    "expires_at": "2026-10-07T02:00:00Z",
    "csrf_token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "output_refs": []
}
```

## 拒绝结构示例

```json
{
  "kind": "denied",
  "output_refs": [],
  "failure": {
    "code": "permission_denied",
    "category": "authorization",
    "message": "当前主体没有本动作所需权限。",
    "retryable": false,
    "failed_phase": "policy_gate",
    "recover_hint": "取得真实授权后重新检查；不能通过换工具绕过。"
  }
}
```

## 模块与目录

| 节点 | 详细策略 | 计划代码位置 |
| --- | --- | --- |
| `ui` | [开发设计](../../../docs/design/components/ui.md) | `apps/web/src/features/workspace/` |
| `ingress` | [开发设计](../../../docs/design/components/ingress.md) | `src/uaw/api/ingress.py` |
| `run.history` | [开发设计](../../../docs/design/components/run-history.md) | `src/uaw/run/history.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
