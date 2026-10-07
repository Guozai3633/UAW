# WaitTargets

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

等待最多8个。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

数组&lt;[Ref](./Ref.md)&gt;。最少项 `1`；最多项 `8`；去重 `True`

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
[
  {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
]
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.WaitTargets`。
