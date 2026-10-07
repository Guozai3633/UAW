# CachePolicy

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

结果/前缀/在途缓存的不同策略。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 政策 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 修订 | 类型约束见对应对象 |
| `layer` | [CacheLayer](./CacheLayer.md) | 是 | 缓存层 | 类型约束见对应对象 |
| `ttl_ms` | [Duration](./Duration.md) | 是 | 生命周期 | 类型约束见对应对象 |
| `max_age_ms` | [Duration](./Duration.md) | 是 | 可接受陈旧程度 | 类型约束见对应对象 |
| `max_entry_bytes` | [Count](./Count.md) | 是 | 单条最大值 | 类型约束见对应对象 |
| `negative_ttl_ms` | [Duration](./Duration.md) | 是 | 明确不存在/短期失败缓存 | 类型约束见对应对象 |
| `allowed_effects` | 数组&lt;[EffectKind](./EffectKind.md)&gt; | 是 | 可缓存效果 | 最少项 `0`；最多项 `256` |
| `shared_across_principals` | [Bool](./Bool.md) | 是 | 是否明确公共资源 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 敏感/私有内容不跨主体；结果缓存不接受写/审批/当前进程状态；前缀命中以provider usage为准。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "layer": "model_prefix",
  "ttl_ms": 0,
  "max_age_ms": 0,
  "max_entry_bytes": 0,
  "negative_ttl_ms": 0,
  "allowed_effects": [],
  "shared_across_principals": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CachePolicy`。
