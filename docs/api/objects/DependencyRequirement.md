# DependencyRequirement

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

声明环境需要，不把shell安装字符串当依赖契约。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `kind` | [DependencyKind](./DependencyKind.md) | 是 | 系统/语言/包 | 类型约束见对应对象 |
| `name` | [NonEmptyText](./NonEmptyText.md) | 是 | 例如python、go | 类型约束见对应对象 |
| `version_constraint` | [NonEmptyText](./NonEmptyText.md) | 是 | 版本要求 | 类型约束见对应对象 |
| `source_profile_ref` | [Ref](./Ref.md) | 否 | 管理员批准的来源 | 类型约束见对应对象 |
| `required` | [Bool](./Bool.md) | 是 | 必需 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "kind": "system",
  "name": "example_001",
  "version_constraint": "example_001",
  "required": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DependencyRequirement`。
