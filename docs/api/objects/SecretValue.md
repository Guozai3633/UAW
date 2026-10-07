# SecretValue

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

write-only秘密，最大8192字符。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

string。最少字符 `1`；最多字符 `8192`；仅写 `True`

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
"EXAMPLE_ONLY_SECRET"
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.SecretValue`。
