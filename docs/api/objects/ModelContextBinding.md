# ModelContextBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

私有输入快照与Run/会话的归属绑定；不从Ref推断权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `snapshot_ref` | [Ref](./Ref.md) | 是 | 固定快照 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 是 | 会话 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "snapshot_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "run_id": "example_001",
  "conversation_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelContextBinding`。
