# StoragePolicy

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

云端权威或本地权威部署选项仍待用户确认。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `mode` | [StorageMode](./StorageMode.md) | 是 | 云权威/本地权威 | 类型约束见对应对象 |
| `local_cache_enabled` | [Bool](./Bool.md) | 是 | 缓存仅加速，不产生第二权威 | 类型约束见对应对象 |
| `retention_ms` | [Duration](./Duration.md) | 否 | 历史保留 | 类型约束见对应对象 |
| `encrypted` | [Bool](./Bool.md) | 是 | 落盘加密要求 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 政策版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "mode": "cloud_authoritative",
  "local_cache_enabled": true,
  "encrypted": true,
  "revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.StoragePolicy`。
