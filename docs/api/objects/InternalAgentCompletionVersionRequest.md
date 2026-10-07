# InternalAgentCompletionVersionRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

版本与硬条件校验的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `report_ref` | [Ref](./Ref.md) | 是 | 绑定当前成果版本的真实核验报告。 | 类型约束见对应对象 |
| `expected_artifact_versions` | 映射&lt;string, [Version](./Version.md)&gt; | 是 | 待完成成果的实际版本；内容变化使旧验证失效。 | 最多键 `256`；值逐项按schema校验 |
| `pending_effect_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 完成提交时尚未知的外部效果，阻止虚假成功。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 提案绑定当前revision，最终CAS归Run。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "report_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_artifact_versions": {},
  "pending_effect_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCompletionVersionRequest`。
