# WorkspacesRevertRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

撤销指定已应用变更。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `workspace_id` | [ID](./ID.md) | 是 | 工作区 | 类型约束见对应对象 |
| `change_set_ref` | [Ref](./Ref.md) | 是 | 可逆变更集 | 类型约束见对应对象 |
| `selected_unit_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 选择改动 | 最少项 `1`；最多项 `256` |
| `expected_workspace_version` | [Version](./Version.md) | 是 | 当前基线 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 撤销创建新版本；用户后续编辑不覆盖；外部服务动作不属于文件撤销。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "workspace_id": "example_001",
  "change_set_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "selected_unit_ids": [
    "example_001"
  ],
  "expected_workspace_version": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.WorkspacesRevertRequest`。
