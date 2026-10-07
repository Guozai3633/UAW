# InternalRunResumeAccessRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

重建连接与核验的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `domain_resource_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 检查点固定的各业务域资源，恢复逐个复核。 | 最多项 `256` |
| `current_principal` | [Principal](./Principal.md) | 是 | 恢复请求的当前认证主体，不继承旧过期权限。 | 类型约束见对应对象 |
| `current_config_revision` | [Revision](./Revision.md) | 是 | 恢复时有效配置版本，含当前撤销与能力开关。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- checkpoint保存引用，当前授权读取原权威。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "domain_resource_refs": [],
  "current_principal": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "current_config_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalRunResumeAccessRequest`。
