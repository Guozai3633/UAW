# RunsDeliveryAcceptRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

实际用户决定整份合同交付；不直接设置completed。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `bundle_ref` | [Ref](./Ref.md) | 是 | 精确Bundle | 类型约束见对应对象 |
| `artifact_ref` | [Ref](./Ref.md) | 是 | 精确成果 | 类型约束见对应对象 |
| `decision` | enum: `accept` / `reject` | 是 | 现有DeliveryDecision的整份接受/拒绝子集。 | — |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 当前认证身份必须与原执行用户会话一致；只接受要求用户接受的合同；版本/取消复核。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "bundle_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "artifact_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "decision": "accept"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunsDeliveryAcceptRequest`。
