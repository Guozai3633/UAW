# CacheComputeRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

只合并相同依赖的可信纯计算；各等待者取消独立。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `key` | [CacheKey](./CacheKey.md) | 是 | 缓存键 | 类型约束见对应对象 |
| `computation_ref` | [Ref](./Ref.md) | 是 | 服务预注册的只读/纯计算句柄 | 类型约束见对应对象 |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 截止 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "key": {
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
  },
  "computation_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "deadline": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CacheComputeRequest`。
