# MS-T2i M1：有界多资料消费固定接口

Session C，2026-10-10。目录 E:/UAW/.worktrees/tool，分支 dev/tool。
远端正式 DISPATCH 已核对；固定基线 ms-i2l-start / 8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0。
M1 源码 ee6645e928bbe7db292de2f1cf053e7acbb07cd4；本阶段 read 明确503，M2继续完成实际消费。

```python
from uaw.tool.providers.file_material_set import (
    FileMaterialSetLimits, FileMaterialSet, FileMaterialSetAdapter,
)
limits = FileMaterialSetLimits(max_characters=16384, max_utf8_bytes=65536)
adapter = FileMaterialSetAdapter(current_owning_reader, limits=limits)
materials = await adapter.read((original_material_ref_a, original_material_ref_b), current_ctx)
# materials.materials: tuple[FileMaterial,...]，保持原顺序，不拼接、不截断
# materials.refs / characters / utf8_bytes：原完整Refs及集合实际正文总量
```

输入严格1–8完整Ref tuple，重复拒绝。两界限只允许更小正整数，bool不允许。
冻结集合保留每项原FileContent/Usage/owner和command/receipt/provider/call/observation/fragment/material Ref。
没有公共DTO、集合持久正文缓存、注册或新授权，构造/消费不执行文件、不reserve/dispatch/retry。
无自有句柄、任务、连接，adapter无需close；注入Reader生命周期由A控制。

A owning Reader须从可信已登记的每个material来源解析原attempt和原ctx，并以传入当前ctx重新检查当前主体/会话/范围/权限，最终调用已有单文件Reader。一个FileMaterialAdapter只读自己的原attempt，不能将新ctx改成其他attempt来伪造权限；多来源路由归A，不从Ref猜ctx/provider，不注册受控测试来源。
C逐项read，读取全部以后按输入顺序再次read并逐项比较完整冻结值、owner和原Ref，任何撤销/变化/缺项/超界整体失败。
不承诺跨模块原子授权快照；最终复核后撤销不能收回已返回字节。

A现有桥仅whole≤16384字符/64KiB UTF8；lines/cursor/非空project仍不可用。费用恢复独立原计划，不由集合读取触发。
M1 ruff check/format通过；实际SQL和完整M2验证后续记录，不将旧369/81当本轮结果。
