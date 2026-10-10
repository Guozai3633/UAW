# web.session.logout

状态：本机浏览器身份已实现；后台执行与真实页面整链另验收。类别：用户与管理端 HTTP API。所属：运行与会话。

撤销当前浏览器会话并清cookie。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`DELETE /v1/web/session`；认证：`user`。

正文使用{meta,payload}；精确Origin、HttpOnly cookie和X-UAW-CSRF。无If-Match查询参数。

## 输入

[WebSessionLogoutRequest](../objects/WebSessionLogoutRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |

## 输出

[HttpWebSessionLogoutResult](../objects/HttpWebSessionLogoutResult.md) 为完整返回结构。`kind=ok` 的payload是 [Acknowledgement](../objects/Acknowledgement.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `operation_id` | [ID](../objects/ID.md) | 是 | 受理ID |
| `status` | enum: `accepted` / `unchanged` / `completed` / `pending` | 是 | 确认状态 |
| `related_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 否 | 相关资源 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- {meta,payload}正文；精确Origin/HttpOnly cookie/X-UAW-CSRF；无If-Match参数。

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
    "operation_id": "example_001",
    "status": "accepted"
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
