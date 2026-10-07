# 开发设计维护源

`catalog.py` 保存各架构节点的具体开发策略，`build_design.py` 将它们生成到 `docs/design/`，并产生节点 → 文档 → 计划代码位置的映射。

这些是开发设计，不是 Runtime 实现。计划代码位置不能标记为已存在。策略需要随真实任务验证更新；不要只编辑生成文档，下一次重建会覆盖。

改策略的重建顺序：项目根目录运行 `python design/build_design.py`，再运行 `python architecture/build_atlas.py`。新增/修改图节点时，先运行一次图生成器更新graph.json，再生成设计文档/映射，最后重建图谱链接。文档生成会检查图节点覆盖率与策略字段，图谱生成消费 `design/design-map.json` 并将设计链接加入节点详情。
