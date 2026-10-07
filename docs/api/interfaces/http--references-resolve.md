# references.resolve

状态：契约0.1，待实现。类别：用户与管理端 HTTP API。所属：上下文与资料。

解析引用。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/references/resolve`；认证：`user`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[ReferencesResolveRequest](../objects/ReferencesResolveRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `reference` | [Ref](../objects/Ref.md) | 是 | 目标 |

## 输出

[HttpReferencesResolveResult](../objects/HttpReferencesResolveResult.md) 为完整返回结构。`kind=ok` 的payload是 [ResolvedReference](../objects/ResolvedReference.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `record` | [ReferenceRecord](../objects/ReferenceRecord.md) | 是 | 来源 |
| `citations` | 数组&lt;[Citation](../objects/Citation.md)&gt; | 是 | 主张定位 |
| `next_cursor` | [Cursor](../objects/Cursor.md) | 否 | 下一页 |

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
{
  "meta": {
    "request_id": "request_001",
    "schema_version": "0.1",
    "expected_revision": 0
  },
  "payload": {
    "reference": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "record": {
      "ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "title": "example_001",
      "content_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "retrieved_at": "2026-10-07T02:00:00Z",
      "provenance_refs": [],
      "access_scope": {
        "principal_id": "example_001"
      }
    },
    "citations": []
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
| `context.references` | [开发设计](../../../docs/design/components/context-references.md) | `src/uaw/context/references.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
