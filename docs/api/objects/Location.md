# Location

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

引用定位器，kind对应字段由Runtime交叉检查。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `kind` | enum: `whole` / `page` / `lines` / `paragraph` / `json_pointer` / `cell_range` / `text_span` | 是 | 定位种类 | — |
| `start` | [Count](./Count.md) | 否 | 起点：页/行从1，字符offset从0 | 类型约束见对应对象 |
| `end` | [Count](./Count.md) | 否 | 含义随kind，字符end为排他 | 类型约束见对应对象 |
| `anchor` | [Text](./Text.md) | 否 | 段落ID/JSON Pointer/单元格范围 | 类型约束见对应对象 |
| `relative_path` | [RelativePath](./RelativePath.md) | 否 | 工作区内文件位置 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- end不得小于start；whole不填写起止；page/lines必须start>=1；json_pointer/cell_range必须anchor。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "kind": "whole"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Location`。
