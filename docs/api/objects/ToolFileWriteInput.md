# ToolFileWriteInput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

写获准根内文件。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `workspace_ref` | [Ref](./Ref.md) | 是 | 工作区 | 类型约束见对应对象 |
| `path` | [RelativePath](./RelativePath.md) | 是 | 相对路径 | 类型约束见对应对象 |
| `text` | [Text](./Text.md) | 否 | 新内容 | 类型约束见对应对象 |
| `expected_content_hash` | [Hash](./Hash.md) | 否 | 现有内容摘要 | 类型约束见对应对象 |
| `create_only` | [Bool](./Bool.md) | 是 | 仅新建 | 类型约束见对应对象 |
| `content_ref` | [Ref](./Ref.md) | 否 | 大内容的获准完整blob；与text互斥。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "required": [
        "text"
      ],
      "not": {
        "required": [
          "content_ref"
        ]
      }
    },
    {
      "required": [
        "content_ref"
      ],
      "not": {
        "required": [
          "text"
        ]
      }
    }
  ]
}
```

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "create_only": {
            "const": false
          }
        },
        "required": [
          "create_only"
        ]
      },
      "then": {
        "required": [
          "expected_content_hash"
        ]
      }
    }
  ]
}
```

## 运行时约束

- create_only=false须旧摘要；写原子替换、记录before/after；超大内容先上传blob。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "workspace_ref": {
    "kind": "workspace",
    "id": "workspace_main",
    "version": "tree_7"
  },
  "path": "src/main.py",
  "text": "print('hello')\n",
  "expected_content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "create_only": false
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolFileWriteInput`。
