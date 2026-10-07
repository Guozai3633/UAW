# InternalContextRetrievalRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

资料检索与证据的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `query` | [Text](./Text.md) | 是 | 按当前语义任务生成的检索查询，不使用行业词典固定路由。 | 类型约束见对应对象 |
| `corpus_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 授权并发布的检索语料；删除资料不可用旧缓存召回。 | 最多项 `256` |
| `active_revisions` | 映射&lt;string, [Revision](./Revision.md)&gt; | 是 | 每个语料当前已发布的索引修订；旧未发布索引不得混入。 | 最多键 `256`；值逐项按schema校验 |
| `top_k` | integer | 是 | 检索最多命中数，1–64；过滤访问权后再排序。 | ≥ `1`；≤ `64` |
| `freshness` | [FreshnessPolicy](./FreshnessPolicy.md) | 是 | 固定版本、最新必需或政策限定时效。 | 类型约束见对应对象 |
| `max_age_ms` | [Duration](./Duration.md) | 否 | bounded_age必需；0表示不接受陈旧数据。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "freshness": {
            "const": "bounded_age"
          }
        },
        "required": [
          "freshness"
        ]
      },
      "then": {
        "required": [
          "max_age_ms"
        ]
      }
    }
  ]
}
```

## 运行时约束

- 保存RetrievalManifest与实际索引版本；不能把高相似排名写成已验证事实。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "query": "example_001",
  "corpus_refs": [],
  "active_revisions": {},
  "top_k": 1,
  "freshness": "pinned"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalContextRetrievalRequest`。
