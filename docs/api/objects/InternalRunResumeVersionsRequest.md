# InternalRunResumeVersionsRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

版本兼容检查的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `checkpoint_ref` | [Ref](./Ref.md) | 是 | 已提交检查点，不能是模型虚构摘要。 | 类型约束见对应对象 |
| `current_runtime_manifest` | [Ref](./Ref.md) | 是 | 正在运行代码与协议的实际版本清单。 | 类型约束见对应对象 |
| `migration_policy` | [Ref](./Ref.md) | 是 | 检查点跨协议版本迁移的批准策略。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 记录迁移输入/输出和实现版本，保留旧checkpoint。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "checkpoint_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "current_runtime_manifest": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "migration_policy": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalRunResumeVersionsRequest`。
