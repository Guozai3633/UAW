# ProcessSpec

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

argv模式优先；shell模式是单独能力。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `workspace_ref` | [Ref](./Ref.md) | 是 | 工作区版本 | 类型约束见对应对象 |
| `executable` | [NonEmptyText](./NonEmptyText.md) | 是 | 可执行文件或批准句柄 | 类型约束见对应对象 |
| `argv` | 数组&lt;[Text](./Text.md)&gt; | 是 | 独立参数数组 | 最少项 `0`；最多项 `256` |
| `cwd` | [RelativePath](./RelativePath.md) | 是 | 根内工作目录，.表示根 | 类型约束见对应对象 |
| `environment` | 数组&lt;[EnvVar](./EnvVar.md)&gt; | 是 | 额外非秘密环境变量 | 最少项 `0`；最多项 `256` |
| `timeout_ms` | [Duration](./Duration.md) | 是 | 最大运行时间 | ≥ `1`；类型约束见对应对象 |
| `shell_command` | [NonEmptyText](./NonEmptyText.md) | 否 | shell模式命令 | 类型约束见对应对象 |
| `shell_profile_ref` | [Ref](./Ref.md) | 否 | 获准shell配置 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "required": [
          "shell_command"
        ]
      },
      "then": {
        "properties": {
          "argv": {
            "maxItems": 0
          }
        }
      }
    }
  ]
}
```

## dependentRequired结构规则

```json
{
  "dependentRequired": {
    "shell_command": [
      "shell_profile_ref"
    ],
    "shell_profile_ref": [
      "shell_command"
    ]
  }
}
```

## 运行时约束

- timeout必须>0；shell_command和shell_profile_ref同时出现；shell模式argv必须为空；Runner执行真实OS策略；超时终止进程树并报告残留。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "workspace_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "executable": "example_001",
  "argv": [],
  "cwd": "src/main.py",
  "environment": [],
  "timeout_ms": 1
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ProcessSpec`。
