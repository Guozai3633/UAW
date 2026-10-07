# support.stores

状态：契约0.1，待实现。类别：细分组件私有接口。所属：配置与共享基础设施。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalSupportStoresRequest, context: TrustedExecutionContext) -> ComponentSupportStoresResult`。所属入口为 `support.stores`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalSupportStoresRequest](../objects/InternalSupportStoresRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalSupportStoresRequestGet](../objects/InternalSupportStoresRequestGet.md)
- [InternalSupportStoresRequestPut](../objects/InternalSupportStoresRequestPut.md)
- [InternalSupportStoresRequestDelete](../objects/InternalSupportStoresRequestDelete.md)

## 输出

[ComponentSupportStoresResult](../objects/ComponentSupportStoresResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalSupportStoresOutput](../objects/InternalSupportStoresOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 物理数据库可共用，逻辑写入所有权不同；可重建派生与权威数据采用不同保留规则。
- 每领域通过自己的Repository接口读写
- 共享设施提供事务/CAS、对象引用、索引发布与缓存能力适配
- 资源读写检查归属和保留政策
- 备份恢复重放删除/撤销记录
- 迁移版本显式校验，不让万能JSON状态表承担所有领域规则
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 版本冲突类型化
- 部分对象上传保留pending并清理未引用块
- 迁移失败不宣布ready

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "get",
  "parameters": {
    "repository_kind": "history",
    "key": "example_001"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "get",
    "result": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
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
| `support.stores` | [开发设计](../../../docs/design/components/support-stores.md) | `src/uaw/shared/stores.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
