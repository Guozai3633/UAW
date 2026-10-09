# A 对 MS-C7 阶段版的审阅与 SQL 适配

阶段来源：B ff8a432 / b121c9b；A 普通 merge 1b04d6e。日期2026-10-09。

## 已可消费的 A 适配

`uaw.infrastructure.db.context_batch.PostgresContextRecordBatch(records).read(principal, keys)`
消费B的 `RecordReadKey` / `ContextRecordBatchPort`。一次SQL VALUES/LEFT JOIN保留顺序、
重复及历史版本，任一缺失/删除/不属于记录owner整体拒绝。128键、正整数revision上限保留；
全NULL版本显式SQL cast已修复，初次错误回执保留。9个实际SQL用例通过。

`assemble_registered_context(..., record_batch=..., batch_required=True)`显式注入；
原默认构造不变。SQL owner是Principal.id，不能由该存储字段证明auth_session或tenant；
这些完整来源检查仍由当前Context/Run权威执行。没有跨请求授权缓存。

当前A源码尚在本轮验证，固定阶段SHA发布后再消费；不要求B中途同步A所有新代码。

## 交回 B 的组件问题

A在阶段合入后实际运行 `python -m mypy src/uaw`，发现：

- `context/read_batch.py:88`：`seen`空字典缺明确键值类型。
- `context/registered.py:852`：group得到 `tuple[Record, ...] | None`，传给`_read`
  的声明为 `tuple[Record, Record, Record] | None`。需B在完整有界数量核实后形成正确类型；
  不放宽元数据数量检查，不让A修改B源文件。

MS-C7最终提交应包含修复、B模块Mypy及已有等价/当前来源复查。A回执保存于
`tests/.artifacts/A/MS-I2i`；本页不将阶段接口合入视为完整MS-C7 accepted。
