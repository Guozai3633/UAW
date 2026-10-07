# ToolToolsDiscoverInput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

按语义寻找当前可用工具和角色。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `query` | [NonEmptyText](./NonEmptyText.md) | 是 | 任务相关搜索 | 类型约束见对应对象 |
| `categories` | 数组&lt;[ID](./ID.md)&gt; | 否 | 收窄类别 | 最少项 `0`；最多项 `256` |
| `max_candidates` | [CandidateLimit](./CandidateLimit.md) | 是 | 最多候选 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 角色类别、产品旗标和权限先过滤，混合召回后交当前LLM选；小目录可直接返回。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "query": "example_001",
  "max_candidates": 1
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolToolsDiscoverInput`。
