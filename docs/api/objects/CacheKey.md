# CacheKey

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

稳定前缀与结果缓存是两种缓存，不可混为一谈。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `namespace` | [ID](./ID.md) | 是 | 隔离命名空间 | 类型约束见对应对象 |
| `scope` | [Scope](./Scope.md) | 是 | 主体范围 | 类型约束见对应对象 |
| `dependency_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 所有会影响结果的版本 | 最少项 `0`；最多项 `256` |
| `parameters_hash` | [Hash](./Hash.md) | 是 | 规范参数 | 类型约束见对应对象 |
| `policy_ref` | [Ref](./Ref.md) | 是 | 策略版本 | 类型约束见对应对象 |
| `freshness` | [FreshnessPolicy](./FreshnessPolicy.md) | 是 | 时效要求 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "namespace": "example_001",
  "scope": {
    "principal_id": "example_001"
  },
  "dependency_refs": [],
  "parameters_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "freshness": "pinned"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CacheKey`。
