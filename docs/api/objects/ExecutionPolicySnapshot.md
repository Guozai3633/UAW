# ExecutionPolicySnapshot

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

实时父子权限交集，非可复用授权；来源均为当前主体持久政策。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 已受理运行 | 类型约束见对应对象 |
| `scope` | [Scope](./Scope.md) | 是 | 当前可信请求作用域 | 类型约束见对应对象 |
| `policy_refs` | 数组&lt;见结构规则&gt; | 是 | 叶到根当前版本与摘要 | 最少项 `1`；最多项 `8` |
| `allowed_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 在全部父政策允许的当前scope能力 | 最少项 `1`；最多项 `256` |
| `denied_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 祖先显式禁止的并集 | 最少项 `0`；最多项 `256` |
| `network_allowlist` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 网络范围交集 | 最少项 `0`；最多项 `256` |
| `feature_flag_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 需另行核验的开关引用 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 不创建权限、不证明角色/设备/资源/租约或执行器已就绪；模型不能提供该对象来取得授权；执行前必须重查当前状态。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "scope": {
    "principal_id": "example_001"
  },
  "policy_refs": [
    {
      "kind": "policy",
      "id": "example_001",
      "version": "1",
      "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ],
  "allowed_capabilities": [
    "example_001"
  ],
  "denied_capabilities": [],
  "network_allowlist": [],
  "feature_flag_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ExecutionPolicySnapshot`。
