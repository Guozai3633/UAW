# ConfigurationDraft

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

管理配置业务草案，发布ID/revision/state由服务分配。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `model_refs` | 数组&lt;[ModelRef](./ModelRef.md)&gt; | 是 | 模型目录 | 最少项 `0`；最多项 `256` |
| `provider_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 提供方 | 最少项 `0`；最多项 `256` |
| `environment_template_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 环境模板 | 最少项 `0`；最多项 `256` |
| `feature_flags` | 数组&lt;[FeatureFlag](./FeatureFlag.md)&gt; | 是 | 旗标 | 最少项 `0`；最多项 `256` |
| `approval_policy_ref` | [Ref](./Ref.md) | 是 | 审批政策 | 类型约束见对应对象 |
| `storage_policy_ref` | [Ref](./Ref.md) | 是 | 部署存储政策 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "model_refs": [],
  "provider_refs": [],
  "environment_template_refs": [],
  "feature_flags": [],
  "approval_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "storage_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ConfigurationDraft`。
