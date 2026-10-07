# RevisionMap

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

ID到CAS修订映射；键和值均校验。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

映射&lt;string, [Revision](./Revision.md)&gt;。最多键 `256`；值逐项按schema校验

## propertyNames结构规则

```json
{
  "propertyNames": {
    "description": "域内不透明标识，不能推断主体或访问权限。",
    "type": "string",
    "minLength": 1,
    "maxLength": 128,
    "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$"
  }
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RevisionMap`。
