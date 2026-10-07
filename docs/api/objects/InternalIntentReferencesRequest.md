# InternalIntentReferencesRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

指代解析的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `expressions` | 数组&lt;[Text](./Text.md)&gt; | 是 | 用户原文中待消解的指代/文件/材料称呼。 | 最多项 `256` |
| `candidate_scope` | [Scope](./Scope.md) | 是 | 指代消解允许搜索的资源范围。 | 类型约束见对应对象 |
| `expected_versions` | 映射&lt;string, [Revision](./Revision.md)&gt; | 是 | 每个参与资源的预期修订，不允许缺失应校验的资源。 | 最多键 `256`；值逐项按schema校验 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- TaskFrame只记录已解析引用及版本；候选是临时数据，授权由resolver复核。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "expressions": [],
  "candidate_scope": {
    "principal_id": "example_001"
  },
  "expected_versions": {}
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalIntentReferencesRequest`。
