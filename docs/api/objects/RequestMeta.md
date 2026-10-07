# RequestMeta

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

所有服务端操作的关联与幂等元数据。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `request_id` | [ID](./ID.md) | 是 | 同逻辑请求重试不变 | 类型约束见对应对象 |
| `schema_version` | [Version](./Version.md) | 是 | 契约版本 | 类型约束见对应对象 |
| `expected_revision` | 至少一个分支 | 否 | 修改时的CAS版本，创建可为0 | — |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "request_id": "example_001",
  "schema_version": "0.1"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RequestMeta`。
