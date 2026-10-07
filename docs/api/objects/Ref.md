# Ref

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

跨域资源引用；资源本体/权限归所属领域。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `kind` | [RefKind](./RefKind.md) | 是 | 来源类型 | 类型约束见对应对象 |
| `id` | [ID](./ID.md) | 是 | 资源ID | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 实际来源版本 | 类型约束见对应对象 |
| `location` | [Location](./Location.md) | 否 | 可选定位 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 否 | 取得内容摘要 | 类型约束见对应对象 |
| `access_scope` | [Scope](./Scope.md) | 否 | 可见范围，由来源域确认 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 引用可解析不表示当前有权限；删除/撤销不能通过旧Ref读取。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "kind": "web",
  "id": "example_001",
  "version": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Ref`。
