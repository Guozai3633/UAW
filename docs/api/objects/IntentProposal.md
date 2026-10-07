# IntentProposal

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

LLM提案；summary仅提示，推断与缺口必须独立列出。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `summary` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `2000` |
| `requirements` | 数组&lt;[IntentRequirementProposal](./IntentRequirementProposal.md)&gt; | 是 | 有来源约束 | 最少项 `0`；最多项 `64` |
| `outputs` | 数组&lt;[IntentOutputProposal](./IntentOutputProposal.md)&gt; | 是 | 有来源成果 | 最少项 `0`；最多项 `16` |
| `assumptions` | 数组&lt;string&gt; | 是 | 未经确认假设 | 最少项 `0`；最多项 `32` |
| `unresolved` | 数组&lt;string&gt; | 是 | 缺口或矛盾 | 最少项 `0`；最多项 `32` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "summary": "example_001",
  "requirements": [],
  "outputs": [],
  "assumptions": [],
  "unresolved": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.IntentProposal`。
