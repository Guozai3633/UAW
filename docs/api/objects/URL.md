# URL

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

绝对HTTP(S)候选地址；网络策略必须独立检查重定向/地址。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

string。最多字符 `4096`；正则 `^https?://`；格式 `uri`

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
"https://example.org/resource"
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.URL`。
