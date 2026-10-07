# InternalToolDiscoveryRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

工具发现与筛选的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `query` | [Text](./Text.md) | 是 | 按当前语义任务生成的检索查询，不使用行业词典固定路由。 | 类型约束见对应对象 |
| `role_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 角色允许的类别，发现时与有效权限求交。 | 最多项 `256` |
| `allowed_scope` | [Scope](./Scope.md) | 是 | 有效权限交集内的允许范围，不能由发现结果扩大。 | 类型约束见对应对象 |
| `max_candidates` | integer | 是 | 一次最多提供候选数，减少模型输入而不授予权限。 | ≥ `1`；≤ `64` |
| `registry_revision` | [Revision](./Revision.md) | 是 | 本次发现消费的工具目录修订。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 记录候选与选中理由；目录命中不产生授权记录。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "query": "example_001",
  "role_capabilities": [],
  "allowed_scope": {
    "principal_id": "example_001"
  },
  "max_candidates": 1,
  "registry_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolDiscoveryRequest`。
