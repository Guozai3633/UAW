# ContextSnapshot

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

一次模型调用的不可变输入；引用固定实际内容。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 快照 | 类型约束见对应对象 |
| `epoch` | [Revision](./Revision.md) | 是 | 上下文纪元 | 类型约束见对应对象 |
| `purpose` | [Purpose](./Purpose.md) | 是 | 构建目的 | 类型约束见对应对象 |
| `blocks` | 数组&lt;[ContextBlock](./ContextBlock.md)&gt; | 是 | 按顺序输入 | 最少项 `0`；最多项 `256` |
| `instruction_set_ref` | [Ref](./Ref.md) | 是 | 已解决规则 | 类型约束见对应对象 |
| `capability_snapshot_ref` | [Ref](./Ref.md) | 是 | 本轮工具/角色摘要 | 类型约束见对应对象 |
| `manifest` | [Manifest](./Manifest.md) | 是 | 依赖 | 类型约束见对应对象 |
| `input_tokens` | [Count](./Count.md) | 是 | 估算输入量 | 类型约束见对应对象 |
| `output_reserve` | [Count](./Count.md) | 是 | 保留输出Token | 类型约束见对应对象 |
| `tool_reserve` | [Count](./Count.md) | 是 | 保留工具往返Token | 类型约束见对应对象 |
| `omitted_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 主动裁剪资料 | 最少项 `0`；最多项 `256` |
| `compressed_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 语义压缩结果 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 总预算必须适配实际模型；关键用户要求不可静默裁掉；资料内容不自动升级为指令。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "epoch": 0,
  "purpose": "draft_preview",
  "blocks": [],
  "instruction_set_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "capability_snapshot_ref": {
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
  "input_tokens": 0,
  "output_reserve": 0,
  "tool_reserve": 0,
  "omitted_refs": [],
  "compressed_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ContextSnapshot`。
