# tool.mcp

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolMcpRequest, context: TrustedExecutionContext) -> ComponentToolMcpResult`。所属入口为 `tool.mcp`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolMcpRequest](../objects/InternalToolMcpRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalToolMcpRequestConnect](../objects/InternalToolMcpRequestConnect.md)
- [InternalToolMcpRequestDiscover](../objects/InternalToolMcpRequestDiscover.md)
- [InternalToolMcpRequestCall](../objects/InternalToolMcpRequestCall.md)
- [InternalToolMcpRequestClose](../objects/InternalToolMcpRequestClose.md)

## 输出

[ComponentToolMcpResult](../objects/ComponentToolMcpResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalToolMcpOutput](../objects/InternalToolMcpOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Tool持有协议Session，控制层持有账号授权；连接状态不能充当动作批准。
- 读取有效账号/提供方引用，不加载凭据进模型
- 建立协议会话并发现能力
- 工具名放provider命名空间，能力schema与版本入Registry
- 远端调用通过统一Tool闸门与结果规范化
- 健康变化有限重连并更新能力revision
- 撤销关闭会话和失效绑定，未知写不重放
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 协商不支持返回protocol_mismatch
- 掉线写结果可能unknown
- 能力变更让旧绑定stale

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "connect",
  "parameters": {
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "connection_revision": 0,
    "transport_config_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "deadline": "2026-10-07T02:00:00Z"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "connect",
    "result": {
      "id": "example_001",
      "provider_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "state": "disconnected",
      "capability_revision": 0
    }
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
| `tool.mcp` | [开发设计](../../../docs/design/components/tool-mcp.md) | `src/uaw/tool/mcp/facade.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
