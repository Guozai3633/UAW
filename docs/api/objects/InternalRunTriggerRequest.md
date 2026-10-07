# InternalRunTriggerRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

未来触发器的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `trigger_spec_ref` | [Ref](./Ref.md) | 是 | 获准触发规则、目标、范围和重叠策略版本。 | 类型约束见对应对象 |
| `occurrence_key` | [Text](./Text.md) | 是 | 定时/事件这一次触发的稳定去重键。 | 类型约束见对应对象 |
| `target_task_ref` | [Ref](./Ref.md) | 是 | 定时触发所绑定任务版本。 | 类型约束见对应对象 |
| `overlap_policy` | enum: `queue` / `skip` / `parallel` | 是 | 已有运行未结束时排队、跳过或获准并行。 | — |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 每次触发与授权版本留记录，节点Scheduler不负责决定定时唤醒。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "trigger_spec_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "occurrence_key": "example_001",
  "target_task_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "overlap_policy": "queue"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalRunTriggerRequest`。
