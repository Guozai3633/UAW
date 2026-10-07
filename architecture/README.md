# 架构图谱维护

这组文件用于设计交流，不实现 Runtime。

- `build_atlas.py`：节点/关系/归属的维护源与生成器。
- `explorer.template.html`：交互图页面模板。
- `graph.json`：生成的可消费图目录，包含节点入口、输入/输出、约束、分层关系与开发设计/计划代码映射。
- `../ARCHITECTURE_ATLAS.md` 和 `../demo/uaw-architecture-map.html`：由同一份图目录生成的文档与独立 HTML。

在项目根目录运行 `python architecture/build_atlas.py` 即可重建，无第三方 Python 包。脚本检查节点/关系引用、唯一 ID、父级归属环和未展示节点。职责图中的反馈环是允许的，不能用这份图取代运行中的任务依赖 DAG 校验。

详细策略维护在 `design/catalog.py`；正常修改先运行 `python design/build_design.py` 再重建图。节点新增时先生成一次graph.json，补齐新节点策略后生成设计映射，再重建图。完整指引见项目README和docs/DOCUMENT_MAP.md。

HTML 内嵌图目录，可直接打开，不需要联网。点击节点看详情，通过“展开内部”或双击进入下一层；也可搜索节点、筛选关系类型。窄屏采用节点卡片与关系列表。修改生成文件会在下次重建时覆盖，应先修改维护源。
