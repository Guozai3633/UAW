# DeliveryContract

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

命名兼容别名，结构以 Contract 为准。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

[Contract](./Contract.md)。类型约束见对应对象

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "goal": "example_001",
  "requirements": [],
  "outputs": [],
  "version": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DeliveryContract`。
