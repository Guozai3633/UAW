# ProcessesStopRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

停止进程树。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `process_id` | [ID](./ID.md) | 是 | 进程 | 类型约束见对应对象 |
| `reason` | [NonEmptyText](./NonEmptyText.md) | 是 | 理由 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 先软终止、超时硬终止；离线lost不伪称stopped。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "process_id": "example_001",
  "reason": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ProcessesStopRequest`。
