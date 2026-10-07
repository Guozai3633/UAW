# InternalAgentCompletionSemanticRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

语义核对的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `contract_ref` | [Ref](./Ref.md) | 是 | 当前目标和验收要求的固定版本。 | 类型约束见对应对象 |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际取得、可读取且与本次要求有关的证据。 | 最多项 `256` |
| `artifact_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际存在、获准且固定版本的成果；不接受虚构路径。 | 最多项 `256` |
| `reviewer_policy` | [Ref](./Ref.md) | 是 | 语义评审方法、模型继承和预算，不替代真实检查。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- VerificationReport记录判别方法版本与限制，不直接结束Run。
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
  "evidence_refs": [],
  "artifact_refs": [],
  "reviewer_policy": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCompletionSemanticRequest`。
