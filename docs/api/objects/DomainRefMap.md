# DomainRefMap

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

域名到固定版本的映射。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

映射&lt;string, [Ref](./Ref.md)&gt;。最多键 `32`；值逐项按schema校验

## propertyNames结构规则

```json
{
  "propertyNames": {
    "pattern": "^[a-z][a-z0-9_.-]*$"
  }
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DomainRefMap`。
