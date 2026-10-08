# C-007：MS-T2e 阶段检索接口与A接线

日期2026-10-08，实际`E:/UAW/.worktrees/tool / dev/tool`。干净fetch/ff merge后HEAD与`ms-i2h-start^{commit}`一致：`f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8`；uv frozen检查91包，公共锁未改。阶段源码：**`ba0d11ef4533e71ad8147d86abaef04bd07c114c`**。前两里程碑交付后继续同包索引和独立SQL，无须等待集成。

```python
ToolRetriever(registry: ToolRegistry, access: ToolAccessPort, *,
    mode: Literal["lexical-only", "semantic-required"] = "semantic-required",
    embeddings: ToolEmbeddingPort | None = None)
await retriever.discover(query: str, categories: list[str],
    max_candidates: int, ctx: TrustedExecutionContext) -> JsonObject  # DiscoveryResult
ToolFacade(registry, access=None, *, ..., retriever: ToolRetriever | None = None)

@dataclass(frozen=True)
class EmbeddingBinding:
    provider_ref: Ref  # provider kind, required fixed version/content_hash
    model_ref: Ref     # configuration kind, required fixed version/content_hash
    dimensions: int   # 1..4096
    text_version: str = "tool-projection-json-v1"
@dataclass(frozen=True)
class EmbeddingBatch:
    binding: EmbeddingBinding
    text_hashes: tuple[str, ...]  # SHA256 actual UTF-8 texts, order preserved
    vectors: tuple[tuple[float, ...], ...]  # finite, correct dimension, nonzero norm
class ToolEmbeddingPort(Protocol):
    async def current(self, ctx) -> EmbeddingBinding: ...
    async def embed(self, texts: tuple[str, ...], ctx) -> EmbeddingBatch: ...
```

A可信内部接线样例：

```python
retriever = ToolRetriever(registry, actual_run_tool_access,
    mode="semantic-required", embeddings=admin_bound_actual_embedding_adapter)
facade = ToolFacade(registry, actual_run_tool_access,
    retriever=retriever)  # 其他真实invoke/result依赖沿用既有组装
result = await facade.discover({"query": "检查所给文本长度",
    "categories": ["text"], "max_candidates": 8}, original_ctx)
# 只返回现有DiscoveryResult候选，LLM选择；不调用工具或切换用户模型。
```

可明确配置`mode="lexical-only"`而省略embedding。默认Facade没有retriever时完全沿用原小目录行为；显式semantic-required缺提供方/无效向量直接unavailable，不静默降级。本包没有添加真实网络adapter、模型/embedding配置、产品目录/flags或公共DTO；D06来源由A/管理员提供。

固定registry快照最多128工具；query最多8192 UTF-8 bytes，CandidateLimit沿用1..32。先当前role/category/权限/flags/环境/active provider过滤，再将允许工具id/原description/categories的规范JSON投影交给embedding；未允许描述不外发。query保持原样且不作为指令。输入/返回批次严格校验provider/model/版本/维度/文本规范版本、actual text SHA256/顺序、有限数值和非零向量。词法使用现有casefold/子串计分；向量cosine>0召回，reciprocal-rank fusion k=60、两路等权、score范围0..1，按score降序及tool id/version稳定排序；不是语义质量评价或执行授权。

每个embedding await后及返回前重新读取当前ToolAccess/Registry/embedding binding；任何工具修订/卸载、权限/flags/provider变更、取消/期限或固定ctx变化都不能返回旧候选。整体期限约束异步等待，异步取消向调用方传播。实际current adapter须独立核查完整主体/session、Run/model/scope、提供方可用/撤销/计费；不得由query/ctx回显冒充授权，固定用户模型不替换。

阶段验证：**186单元通过（原162＋新24），0失败/错误/跳过**；Ruff通过、24源码Mypy通过。首次测试查询中的短词a意外命中原词法substring，导致预期纯向量score错误；修正为明确未命中字串，初始185passed/1failed和类型标注失败回执均保留于ignored`tests/.artifacts/C/MS-T2e-stage/initial-*`，最终unit.xml/unit.txt/mypy.txt/ruff.txt为实际通过回执。数值embedding是明示受控向量，不证明真实语义质量。C独立55434库已启动并alembic head成功，SQL在本包后半段实跑。

后半段索引将使用标准库SQLite、可信构造path和显式内部index port；只保存工具元数据绑定与向量，不保存用户正文/查询、凭据、授权结果或调用结果。缓存只是可重建派生数据，当前Registry/Access始终最终权威。完整MS-T2、公开Runtime/flags仍待A接受，本包不扩能力。
