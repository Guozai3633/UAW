# SelectionResult

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

预算分配与遗漏有据可查。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `selected_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 选取内容 | 最少项 `0`；最多项 `256` |
| `omitted_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 裁剪 | 最少项 `0`；最多项 `256` |
| `allocated_tokens` | [Count](./Count.md) | 是 | 预算 | 类型约束见对应对象 |
| `preserved_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 保护 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "selected_refs": [],
  "omitted_refs": [],
  "allocated_tokens": 0,
  "preserved_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.SelectionResult`。
