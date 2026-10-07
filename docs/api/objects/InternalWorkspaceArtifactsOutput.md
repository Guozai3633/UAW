# InternalWorkspaceArtifactsOutput

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
      "$ref": "#/$defs/InternalWorkspaceArtifactsOutputRegister"
    },
    {
      "$ref": "#/$defs/InternalWorkspaceArtifactsOutputPreview"
    },
    {
      "$ref": "#/$defs/InternalWorkspaceArtifactsOutputExport"
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
  "action": "register",
  "result": {
    "id": "example_001",
    "version": "example_001",
    "title": "example_001",
    "format_kind": "example_001",
    "media_type": "example_001",
    "content_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "size_bytes": 0,
    "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "provenance_refs": [],
    "verification_refs": [],
    "created_at": "2026-10-07T02:00:00Z"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalWorkspaceArtifactsOutput`。
