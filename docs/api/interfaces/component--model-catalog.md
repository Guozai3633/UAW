# model.catalog

状态：契约0.1，待实现。类别：细分组件私有接口。所属：模型调用。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalModelCatalogRequest, context: TrustedExecutionContext) -> ComponentModelCatalogResult`。所属入口为 `model.catalog`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalModelCatalogRequest](../objects/InternalModelCatalogRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalModelCatalogRequestList](../objects/InternalModelCatalogRequestList.md)
- [InternalModelCatalogRequestResolve](../objects/InternalModelCatalogRequestResolve.md)

## 输出

[ComponentModelCatalogResult](../objects/ComponentModelCatalogResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalModelCatalogOutput](../objects/InternalModelCatalogOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 平台配置是目录来源，Model保存解析与调用实际目录revision。
- 读取管理员启用模型元数据
- 按用户可见域、提供方状态与能力筛选
- 精确名称和已登记别名解析到canonical ID，模糊相似名称仅候选
- 返回实际版本/可用状态与限制
- 调用时仍重查下线/撤销
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 精确缺失返回model_not_found
- 别名多解返回ambiguous
- 故障目录返回unavailable不猜模型

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "list",
  "parameters": {}
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "list",
    "result": {
      "items": [],
      "snapshot_revision": 0
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
| `model.catalog` | [开发设计](../../../docs/design/components/model-catalog.md) | `src/uaw/model/catalog.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
