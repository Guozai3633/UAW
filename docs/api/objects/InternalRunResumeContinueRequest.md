# InternalRunResumeContinueRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

恢复可运行工作的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `reconciled_state_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 恢复后已经复核/对账的业务域版本。 | 最多项 `256` |
| `expected_run_revision` | [Revision](./Revision.md) | 是 | Run状态CAS修订，过期执行者不能推进新状态。 | 类型约束见对应对象 |
| `resumable_nodes` | 数组&lt;[ID](./ID.md)&gt; | 是 | 通过依赖/权限/环境/效果核验的可续跑节点。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 恢复是继续同Run，rerun另建ID并保留关联来源。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "reconciled_state_refs": [],
  "expected_run_revision": 0,
  "resumable_nodes": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalRunResumeContinueRequest`。
