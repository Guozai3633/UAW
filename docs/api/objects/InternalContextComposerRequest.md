# InternalContextComposerRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

装配与快照的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `instruction_set_ref` | [Ref](./Ref.md) | 是 | 按来源优先级和作用域解决的指令集合。 | 类型约束见对应对象 |
| `selected_block_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 经过预算分配、来源/权限核对的上下文块。 | 最多项 `256` |
| `capability_snapshot` | [Ref](./Ref.md) | 是 | 当前有效能力及旗标版本，用于缩小候选。 | 类型约束见对应对象 |
| `context_epoch` | [Revision](./Revision.md) | 是 | 上下文纪元，旧快照不能向新纪元追加。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 快照内容不可变；装配源引用保留以便诊断，删除/撤销可使其不可再读取。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "instruction_set_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "selected_block_refs": [],
  "capability_snapshot": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "context_epoch": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalContextComposerRequest`。
