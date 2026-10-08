# MS-C4：可选纯计算缓存接线与待执行 SQL

日期：2026-10-08。基线 `ms-i2e` / `ba2f3b0d9417e6d695eaa74c2f766217c98b01f1`。
本提案仅说明 A 的内部可选注入；没有公共 schema/port/配置/依赖缺口，也不申请自动开启产品缓存。

## 最小接线

保持现有 `ModelInputPort.resolve(ref, ctx) -> ModelPrompt` 和 `TokenCounter.count(reading) -> int`。
B 在 `ContextComponents` / `Selector` 和 `GenericModelInputs` 构造器增加可选 `cache=`。
A 仍先接入真实通用 authority、Reader、固定模型窗口及取消来源，并保留 `ms-i2e` 输入路由。
没有这些依赖时继续明确不可用，不能用理解专用模板或测试 tools/authority 替代。

```python
from uaw.context.cache import PureComputationCache
from uaw.context.facade import ContextComponents
from uaw.context.model_input import GenericModelInputs

# 下面变量必须是 A 接入的真实 port；仅展示构造方式，不创建生产来源。
def make_inputs(cache=None):
    generic = ContextComponents(
        readers=registered_readers,
        cancellation=current_cancellation,
        rules=registered_purpose_rules,
        models=fixed_model_window,
        repository=context_repository,
        authority=current_composition_authority,
        cache=cache,
    )
    return generic, GenericModelInputs(generic.composer, cache=cache)

pure_cache = PureComputationCache(max_entries=128, max_bytes=2 * 1024 * 1024)
generic, inputs = make_inputs(pure_cache)
prompt = await inputs.resolve(snapshot_ref, trusted_context)
```

同一实例可供两个 B 纯计算入口使用，但主体/完整 scope/Run/模型/权限始终属于键。
`ContextComponents(cache=...)` 只给 selector 注入；`GenericModelInputs(cache=...)` 必须单独明确选择。
A 的当前 composition 未改，默认没有缓存。关闭示例：

```python
# 默认关闭：两个构造器都使用 cache=None。
generic_off, inputs_off = make_inputs()
# 若保留显式实例，把两个入口都注入 disabled；任一容量为零均关闭。
disabled = PureComputationCache(max_entries=0, max_bytes=2 * 1024 * 1024)
generic_zero, inputs_zero = make_inputs(disabled)
# 也可 PureComputationCache(max_entries=128, max_bytes=0)。
# 默认 PureComputationCache() 同样关闭。
```

自定义 counter 沿用既有 `name`/`count`，默认绕过估算缓存；如确认 count 是纯计算，可在具体实现提供非空字符串 `cache_version`，覆盖算法及全部参数。算法/配置改变必须推进该版本。键同时有 counter 类型、名称和 selector 持有的每个 counter 实例身份；替换 counter 不复用旧值。默认 ConservativeTokenCounter 的内部版本为 `1`，UTF-8 字节＋64 估算公式保持原样。

## 消费方影响和边界

- 每次先加载实际固定快照/InstructionSet、current authority/规则/来源/分类/能力集合/窗口，并校验完整 scope、epoch、依赖、取消与期限；原全部 await 后与最终复查保留。
- 只保存纯消息格式化/序列化的 bytes 和估算整数的 bytes；不保存 Reading、CompositionBinding、访问许可、ModelPrompt 授权结论或模型输出。tools 每次从当前真实来源解析/验证，不造空 tools。
- generic 键包含实际 snapshot Ref/全部 snapshot/request/instructions、binding 的完整键材料、全部实际 Reading 内容/Ref/分类/required/requirement_ids、ToolSpec/input/output schema、窗口三项数值、预留和算法版本。token 键也包含当前 selection/preserve/window/composition/full readings。
- 主体 kind/id 分区；完整 Principal（含 auth session）、Scope、Run、fixed model/capability/budget refs、agent/node 进入完整键。operation/trace/attempt/deadline 不属于纯输入身份；每次的取消/期限/授权仍必须通过。
- 无来源 hash、无 snapshot hash 或无法序列化完整键时绕过；同 ID/version 内容改变先由原读取校验拒绝。源码所有者仍维护原文、快照和政策。
- LRU 进程内淘汰，条目与字节均有上限；字节统计为 payload + 两个摘要的 UTF-8 字节，Python 容器额外开销由条目数限制，不能当作 RSS 精确上限。超大条目不存储，clear/进程结束后可重算。
- 缓存启用/读/写故障或不可解析的内部条目只触发重算；实际 Reader/authority/模型/计数器错误仍失败。miss 后没有在途合并。每次构造新的 ModelPrompt，缓存消息解析为副本，实际 tools 重新解析。
- 不改变 Model provider/native request 估算、Tool/权限/flags/预算/取消边界；不改变 D01/D03/D06。没有 provider prompt cache、模型 Token 减少或实际延迟收益主张。此包没有持久缓存、语义命中或产品配置。

## 实际回执和 A 的 SQL 复跑

B 本 worktree 单元 **174 passed**（原107＋新增67，零失败/跳过）；Ruff通过、格式19文件通过、Mypy11个B源码通过。受控重复输入，两次消息格式化仅1次；三个 Reading 的 count 合计3次，第二次新增0次。两次分别仍执行 Reader read 16次、authority.verify 4次、window.resolve 6次、rule provider 2次。仅报告实际本地纯计算调用次数。

B 的 `UAW_TEST_DATABASE_URL` 未配置；**35项 SQL 未执行**，含原24项（C2的9＋C3的15）和C4新增11项。跨目录209项收集成功、新SQL fixture dry setup plan成功不算SQL通过。A 已在 ms-i2e 接受C3原15项的历史回执保留，两处Ref/Windows兼容修复文件均与基线逐字节一致。

新增模块 `tests/integration/context/test_cache_postgres.py` 与单元 `test_cache.py` 名称不同；实际SQL用例覆盖 warm cache重复/变异、规则/工具/材料/epoch变更、实际政策撤销、实际Run取消、实际原文删除、清空/新缓存实例、窗口变化和跨Run。规则/工具/epoch authority是明确受控SQL fixture，原文/政策/Run/固定窗口用现有真实适配器；没有实际模型/Runner调用。窗口缩小用明确受控 wrapper。新实例不冒充新进程；原C3新进程恢复用例保留。

A 在安排的真实测试连接/集成提交运行：

```powershell
./.venv/Scripts/python.exe -m pytest tests/integration/context -q --require-postgres
```

按原随机主体清理，禁止 truncate/复制私有 `.data` 或凭据。随后由A执行Model路由、理解输入与整条链路回归，审阅/合入/处理公共冲突。缺通用生产依赖继续不可用；MS-C4只交付局部组件，不标P1-02/P4-04整轮accepted。
