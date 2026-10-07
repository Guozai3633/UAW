# ExecutionAssessment

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

四个独立执行选择，属于可修改建议，不授予权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `planning` | [PlanningLevel](./PlanningLevel.md) | 是 | 无规划、清单或依赖图 | 类型约束见对应对象 |
| `delegation` | [DelegationMode](./DelegationMode.md) | 是 | 单Agent或父子Agent | 类型约束见对应对象 |
| `parallelism` | [Parallelism](./Parallelism.md) | 是 | 顺序或独立部分并发 | 类型约束见对应对象 |
| `information_state` | [InformationState](./InformationState.md) | 是 | 可以开始、先读材料或澄清 | 类型约束见对应对象 |
| `rationale` | [NonEmptyText](./NonEmptyText.md) | 是 | 判断依据及成本收益 | 类型约束见对应对象 |
| `candidate_agent_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 可用角色候选 | 最少项 `0`；最多项 `256` |
| `independent_groups` | 数组&lt;[WorkGroup](./WorkGroup.md)&gt; | 是 | 可独立执行的工作 | 最少项 `0`；最多项 `256` |
| `reassessment_conditions` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 需要重新判断的条件 | 最少项 `0`；最多项 `256` |
| `source_frame_ref` | [Ref](./Ref.md) | 是 | 本次理解版本 | 类型约束见对应对象 |
| `decision_status` | [DecisionStatus](./DecisionStatus.md) | 是 | 资料不足时暂定 | 类型约束见对应对象 |
| `parallel_scope` | [ParallelScope](./ParallelScope.md) | 是 | 工具并发与Agent并发分开 | 类型约束见对应对象 |
| `suggested_delegations` | 数组&lt;[SuggestedDelegation](./SuggestedDelegation.md)&gt; | 是 | 建议而非已启动 | 最少项 `0`；最多项 `16` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "parallelism": {
            "const": "serial"
          }
        },
        "required": [
          "parallelism"
        ]
      },
      "then": {
        "properties": {
          "parallel_scope": {
            "const": "none"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "parallelism": {
            "const": "parallel"
          }
        },
        "required": [
          "parallelism"
        ]
      },
      "then": {
        "properties": {
          "parallel_scope": {
            "enum": [
              "tools",
              "agents",
              "mixed"
            ]
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "delegation": {
            "const": "single"
          }
        },
        "required": [
          "delegation"
        ]
      },
      "then": {
        "properties": {
          "suggested_delegations": {
            "maxItems": 0
          },
          "parallel_scope": {
            "enum": [
              "none",
              "tools"
            ]
          }
        }
      }
    }
  ]
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "planning": "steps",
  "delegation": "single",
  "parallelism": "parallel",
  "information_state": "read_materials",
  "rationale": "先并发只读检索接口与调用方；是否委派需读完材料后再判断。",
  "candidate_agent_refs": [],
  "independent_groups": [],
  "reassessment_conditions": [
    "读取实现和调用方后"
  ],
  "source_frame_ref": {
    "kind": "task_frame",
    "id": "task_api_1",
    "version": "1"
  },
  "decision_status": "provisional",
  "parallel_scope": "tools",
  "suggested_delegations": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ExecutionAssessment`。
