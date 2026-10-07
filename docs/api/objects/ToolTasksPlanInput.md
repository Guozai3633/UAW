# ToolTasksPlanInput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

创建/修改执行计划。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `planning_level` | [GraphPlanningLevel](./GraphPlanningLevel.md) | 是 | steps或dag | 类型约束见对应对象 |
| `node_specs` | 数组&lt;[NodeSpec](./NodeSpec.md)&gt; | 是 | 完整初始图 | 最少项 `0`；最多项 `256` |
| `patch` | [PlanPatch](./PlanPatch.md) | 否 | 增量修改 | 类型约束见对应对象 |
| `expected_plan_revision` | [Revision](./Revision.md) | 是 | 0创建 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "required": [
        "patch"
      ],
      "properties": {
        "node_specs": {
          "maxItems": 0
        }
      }
    },
    {
      "not": {
        "required": [
          "patch"
        ]
      },
      "properties": {
        "node_specs": {
          "minItems": 1
        }
      }
    }
  ]
}
```

## 运行时约束

- patch与非空node_specs互斥；硬依赖校验由代码；不自动invoke。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "planning_level": "steps",
  "node_specs": [],
  "expected_plan_revision": 0,
  "patch": {
    "base_revision": 0,
    "upsert_nodes": [],
    "remove_node_ids": [],
    "reason": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolTasksPlanInput`。
