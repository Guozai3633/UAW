# RunnerLocalGetRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

查询原本机启动；当前主体/通道/原根复查，后端重启标unavailable，不重发。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `launch_id` | [ID](./ID.md) | 是 | 原启动 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 同账号新Web session不能接管旧实例；状态不替代Tool/预算/RootSource。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "launch_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerLocalGetRequest`。
