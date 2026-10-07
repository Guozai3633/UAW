# InternalToolMcpInvalidateRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

变化与撤销的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `provider_ref` | [Ref](./Ref.md) | 是 | 管理员配置且当前可用的固定提供方版本。 | 类型约束见对应对象 |
| `reason` | enum: `revoked` / `expired` / `capability_changed` / `disconnected` | 是 | 明确操作理由；不得用理由文字替代权限/版本校验。 | — |
| `affected_revision` | [Revision](./Revision.md) | 是 | 发生撤销/能力变化的绑定修订，用于失效传播。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 撤销当前生效，普通版本固定不能绕过。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "reason": "revoked",
  "affected_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolMcpInvalidateRequest`。
