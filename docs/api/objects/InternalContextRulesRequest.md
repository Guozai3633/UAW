# InternalContextRulesRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

规则与信任装配的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `scope_paths` | 数组&lt;[PathRef](./PathRef.md)&gt; | 是 | 获准项目路径引用，用于查找作用域项目规则。 | 最多项 `256` |
| `user_instruction_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 用户当前要求和获准偏好规则，保留来源。 | 最多项 `256` |
| `activated_skill_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 本轮已激活的固定技能版本，按作用域继承方法。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 保存InstructionSet与rule_manifest；跨目录分别记录适用规则，工具写入前核对作用域。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "scope_paths": [],
  "user_instruction_refs": [],
  "activated_skill_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalContextRulesRequest`。
