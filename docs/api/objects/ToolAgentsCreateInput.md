# ToolAgentsCreateInput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

把用户明确要求的子Agent保存到当前会话。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `definitions` | [DefinitionDrafts](./DefinitionDrafts.md) | 是 | 草案 | 类型约束见对应对象 |
| `batch_policy` | [BatchPolicy](./BatchPolicy.md) | 是 | 批量策略 | 类型约束见对应对象 |
| `source_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 明确用户要求 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 不能包含owner、权限批准或conversation；create不启动实例；同键相同内容幂等。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "definitions": [
    {
      "client_definition_key": "api_reviewer_v1",
      "name": "API兼容性审查员",
      "description": "读取代码及调用方，整理兼容风险和证据",
      "instructions": "先读取接口及调用方，再核对行为差异。证据不足时明确说明，不改动文件。",
      "use_when": [
        "独立核对API兼容性"
      ],
      "avoid_when": [
        "需要实际修改代码"
      ],
      "skill_refs": [],
      "tool_categories": [
        "file_read",
        "code_search"
      ],
      "input_contract": {
        "goal": "核对API兼容性并交付证据",
        "requirements": [
          {
            "id": "req_compatibility",
            "text": "说明兼容风险并引用调用方证据",
            "mandatory": true,
            "source_refs": [
              {
                "kind": "input",
                "id": "input_create_roles",
                "version": "1"
              }
            ]
          }
        ],
        "outputs": [
          {
            "id": "out_report",
            "kind": "markdown",
            "description": "含证据的检查报告",
            "required": true
          }
        ],
        "version": "1"
      },
      "output_contract": {
        "goal": "核对API兼容性并交付证据",
        "requirements": [
          {
            "id": "req_compatibility",
            "text": "说明兼容风险并引用调用方证据",
            "mandatory": true,
            "source_refs": [
              {
                "kind": "input",
                "id": "input_create_roles",
                "version": "1"
              }
            ]
          }
        ],
        "outputs": [
          {
            "id": "out_report",
            "kind": "markdown",
            "description": "含证据的检查报告",
            "required": true
          }
        ],
        "version": "1"
      },
      "model_request": {
        "mode": "inherit"
      }
    }
  ],
  "batch_policy": "atomic",
  "source_input_ref": {
    "kind": "input",
    "id": "input_create_roles",
    "version": "1"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolAgentsCreateInput`。
