# IncludeRules

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

基础快照收录策略，保护用户未提交改动。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `include_uncommitted` | [Bool](./Bool.md) | 是 | 包含获准未提交修改 | 类型约束见对应对象 |
| `include_untracked` | [Bool](./Bool.md) | 是 | 包含未跟踪文件 | 类型约束见对应对象 |
| `include_paths` | 数组&lt;[RelativePath](./RelativePath.md)&gt; | 是 | 显式包含 | 最少项 `0`；最多项 `256` |
| `exclude_paths` | 数组&lt;[RelativePath](./RelativePath.md)&gt; | 是 | 显式排除 | 最少项 `0`；最多项 `256` |
| `max_total_bytes` | [Count](./Count.md) | 是 | 收录上限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 默认不收录密钥和缓存；超过上限失败或返回明确缺口，不静默截断。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "include_uncommitted": true,
  "include_untracked": true,
  "include_paths": [],
  "exclude_paths": [],
  "max_total_bytes": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.IncludeRules`。
