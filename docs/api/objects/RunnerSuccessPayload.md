# RunnerSuccessPayload

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

互斥分支；所有字段须匹配所选action。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

互斥选择。—

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "$ref": "#/$defs/RunnerSuccessPayloadWorkspace.capture"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadWorkspace.allocate"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadEnvironment.inspect"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadEnvironment.ensure"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadFile.read"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadFile.write"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadFile.list"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadProcess.exec"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadProcess.poll"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadProcess.stop"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadChanges.capture"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadChanges.merge"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadChanges.revert"
    },
    {
      "$ref": "#/$defs/RunnerSuccessPayloadWorkspace.release"
    }
  ]
}
```

## 运行时约束

- 禁止用一个动作的参数调用另一个动作；服务端先确定action再校验分支。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action": "workspace.capture",
  "result": {
    "id": "example_001",
    "kind": "commit",
    "source_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "manifest": {
      "version": "example_001",
      "input_refs": [],
      "dependency_refs": [],
      "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    "include_rules": {
      "include_uncommitted": true,
      "include_untracked": true,
      "include_paths": [],
      "exclude_paths": [],
      "max_total_bytes": 0
    },
    "created_at": "2026-10-07T02:00:00Z"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerSuccessPayload`。
