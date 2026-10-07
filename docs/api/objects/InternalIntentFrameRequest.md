# InternalIntentFrameRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

任务框架的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `goal` | [Text](./Text.md) | 是 | 当前目标，必须保留原文与已确认修订的含义。 | 类型约束见对应对象 |
| `constraints` | 数组&lt;[Constraint](./Constraint.md)&gt; | 是 | 有用户/政策来源的任务硬约束。 | 最多项 `256` |
| `output_specs` | 数组&lt;[OutputSpec](./OutputSpec.md)&gt; | 是 | 预期交付类型、用途和是否必需。 | 最多项 `256` |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际取得、可读取且与本次要求有关的证据。 | 最多项 `256` |
| `expected_revision` | [Revision](./Revision.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- Intent是TaskFrame唯一写入者；版本追加，Run记录frame_ref和变更事件。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "goal": "example_001",
  "constraints": [],
  "output_specs": [],
  "evidence_refs": [],
  "expected_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalIntentFrameRequest`。
