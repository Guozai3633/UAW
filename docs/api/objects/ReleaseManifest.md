# ReleaseManifest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

可评测、恢复核对的不可变系统版本清单。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 发布 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 版本 | 类型约束见对应对象 |
| `runtime_version` | [Version](./Version.md) | 是 | 代码 | 类型约束见对应对象 |
| `contract_version` | [Version](./Version.md) | 是 | 协议 | 类型约束见对应对象 |
| `prompt_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 提示词版本 | 最少项 `0`；最多项 `256` |
| `skill_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 技能版本 | 最少项 `0`；最多项 `256` |
| `tool_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 工具schema | 最少项 `0`；最多项 `256` |
| `adapter_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 适配器 | 最少项 `0`；最多项 `256` |
| `model_catalog_ref` | [Ref](./Ref.md) | 是 | 模型目录 | 类型约束见对应对象 |
| `configuration_ref` | [Ref](./Ref.md) | 是 | 配置 | 类型约束见对应对象 |
| `environment_template_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 环境 | 最少项 `0`；最多项 `256` |
| `evaluation_report_ref` | [Ref](./Ref.md) | 是 | 回归证据 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 清单摘要 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "runtime_version": "example_001",
  "contract_version": "example_001",
  "prompt_refs": [],
  "skill_refs": [],
  "tool_refs": [],
  "adapter_refs": [],
  "model_catalog_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "configuration_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "environment_template_refs": [],
  "evaluation_report_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ReleaseManifest`。
