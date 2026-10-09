# C-008：MS-T2e 最终向量索引与A接线要求

日期2026-10-08。实际`E:/UAW/.worktrees/tool / dev/tool`，固定开发基线`ms-i2h-start / f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8`。阶段源码`ba0d11ef4533e71ad8147d86abaef04bd07c114c`与接口文档`8ed211ecb11fb12a7e644d7809f8e7b5c3831a30`保留；最终源码：**`27fe04f22cf19f734f776da326e79dc52eb7b83e`**；实际验证见[C handoff](../../handoffs/C.md)。本包只返回现有DiscoveryResult，不执行工具或改变固定用户模型；没有公共schema/锁/迁移/组装/API/flags变更。

## 固定入口与可信组装

阶段异步签名保持；最终仅增加可选`index`：

```python
ToolRetriever(registry: ToolRegistry, access: ToolAccessPort, *,
    mode: Literal["lexical-only", "semantic-required"] = "semantic-required",
    embeddings: ToolEmbeddingPort | None = None,
    index: ToolVectorIndexPort | None = None)
await retriever.discover(query: str, categories: list[str],
    max_candidates: int, ctx: TrustedExecutionContext) -> JsonObject  # DiscoveryResult
ToolFacade(registry, access=None, *, ..., retriever: ToolRetriever | None = None)

SQLiteVectorIndex(path: Path, *, max_bytes: int = 16 * 1024 * 1024,
    namespaces: int = 8)
class ToolVectorIndexPort(Protocol):
    async def read(self, plan: IndexPlan) -> tuple[tuple[float, ...], ...] | None: ...
    async def replace(self, plan: IndexPlan,
        vectors: tuple[tuple[float, ...], ...]) -> None: ...
    async def invalidate(self, namespace: str) -> None: ...

ToolRegistry.unregister(tool_ref: JsonObject, *, expected_revision: int) -> int
```

unregister仅为可信内部admin/composition提供CAS卸载，与原register一样没有新增HTTP/模型入口；卸载后索引不能保持工具安装或获权。旧Facade无retriever时沿用原小目录逻辑，旧invoke/result/reconcile不改；Facade/retriever必须共享同一个实际Registry。ModelToolSet的非空来源验证继续走A已发布当前adapter。

```python
from pathlib import Path
from uaw.tool.facade import ToolFacade
from uaw.tool.index import SQLiteVectorIndex
from uaw.tool.retrieval import ToolRetriever

# path由可信组装配置给出；禁止从模型request传路径或Embedding配置。
index = SQLiteVectorIndex(private_cache_directory / "tool-vectors.sqlite",
    max_bytes=16 * 1024 * 1024, namespaces=8)
retriever = ToolRetriever(actual_registry, actual_run_tool_access,
    mode="semantic-required", embeddings=admin_bound_actual_embedding_adapter,
    index=index)
facade = ToolFacade(actual_registry, actual_run_tool_access,
    retriever=retriever)  # 保留A当前invoke/result其他依赖的既有构造参数
result = await facade.discover({"query": "检查所给文本的长度",
    "categories": ["text"], "max_candidates": 8}, original_ctx)
# result.payload仍仅tools/agents/registry_revision，LLM选择工具。
```

只要没有实际embedding提供方，这个semantic-required组装明确unavailable；不生成hash/random向量，不自动添加提供方、切换模型或回退词法。显式`mode="lexical-only"`可省略embedding与index，只进行词法检索，使用同样当前权限/目录复查；该模式配置本身明确算法，现有公共DTO没有新增mode字段。无index时semantic-required仍可直接召回，向量未持久化；cache miss重建actual vectors，cache损坏不静默回退。A可按C-007实现真实ToolEmbeddingPort，NumericalEmbedding仅为测试数值协议，不能作为产品adapter。

## 实际数据边界与排序

- 实际Registry固定revision及全部immutable entries，在任何检索前消费当前ToolAccess，按完整role/categories、scope能力交集/deny、flags、环境和active Tool provider过滤。registry最多128工具，query最多8192 UTF-8 bytes，max_candidates沿用CandidateLimit 1..32；向量维度1..4096。候选总JSON还受现有canonical的64KiB/结构边界，不扩大公共容量契约。
- 只投影允许工具的原id/description/categories规范JSON；描述是资料，embedding adapter不得按其指令操作。未允许工具的内容不传embedding；用户query原样仅用于当次请求，不入索引。
- `EmbeddingBinding`固定provider Ref、模型configuration Ref（均version/content_hash）、dimensions及`tool-projection-json-v1`。`EmbeddingBatch`严格对应actual UTF-8 text SHA256/顺序与batch数，每一向量是有限数值tuple、正确维度、非零有限norm。数值拒绝NaN/Inf/bool/错误维度/顺序/绑定/摘要，无hash/random语义替身。
- 词法沿用casefold、id/description子串匹配；向量cosine>0召回，按相似度降序；两路reciprocal rank fusion k=60、等权，score≤1，最终按score降序、tool id/version确定排序。只返回ToolCandidate原Ref/description/input_schema/effect/score，agents=[]，没有执行建议授权或自动挑选工具。
- 当前Access完整快照和固定Registry在embedding/current/index await后重新读取，并在返回前复查；即使某权限/flag变化不影响当次工具集合，也拒绝旧快照。索引等待后复查embedding current，变化时不发送query/描述；embedding调用和索引更新后再校验provider/model绑定。整体asyncio期限约束等待，超时明确deadline_exceeded或retrieval_interrupted，无结果；异步取消传播。没有跨请求授权缓存。

## SQLite缓存格式、原子性和容量

`IndexPlan(namespace,binding,documents)`由retriever生成；namespace是完整Principal含kind/session的SHA256，documents严格含工具完整Ref/hash、Tool provider Ref及投影text_hash，embedding binding另存。拒绝带location/access_scope的索引Ref；不保存owner明文、用户query/正文、凭据、ToolAccess/批准结果、调用响应或ToolResult。元数据只固定向量可复用的实际资料来源，不能将namespace或文档成员当权限。

SQLite只有结构化`snapshots(namespace,metadata,checksum,generation,count)`与`vectors(namespace,position,value)`；vectors为网络字节序IEEE754 float64 BLOB，不是pickle或宽泛业务Object。user_version=1/application_id固定，摘要绑定整个metadata与按位置vector bytes；仅用于缓存损坏检测，不冒充来源认证/权限签名。读取数量最多128，按位置完整、规范metadata相等、checksum/维度/有限数值全部复查。元数据不匹配为明确miss；当前registry决定重建。缓存每次命中仍调用实际embedding生成当次query向量，query绝不持久化。

单个完整generation在BEGIN IMMEDIATE事务中替换；读事务固定一个完整generation，删除用外键级联，失败回滚保留原完整generation。多个实例/进程使用SQLite自身writer锁；旧写者即使迟到，当前计划metadata不匹配也不会被当作当前索引。默认8 namespace，允许1..32，按generation确定驱逐旧namespace；每namespace只保存一份generation，权限/工具/版本改变后的重建会替换旧资料集。显式invalidate删除该namespace；已不允许/卸载的工具不因残留缓存行重新变为候选。

max_bytes允许32KiB..16MiB。数据库只占预算约一半（4096 page对齐，另为rollback journal/header预留至少8KiB或总量1/64），PRAGMA max_page_count硬限文件增长；journal_mode DELETE不积累WAL，SQLite阻塞操作在to_thread中，busy timeout 2秒。规范资料及向量有明确预检，真正SQLite空间耗尽也整体回滚并明确失败，不返回部分向量。实测默认配置可保存128个4096维向量，文件容量保持限制；小配置可能明确index_full/index_invalid，不静默扩大容量。admin传入私有cache path仅归可重建缓存，D01普通业务状态库权威没有改变。

异步取消后已在线程运行的有限SQLite事务可能完成或回滚；只能留下可重建索引资料，不会返回候选或产生Tool动作/发送权。未识别/超限/损坏库明确index_invalid，不自动删除不明文件；A要显式清理可信private cache并重建，不能从索引读取安装、权限或业务状态。原始资料始终以实际Registry/当前Access为准。

## A待接线与消费方影响

1. A把可选retriever注入现有ToolFacade，并提供实际已发布RunToolAccessSources或等效当前权威；需要完整主体/session、Run/固定用户模型/范围/role/policy/flags/provider复查。缺权限port或无效返回明确unavailable/protocol failure。默认生产flags与Runtime绑定不变。
2. A/管理员提供实际ToolEmbeddingPort current/embed，独立验证当前embedding provider/model/版本/撤销、认证、其自身权限/预算计费和deadline/cancel。C不消费Model私有ProviderRequest、不调用网络API、不创建embedding策略或替换用户固定模型。D06及embedding语义质量仍未确认，数值测试只证明计算/排序/协议。
3. A可信组装配置私有cache path、容量/namespace数与显式模式。若需公共配置、port/schema/依赖/flag，先发布兼容基线；本包标准库SQLite无新增依赖或公共DTO缺口，不直接改任何公共文件。
4. Stage接口可直接使用；最终新增optional index及内部CAS unregister不强制旧调用方改构造。缓存不登记工具，ModelToolSet依旧需要A真实当前工具来源，检索不绕过invoke的审批/预算/资源/结果核对。
5. 本包完成后停止，完整MS-T2/P1-03、Agent整链与生产语义效果仍待A集成验收；不读其他worker开发分支，D01/D03/D06不自行裁定。

## 实际验证与失败记录

最终218单元通过（原162＋检索24＋索引32），0失败/错误/跳过。Ruff通过、51文件format check、25源码Mypy通过。真实SQL按不同节点去重124项通过：原100项调用/结果回归首轮99passed/1failed，既有并发调用触发20秒wait_for超时；在不修改原模块、超时或断言的情况下定向复跑该3项模块，3passed，其中并发15.38秒。新增检索SQL最终24passed；不是一次124项完整运行。原100项SQL全部保持基线字节，不因首次超时降低验证标准；首轮及复跑实际回执同时保留。

阶段首次185passed/1failed来自测试query中短词a被原词法子串规则命中，修正query后186passed；阶段Mypy类型标注也已修复，initial-*回执保留。新增SQL初始21passed、补索引await撤销/期限取消后24passed，最后容量/缺权限边界冻结后的最终24项再次84.97秒通过。SQLite持久文件、跨实例/新Python进程重启、原子并发、容量回滚和损坏测试使用实际标准库SQLite；SQL使用实际注册Role/RunToolAccessSources/Policy/配置/Budget读，embedding为受控已知数值、不证明语义质量或产品认证。

C独立55434、own Docker project/volume、私有生成DB env，按锁alembic upgrade head成功。ignored回执：`tests/.artifacts/C/MS-T2e/{unit.xml,unit.txt,sql-original.xml,sql-original.txt,sql-original-recheck.xml,sql-original-recheck.txt,sql-retrieval-initial.xml,sql-retrieval-progress.xml,sql-retrieval-final.xml,sql-retrieval-final.txt,ruff.txt,format.txt,mypy.txt,migration.txt,environment.json}`；阶段回执`tests/.artifacts/C/MS-T2e-stage/`。没有凭据/URL、A配置或共享evidence写入，没有当前未通过用例；原20秒超时提示环境耗时波动，应由A整链测量评估，不宣称生产延迟保证。真实embedding与语义质量/Agent/生产产品回归仍待A/管理员。
