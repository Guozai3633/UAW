# ExtensionManifest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

能力包安装、依赖、校验与启停。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 插件 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 版本 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 摘要 | 类型约束见对应对象 |
| `skill_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 技能 | 最少项 `0`；最多项 `256` |
| `tool_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 工具 | 最少项 `0`；最多项 `256` |
| `dependency_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 依赖 | 最少项 `0`；最多项 `256` |
| `requested_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 请求权限 | 最少项 `0`；最多项 `256` |
| `state` | [ProviderState](./ProviderState.md) | 是 | 启用状态 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "skill_refs": [],
  "tool_refs": [],
  "dependency_refs": [],
  "requested_capabilities": [],
  "state": "draft"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ExtensionManifest`。
