# InternalAgentCompletionEvidenceRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

真实证据收集的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `contract_ref` | [Ref](./Ref.md) | 是 | 当前目标和验收要求的固定版本。 | 类型约束见对应对象 |
| `artifact_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际存在、获准且固定版本的成果；不接受虚构路径。 | 最多项 `256` |
| `coverage_gaps` | 数组&lt;[ID](./ID.md)&gt; | 是 | 缺乏证据的验收要求ID，用于申请实际检查。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 验证证据是不可变引用，不以模型口述替代。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "contract_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "artifact_refs": [],
  "coverage_gaps": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCompletionEvidenceRequest`。
