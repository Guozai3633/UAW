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

## M2 实际消费阶段（连续推进M3/M4）

源码 47bf1269de3a20f0150e88055662c8962ec5c774；上述构造和调用签名不变，read已实现。
输入在任何await前冻结完整wire；逐项读取并提前拒绝总量，所有项完成以后按相同顺序逐项owning read并比较整个冻结FileMaterial。Reader响应必须绑定精确Ref和当前Principal，完整证据/原attempt/provider的来源核验仍由owning Reader执行。异步取消和依赖异常原样传播，不包装成部分成功，不缓存正文，不调export/execute/open/预算。

错误：非法tuple/缺hash/非content为422；重复409；缺Reader503；错Ref/owner409；原值变化412；超总量413。owning Reader当前数据撤销或缺源按其原错误传播。所有失败无partial输出；不是多个模块事务原子授权。
27新单元通过，mypy本模块、ruff通过。首次直接pytest.exe缺仓库imports产生收集失败，已保留m2-unit.xml/txt；修正为本工作区python.exe -m pytest后m2-unit-fixed.xml/txt实际通过，不修改公共测试配置。真实SQL继续，同包不等A集成。

A桥接样例：注入按已登记来源路由的FileMaterialReaderPort，传入当前ctx，tuple里保留每个原完整material Ref。分别用material.fragment_ref/current.text给低信任Context，full-file hash、fragment hash和material JSON hash分开；不将集合读成功当Task完成。不扩大whole/lines/cursor/project支持。
