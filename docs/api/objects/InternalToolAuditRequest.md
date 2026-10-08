# InternalToolAuditRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

执行审计与指标的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `call_ref` | [Ref](./Ref.md) | 是 | 实际调用记录及固定参数版本。 | 类型约束见对应对象 |
| `approval_ref` | [Ref](./Ref.md) | 否 | 参数和资源版本匹配、未过期的授权依据。 | 类型约束见对应对象 |
| `actor` | [Principal](./Principal.md) | 是 | 由可信认证产生的操作主体，不能由模型正文自报。 | 类型约束见对应对象 |
| `effect_state` | [EffectState](./EffectState.md) | 是 | 外部效果confirmed/pending/unknown，不能凭HTTP200推断。 | 类型约束见对应对象 |
| `usage` | [Usage](./Usage.md) | 是 | 全部真实attempt消耗，账单不确定性显式记录。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 关键审计不可采样丢失；Trace可按政策采样，二者用调用ID关联。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "call_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "actor": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "effect_state": "confirmed",
  "usage": {
    "attempt_id": "example_001",
    "resources": {
      "currency": "CNY",
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0"
    },
    "billing_state": "confirmed"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolAuditRequest`。
