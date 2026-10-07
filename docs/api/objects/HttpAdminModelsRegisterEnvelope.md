# HttpAdminModelsRegisterEnvelope

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

HTTP请求meta和业务参数；路径/查询另由API合成。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `meta` | [RequestMeta](./RequestMeta.md) | 是 | 幂等与版本元信息 | 类型约束见对应对象 |
| `payload` | [AdminModelsRegisterRequest](./AdminModelsRegisterRequest.md) | 是 | 业务参数 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "meta": {
    "request_id": "example_001",
    "schema_version": "0.1"
  },
  "payload": {
    "entry": {
      "id": "example_001",
      "provider_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "display_name": "example_001",
      "context_limit_tokens": 1,
      "output_limit_tokens": 1,
      "capabilities": []
    }
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.HttpAdminModelsRegisterEnvelope`。
