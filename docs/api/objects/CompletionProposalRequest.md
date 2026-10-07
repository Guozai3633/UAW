# CompletionProposalRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

核对要求、成果、报告与未知效果后提出完成。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `delivery_contract_ref` | [Ref](./Ref.md) | 是 | 验收 | 类型约束见对应对象 |
| `artifact_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 成果 | 最少项 `0`；最多项 `256` |
| `verification_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 证据 | 最少项 `0`；最多项 `256` |
| `expected_revisions` | [RevisionMap](./RevisionMap.md) | 是 | 参与域修订 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "delivery_contract_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "artifact_refs": [],
  "verification_refs": [],
  "expected_revisions": {}
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CompletionProposalRequest`。
