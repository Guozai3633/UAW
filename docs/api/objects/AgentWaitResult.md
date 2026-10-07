# AgentWaitResult

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

等待不是轮询造成功；超时返回仍在运行。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `instances` | 数组&lt;[AgentInstance](./AgentInstance.md)&gt; | 是 | 最新状态 | 最少项 `0`；最多项 `256` |
| `results` | 数组&lt;[AgentResult](./AgentResult.md)&gt; | 是 | 已完成结果 | 最少项 `0`；最多项 `256` |
| `next_cursor` | [Cursor](./Cursor.md) | 否 | 增量游标 | 类型约束见对应对象 |
| `timed_out` | [Bool](./Bool.md) | 是 | 本次等待到期 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "instances": [],
  "results": [],
  "timed_out": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentWaitResult`。
