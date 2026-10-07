# InternalAgentDefinitionsRepositoryRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

定义提交与版本的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `validated_drafts` | 数组&lt;[Draft](./Draft.md)&gt; | 是 | 经过定义、依赖、权限和模型意图核对的草案。 | 最多项 `256` |
| `batch_policy` | enum: `atomic` / `independent` | 是 | atomic整批提交或independent逐项提交。 | — |
| `stable_item_keys` | 数组&lt;[Text](./Text.md)&gt; | 是 | 与每个草案位置一一对应的稳定去重键。 | 最多项 `256` |
| `expected_versions` | 映射&lt;string, [Revision](./Revision.md)&gt; | 是 | 每个参与资源的预期修订，不允许缺失应校验的资源。 | 最多键 `256`；值逐项按schema校验 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 同版本hash不可变，定义未执行；查询pending意图防反馈丢失重复create。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "validated_drafts": [],
  "batch_policy": "atomic",
  "stable_item_keys": [],
  "expected_versions": {}
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentDefinitionsRepositoryRequest`。
