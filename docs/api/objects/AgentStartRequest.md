# AgentStartRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

创建根执行实例。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_ref` | [Ref](./Ref.md) | 是 | 当前运行 | 类型约束见对应对象 |
| `task_frame_ref` | [Ref](./Ref.md) | 是 | 理解 | 类型约束见对应对象 |
| `creation_key` | [ID](./ID.md) | 是 | 去重键 | 类型约束见对应对象 |
| `role_profile_ref` | [Ref](./Ref.md) | 否 | 默认角色 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "task_frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "creation_key": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentStartRequest`。
