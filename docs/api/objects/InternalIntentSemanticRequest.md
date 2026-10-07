# InternalIntentSemanticRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

语义解析的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `input_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 授权并固定实际版本的输入集合。 | 最多项 `256` |
| `instruction_set_ref` | [Ref](./Ref.md) | 是 | 按来源优先级和作用域解决的指令集合。 | 类型约束见对应对象 |
| `material_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 任务指定或相关的获准实际材料版本。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 解析结果提交新理解版本；原文不变，重大目标变化向用户显示。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "input_refs": [],
  "instruction_set_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "material_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalIntentSemanticRequest`。
