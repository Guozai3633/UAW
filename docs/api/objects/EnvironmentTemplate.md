# EnvironmentTemplate

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

预装优先；按需安装须有权限、来源及验收。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 模板 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 固定版本 | 类型约束见对应对象 |
| `dependencies` | 数组&lt;[DependencyRequirement](./DependencyRequirement.md)&gt; | 是 | 依赖 | 最少项 `0`；最多项 `256` |
| `setup_actions` | 数组&lt;[ProcessSpec](./ProcessSpec.md)&gt; | 是 | 受控初始化命令 | 最少项 `0`；最多项 `256` |
| `verification_actions` | 数组&lt;[ProcessSpec](./ProcessSpec.md)&gt; | 是 | 真实检查 | 最少项 `0`；最多项 `256` |
| `network_policy_ref` | [Ref](./Ref.md) | 是 | 网络策略 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "dependencies": [],
  "setup_actions": [],
  "verification_actions": [],
  "network_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.EnvironmentTemplate`。
