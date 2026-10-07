# Schema

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

JSON Schema 2020-12注册片段；不得联网任意解析远端$ref，须可信注册/资源上限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

映射&lt;string, [JsonValue](./JsonValue.md)&gt;。值逐项按schema校验

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Schema`。
