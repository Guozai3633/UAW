# RunnerProcessIdentity

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

独立OS观察的进程实例；不是UAW账号。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `pid` | integer | 是 | 实际进程ID | ≥ `1`；≤ `4294967295` |
| `created` | string | 是 | Windows FILETIME十进制字符串，避免签名JSON数值精度丢失 | 最多字符 `20`；正则 `^[1-9][0-9]{0,19}$` |
| `user_sid` | [ID](./ID.md) | 是 | 实际用户SID | 类型约束见对应对象 |
| `logon_sid` | [ID](./ID.md) | 是 | 实际本机登录SID | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "pid": 1,
  "created": "133987654321098765",
  "user_sid": "example_001",
  "logon_sid": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerProcessIdentity`。
