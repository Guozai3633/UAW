# InternalContextMemoryCandidateRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

记忆候选的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `source_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际来源集合，须固定版本、访问权和可定位内容。 | 最多项 `256` |
| `candidate_kind` | enum: `explicit` / `inferred` | 是 | explicit来源于用户明确要求；inferred先候选后核验。 | — |
| `content` | [MemoryContent](./MemoryContent.md) | 是 | 有来源且受当前记忆政策约束的内容。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 候选未通过之前不进入正式长期召回。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "source_refs": [],
  "candidate_kind": "explicit",
  "content": {
    "text": "example_001",
    "kind": "preference",
    "source_refs": []
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalContextMemoryCandidateRequest`。
