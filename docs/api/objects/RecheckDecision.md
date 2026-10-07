# RecheckDecision

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

审批后再次核对参数/资源/权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `allowed` | [Bool](./Bool.md) | 是 | 是否仍允许 | 类型约束见对应对象 |
| `validated_call_ref` | [Ref](./Ref.md) | 是 | 调用 | 类型约束见对应对象 |
| `resource_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 最新匹配资源 | 最少项 `0`；最多项 `256` |
| `approval_ref` | [Ref](./Ref.md) | 否 | 授权 | 类型约束见对应对象 |
| `reason` | [NonEmptyText](./NonEmptyText.md) | 是 | 依据 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "allowed": true,
  "validated_call_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "resource_refs": [],
  "reason": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RecheckDecision`。
