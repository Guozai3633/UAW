# ProcessRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

启动返回进程句柄，实际结果使用poll。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 进程 | 类型约束见对应对象 |
| `spec` | [ProcessSpec](./ProcessSpec.md) | 是 | 实际配置 | 类型约束见对应对象 |
| `status` | [ProcessState](./ProcessState.md) | 是 | 进程状态 | 类型约束见对应对象 |
| `started_at` | [Timestamp](./Timestamp.md) | 是 | 启动时间 | 类型约束见对应对象 |
| `ended_at` | [Timestamp](./Timestamp.md) | 否 | 结束时间 | 类型约束见对应对象 |
| `exit_code` | [ExitCode](./ExitCode.md) | 否 | 真实退出码；未结束缺省 | 类型约束见对应对象 |
| `stdout_ref` | [Ref](./Ref.md) | 否 | 输出内容 | 类型约束见对应对象 |
| `stderr_ref` | [Ref](./Ref.md) | 否 | 错误输出 | 类型约束见对应对象 |
| `output_cursor` | [Cursor](./Cursor.md) | 否 | 未读日志 | 类型约束见对应对象 |
| `change_set_ref` | [Ref](./Ref.md) | 否 | 命令造成的改动 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 启动/终止失败 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "spec": {
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
  },
  "status": "starting",
  "started_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ProcessRecord`。
