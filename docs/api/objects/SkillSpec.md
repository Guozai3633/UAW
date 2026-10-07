# SkillSpec

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

方法包只先提供摘要，激活时加载完整指令。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 技能ID | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 版本 | 类型约束见对应对象 |
| `name` | [NonEmptyText](./NonEmptyText.md) | 是 | 名称 | 类型约束见对应对象 |
| `description` | [NonEmptyText](./NonEmptyText.md) | 是 | 适用任务 | 类型约束见对应对象 |
| `instruction_ref` | [Ref](./Ref.md) | 是 | 完整方法 | 类型约束见对应对象 |
| `dependency_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 脚本/模板/资料 | 最少项 `0`；最多项 `256` |
| `required_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 能力需求 | 最少项 `0`；最多项 `256` |
| `output_contract` | [Contract](./Contract.md) | 是 | 验收标准 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 内容摘要 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "name": "example_001",
  "description": "example_001",
  "instruction_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "dependency_refs": [],
  "required_capabilities": [],
  "output_contract": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
  },
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.SkillSpec`。
