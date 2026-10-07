# IntentSemanticRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

已核对逐字来源的模型提案；不证明摘要语义质量已验收。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 输入集合版本 | 类型约束见对应对象 |
| `source_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 读取的完整用户输入 | 最少项 `0`；最多项 `256` |
| `proposal` | [IntentProposal](./IntentProposal.md) | 是 | 候选 | 类型约束见对应对象 |
| `model_output_ref` | [Ref](./Ref.md) | 是 | 真实ModelRuntime回执 | 类型约束见对应对象 |
| `context_snapshot_ref` | [Ref](./Ref.md) | 是 | 固定模型输入 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "input_revision": 0,
  "source_refs": [],
  "proposal": {
    "summary": "example_001",
    "requirements": [],
    "outputs": [],
    "assumptions": [],
    "unresolved": []
  },
  "model_output_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "context_snapshot_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.IntentSemanticRecord`。
