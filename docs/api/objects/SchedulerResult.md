# SchedulerResult

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

代码调度结果，禁止LLM直接跳过依赖。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `ready_node_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 可执行 | 最少项 `0`；最多项 `256` |
| `blocked_node_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 受阻 | 最少项 `0`；最多项 `256` |
| `reserved_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际预留 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "ready_node_ids": [],
  "blocked_node_ids": [],
  "reserved_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.SchedulerResult`。
