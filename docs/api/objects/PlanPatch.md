# PlanPatch

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

替换受影响节点并传播失效。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `base_revision` | [Revision](./Revision.md) | 是 | 目标图版本 | 类型约束见对应对象 |
| `upsert_nodes` | 数组&lt;[NodeSpec](./NodeSpec.md)&gt; | 是 | 新增或替换节点 | 最少项 `0`；最多项 `256` |
| `remove_node_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 移除节点 | 最少项 `0`；最多项 `256` |
| `reason` | [NonEmptyText](./NonEmptyText.md) | 是 | 变更理由 | 类型约束见对应对象 |
| `source_input_ref` | [UserInputRef](./UserInputRef.md) | 否 | 用户修订依据 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 已发生的外部动作不能随计划删除而抹除；运行节点先取消/对账再迁移。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "base_revision": 0,
  "upsert_nodes": [],
  "remove_node_ids": [],
  "reason": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.PlanPatch`。
