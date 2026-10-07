# ToolAgentsInvokeInput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

创建隔离实例执行当前有界分工。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `delegation` | [DelegationSpec](./DelegationSpec.md) | 是 | 目标、资料、成果、预算 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 调用是当前主Agent语义决定；创建角色不自动invoke；不做独立性成立不了的并发。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "delegation": {
    "goal": "核对本次API修改是否影响已有调用方",
    "input_refs": [
      {
        "kind": "workspace",
        "id": "workspace_main",
        "version": "tree_7"
      }
    ],
    "definition_ref": {
      "kind": "agent_definition",
      "id": "agent_api_reviewer",
      "version": "2"
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
    "budget": {
      "limits": {
        "input_tokens": 60000,
        "output_tokens": 12000,
        "model_calls": 12,
        "tool_calls": 30,
        "child_agents": 0,
        "wall_time_ms": 600000,
        "money": "10.00",
        "currency": "CNY"
      },
      "max_steps": 20,
      "max_depth": 0,
      "deadline": "2026-10-07T02:10:00Z"
    },
    "read_refs": [
      {
        "kind": "workspace",
        "id": "workspace_main",
        "version": "tree_7"
      }
    ],
    "write_refs": [],
    "creation_key": "review_api_change_7"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolAgentsInvokeInput`。
