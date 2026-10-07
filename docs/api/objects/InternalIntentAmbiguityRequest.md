# InternalIntentAmbiguityRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

歧义处理的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `interpretations` | 数组&lt;[Interpretation](./Interpretation.md)&gt; | 是 | 有用户原文来源的理解候选，不是虚构新目标。 | 最多项 `256` |
| `impact` | [Impact](./Impact.md) | 是 | 理解错误可能产生的影响，用于决定澄清或可逆探查。 | 类型约束见对应对象 |
| `reversible` | [Bool](./Bool.md) | 是 | 错误动作是否有已知可逆策略；不能等同无风险。 | 类型约束见对应对象 |
| `unresolved` | 数组&lt;[Text](./Text.md)&gt; | 是 | 当前还没有答案的关键问题，不自动当成已解决。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 澄清进入Run InteractionItem，用户回答是新输入；假设保持显式版本。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "interpretations": [],
  "impact": "low",
  "reversible": true,
  "unresolved": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalIntentAmbiguityRequest`。
