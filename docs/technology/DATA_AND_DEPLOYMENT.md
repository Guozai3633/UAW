# 数据权威、检索、缓存与部署

[技术总览](../../TECHNOLOGY_STACK.md) · [共享设施](modules/support.md) · [待定项D01](../plan/DECISIONS.md)

状态：设计主选。首版建议服务端权威＋本地缓存，D01尚未得到用户确认；没有把建议自动当作授权结论。

## 1. 数据放在哪里

| 数据 | 主选存储 | 归属与约束 |
| --- | --- | --- |
| 账号映射、会话、原文、Run/Item/Event | PostgreSQL | 账号/工作区条件必带；历史追加与状态更新分别控制 |
| Frame、Plan、角色/实例、Board、审批、预算、效果、成果元数据 | PostgreSQL领域表 | 相应Runtime管理，显式revision/CAS/幂等唯一约束 |
| 资料片段、工具/记忆语义索引 | PostgreSQL＋pgvector | 索引可重建；ToolSpec/原始资料/访问仍是权威 |
| 原始附件、工具大输出、报告、快照 | 私有FSBlobStore；按需S3 | SQL保存Ref/内容Hash/权限/保留；内容本身在持久卷/对象后端 |
| LangGraph局部检查点 | 成组版本的PG checkpointer | 保存执行位置，RunCheckpoint保存已确认的整体引用 |
| Runner命令/attempt/回执、根映射和日志索引 | 本机SQLite＋受保护本机数据目录 | 真实设备执行事实；服务同步回执，不构成另一套聊天主库 |
| 页面读取投影/草稿 | Query cache；P4 IndexedDB | 按账号分区，只作为允许保留的数据缓存 |
| L1缓存与在途计算 | cachetools＋asyncio自有控制器 | 有界、依赖版本、当前授权复核；可全部丢弃而不丢业务事实 |
| 平台/私人/设备秘密 | CredentialStore backend / OS keyring | 仅引用进入SQL/模型；真实秘密不进入任务代码或浏览器缓存 |

数据库不是把1228种schema都变成表。常用查询/状态/索引字段结构化；提案、Manifest等JSONB也按契约验证。领域仓储通过UnitOfWork共享底层连接，不互相改对方事实。

## 2. 事务与CAS

- 单领域修改使用预期revision，更新成功后递增，0行更新返回conflict。
- `(主体范围, request_id/operation_id)`建立恰当唯一约束，相同ID不同参数拒绝。
- 状态、InteractionItem提交和Outbox在所属事务边界完成；seq按Run有序分配。
- 跨领域用已提交引用与确认回执协调，不宣称框架checkpointer自动提供分布式原子事务。
- AsyncSession不跨并行工作单元共享，连接池按进程和任务上限设置。[SQLAlchemy说明](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

Blob与SQL没有共同事务：先写不可变内容、校验持久回执，再提交引用。失败形成待清理孤儿，不广播可用成果；清理查引用、保留期限和当前访问，不能删用户项目根。

## 3. 持久待办和事件传输

主选SQL待办＋Outbox worker，使用短事务 `FOR UPDATE SKIP LOCKED` 领取待办。该机制适合多个消费者领取队列项，不能拿它当业务一致读或整项任务的长期锁。[PostgreSQL说明](https://www.postgresql.org/docs/17/sql-select.html)

长执行依靠Run租约/栅栏与心跳，每次提交/派发复核。NOTIFY是唤醒提示，超时扫描仍读权威表。外部动作可能已发生，消息重复必须由Tool/Runner幂等及对账处理。

SSE通过持久Event seq读取；cursor过旧时返回授权快照再接增量。取消和审批来自持久状态，WebSocket断线、SSE断开、任务取消是不同事实。

## 4. 向量与关键词

采用一个PostgreSQL实例的pgvector，避免首版另维护一个向量服务。表记录主体/资源范围、源版本、embedding profile、维度与删除/启用状态。重新embedding发布新索引修订，不混合旧/新模型向量。

权限先限定查询集合，回传前再次核验。近似索引可能在过滤后返回较少候选；主选早期授权集合精确搜索，规模增大后验证HNSW/iterative_scan、有界扩大与召回指标。[pgvector说明](https://github.com/pgvector/pgvector)

关键词链路包含工具ID/名称精确匹配、英语FTS、中文字符/子串召回。pg_trgm可辅助较长字符串模糊检索，短于三字符的中文请求不能只依赖trigram。RRF融合分数用于候选顺序，最终工具选择与能力差异仍由LLM处理。

## 5. 五层缓存

| 层 | 缓存内容 | key/失效要点 |
| --- | --- | --- |
| L0页面 | 已授权投影/允许草稿 | issuer/subject/workspace、数据revision；退出/切账号/撤销清理 |
| L1进程 | schema、配置内容、派生只读内容 | 自有Manifest、容量/字节上限；当前撤销另查，不把旧配置当授权 |
| L2持久派生 | 解析/检索/可复用只读结果 | SQL＋Blob；源Hash、parser、embedding、范围、时效和目标依赖 |
| L3上下文 | 片段集合/压缩结果 | source revision、purpose、窗口、指令/角色/技能版本；不复用失效事实 |
| L4提供方前缀 | 稳定规则/工具schema等输入前缀 | 实际provider/模型/输入顺序；以usage回执确认，不从相似度推断命中 |

缓存命中后仍核对当前访问和依赖有效性。single-flight只合并相同获准只读计算，等待者取消独立。操作幂等、当前进程、审批和未知外部写用账本处理，不能缓存一个“成功”响应绕过实际状态。

cachetools容器本身不是线程安全的，UAW负责并发锁与不可变结果。[组件说明](https://cachetools.readthedocs.io/en/stable/)

## 6. 两种权威部署profile

### 建议首版：服务端权威

Web静态站点＋同源FastAPI/worker＋服务端PostgreSQL/Blob；本机Runner主动WSS连接。用户通过账号找回会话，本机只保留需要的执行账本和允许的页面缓存。

断网可以显示已允许缓存的内容；不能自行启动第二套权威Run后在联网时盲合并。Runner在途执行依协议记录真实效果，回连后对账。

### 若D01选择首版本地权威

完整Python后端、PostgreSQL/Blob和Web部署在用户本机，Runner在同机运行但保持独立边界；账号云同步默认关闭。仍可调用获准远端模型，因此“本地权威”不意味着资料从不离开设备。

此profile需要本机数据库/升级/备份/安装验证。若之后要用SQLite替代全部业务数据库，必须新增并验证Repository、并发/迁移/向量能力适配；不能因为Runner已经用SQLite就认为替换完成。

同一工作区只有一个权威profile。切换属于显式迁移：冻结写入、对账未决效果、迁移版本/引用/保留规则、校验后切换；本轮不承诺已实现同步或迁移功能。

## 7. 开发、试用和执行环境

- 开发：uv环境＋前端pnpm＋Compose PostgreSQL，可选API/worker同进程方便调试；账本依然持久。
- 受控试用：API/worker独立进程，共用权威PG；Nginx同源入口，TLS/SSE/WSS、真实账号、持久卷及备份恢复验收。
- 本地native任务：真实用户项目授权，标明无OS沙箱时的实际范围。
- 受控Linux任务：非特权容器、必要只读基线/独立写区、资源与网络限制，不挂控制面秘密或daemon socket。
- 可选云任务：D09选定实际沙箱后端，再做同一Workspace port能力验收。

容器共享宿主内核，Docker依赖实际配置；面向强对抗多租户代码时需要另评估更强执行隔离，不能自动宣称当前模板满足。[Docker说明](https://docs.docker.com/engine/security/)
