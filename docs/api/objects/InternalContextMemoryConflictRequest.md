# InternalContextMemoryConflictRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

查重与冲突的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `candidate_ref` | [Ref](./Ref.md) | 是 | 尚未确认的记忆/结果候选版本。 | 类型约束见对应对象 |
| `existing_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 同作用域的已有记忆版本，用于语义冲突核对。 | 最多项 `256` |
| `slot_key` | [Text](./Text.md) | 否 | 同主题互斥事实/偏好的逻辑位置。 | 类型约束见对应对象 |
| `expected_revision` | [Revision](./Revision.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 不原地抹掉来源历史，提交新的事实版本。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "candidate_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "existing_refs": [],
  "expected_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalContextMemoryConflictRequest`。
