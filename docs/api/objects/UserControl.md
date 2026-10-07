# UserControl

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

补充、排队、替换、取消、先交现有成果语义明确。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `mode` | [ControlMode](./ControlMode.md) | 是 | 干预方式 | 类型约束见对应对象 |
| `input_ref` | [Ref](./Ref.md) | 否 | 新要求；steer/enqueue/replace必需 | 类型约束见对应对象 |
| `preserve_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 明确保留的成果 | 最少项 `0`；最多项 `256` |
| `reason` | [Text](./Text.md) | 是 | 解释 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "mode": {
            "enum": [
              "steer",
              "enqueue",
              "replace"
            ]
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "required": [
          "input_ref"
        ]
      }
    }
  ]
}
```

## 运行时约束

- 正在执行的调用在安全边界收到修订；不可撤销外部动作对账后如实展示。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "mode": "steer",
  "preserve_refs": [],
  "reason": "example_001",
  "input_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.UserControl`。
