# ConversationListSnapshot

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

内部持久分页快照；一小时失效，最多4096会话，超容量明确不可用。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 分页身份 | 类型约束见对应对象 |
| `expires` | integer | 是 | Unix秒期限 | ≥ `0` |
| `versions` | 数组&lt;[ConversationListVersion](./ConversationListVersion.md)&gt; | 是 | 创建顺序的固定版本 | 最少项 `0`；最多项 `4096` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "expires": 0,
  "versions": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ConversationListSnapshot`。
