# TaskTemplate

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

可复用任务模板允许锁定稳定部分。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 模板 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 版本 | 类型约束见对应对象 |
| `contract` | [Contract](./Contract.md) | 是 | 目标和验收 | 类型约束见对应对象 |
| `source_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 材料入口 | 最少项 `0`；最多项 `256` |
| `plan_ref` | [Ref](./Ref.md) | 否 | 可选固定步骤 | 类型约束见对应对象 |
| `skill_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 方法 | 最少项 `0`；最多项 `256` |
| `locked_fields` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 禁止自动修改的字段路径 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "contract": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
  },
  "source_refs": [],
  "skill_refs": [],
  "locked_fields": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.TaskTemplate`。
