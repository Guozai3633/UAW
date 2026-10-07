# WorkspaceRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

运行工作区位置与权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 工作区 | 类型约束见对应对象 |
| `revision` | [Version](./Version.md) | 是 | 文件树版本 | 类型约束见对应对象 |
| `project_binding_ref` | [Ref](./Ref.md) | 否 | 本地绑定 | 类型约束见对应对象 |
| `base_ref` | [Ref](./Ref.md) | 是 | 基础快照 | 类型约束见对应对象 |
| `mode` | [IsolationMode](./IsolationMode.md) | 是 | 隔离方式 | 类型约束见对应对象 |
| `writer_agent_ref` | [Ref](./Ref.md) | 是 | 当前写实例 | 类型约束见对应对象 |
| `root_handle` | [ID](./ID.md) | 是 | Runner/沙箱句柄 | 类型约束见对应对象 |
| `environment_ref` | [Ref](./Ref.md) | 否 | 环境状态 | 类型约束见对应对象 |
| `state` | [WorkspaceState](./WorkspaceState.md) | 是 | 可用状态 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": "example_001",
  "base_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "mode": "isolated_copy",
  "writer_agent_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "root_handle": "example_001",
  "state": "allocating"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.WorkspaceRecord`。
