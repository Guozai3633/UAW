# InternalAgentDefinitionsDesignerRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

角色设计方法的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `user_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 当前用户明确要求的原始输入，不是模型推断授权。 | 类型约束见对应对象 |
| `existing_definition_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 当前会话已保存定义，避免重复职责或同名。 | 最多项 `256` |
| `visible_capabilities` | [Ref](./Ref.md) | 是 | 当前已过滤角色/旗标/主体权限的能力摘要。 | 类型约束见对应对象 |
| `design_method_ref` | [Ref](./Ref.md) | 是 | 主Agent按需加载的精炼角色设计方法。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 只产生待验证草案，Registry提交成功后才宣布已创建。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "user_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "existing_definition_refs": [],
  "visible_capabilities": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "design_method_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentDefinitionsDesignerRequest`。
