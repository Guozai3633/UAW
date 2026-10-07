# ValidationReport

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

结构/政策校验结果，不自动执行被校验对象。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `valid` | [Bool](./Bool.md) | 是 | 是否通过 | 类型约束见对应对象 |
| `normalized_ref` | [Ref](./Ref.md) | 否 | 规范化对象 | 类型约束见对应对象 |
| `violations` | 数组&lt;[ValidationIssue](./ValidationIssue.md)&gt; | 是 | 问题 | 最少项 `0`；最多项 `256` |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 依据 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "valid": true,
  "violations": [],
  "evidence_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ValidationReport`。
