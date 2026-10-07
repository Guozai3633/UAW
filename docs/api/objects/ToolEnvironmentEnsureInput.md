# ToolEnvironmentEnsureInput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

按批准模板准备环境并核验。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `workspace_ref` | [Ref](./Ref.md) | 是 | 工作区 | 类型约束见对应对象 |
| `template_ref` | [Ref](./Ref.md) | 是 | 批准模板 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 预装优先，安装受权限/网络来源/预算约束；失败返回真实日志；cwd和venv不等于OS隔离。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "workspace_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "template_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolEnvironmentEnsureInput`。
