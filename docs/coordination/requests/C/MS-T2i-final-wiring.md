# MS-T2i 最终接线：有界原资料集合

Session C，2026-10-10，E:/UAW/.worktrees/tool，dev/tool。
固定基线 ms-i2l-start / 8781da56fb0d9de8b1f6d39e2325c5fac6c74ea0。
远端 origin/integration 的正式 DISPATCH 已只读核对，未合并浮动integration。
M1 ee6645e928bbe7db292de2f1cf053e7acbb07cd4，M2 47bf1269de3a20f0150e88055662c8962ec5c774。
最终源码：44122503ecb60a4036a990eeb20e7340b9618394。验证：397不同单元＋46不同真实SQL最终通过（新增28单元/20SQL；原受影响26SQL）；全部最终节点0failure/error/skip。不是单次397/46运行。。

## 已实现签名和调用

```python
from uaw.tool.providers.file_material_set import (
    FileMaterialSetAdapter, FileMaterialSetLimits,
)

# owning_material_router 必须由 A 登记来源、核对当前数据授权；Ref不是权限。
reader = FileMaterialSetAdapter(
    owning_material_router,
    limits=FileMaterialSetLimits(max_characters=16384, max_utf8_bytes=65536),
)
result = await reader.read(original_material_refs, current_ctx)
for material in result.materials:  # 固定原tuple顺序；分别消费，不拼接正文
    text = material.text
    provenance = material.fragment_ref
    observation = material.observation_ref
    original_usage = material.usage
```

`original_material_refs` 为1–8完整Ref tuple，kind=content，version与content_hash必须来自原source。
不接受list、裸dict、缺hash，精确wire重复409；未提供Reader503。
两个界限默认合计16384字符/65536 UTF8 bytes，只允许更小正整数；bool拒绝。
越总量413，无截断/Unicode规范化/正文拼接/部分返回。保留每项原FileContent/Usage与所有完整Refs。
`FileMaterialSet.materials` 是冻结tuple；`.refs` 为原顺序完整Ref的新副本；`.characters/.utf8_bytes` 是实际正文总量。
没有新wire DTO、SQL命名空间、集合正文Blob/cache或全局注册；不需要close，无自有连接/任务/文件句柄。

## A owning Reader 路由边界

构造可直接用现有 `FileToolBindings.materials` 处理一个原attempt；跨attempt需A实现已登记来源路由的FileMaterialReaderPort。
A不得用Ref猜原ctx/provider或把调用方ctx的attempt_id替换来获得权限。登记表/recipe只提供原来源，不是准入。
传入current_ctx后，owning Reader应复核当前主体/会话/范围/模型来源与数据权限，读取固定原attempt的签名journal及现有单文件Reader。
C不读Context/Agent表、不修改其recipe/assembly，不代建production路由。当前远端本包仅AD-contract和packages，未发布新production多来源Router；明确pending，缺Reader503。
本轮已消费基线实际A RegisteredFileBridge与FileToolBindings.materials，原完整call/ctx/provider、command_ref/receipt_ref与真正签名检查保持；其测试传输/current源仍受控，不是installed/真人授权或固定模型整链。
生产桥继续只whole≤16384字符/64KiB UTF8；lines/text_span/cursor/非空project仍不可用，不从重读拼原snapshot。

## 原来源与返回前复核

输入在首个await前冻结完整wire，含location/access_scope，不丢version/hash。
逐项owning read，精确绑定material_ref与当前Principal；逐步检查合计界限。
全部读完后按原顺序再次逐项owning read，比较整个冻结FileMaterial，含原Usage/owner/provider/call/command/receipt/observation/fragment/body。
依赖撤销、缺项、错版本、跨主体/provider、证据改变使整个调用失败，只有最后全部通过才返回冻结集合。
C只调用read，从不调用export/execute/open/reserve/dispatch/retry，不新attempt；CancelledError与依赖异常直接传播，无部分输出。
这是连续当前来源复核，不承诺跨模块原子授权快照；最终复核之后的撤销无法收回已返回字节。消费方后续复用必须再调用当前owning Reader。

## 摘要、恢复和费用

`material.file_hash` 是原同一次执行完整文件的SHA256；`fragment_ref.content_hash` 是实际选中正文UTF8的SHA256；`material_ref.content_hash == raw_result_ref.content_hash` 是规范FileContent JSON的SHA256。whole文本时full/fragment可相等，不借相等合并证据层级。
保留原command_ref、实际签名runner_receipt_ref和observation_ref；集合不重新计算快照或制造新set receipt。
回复丢失/进程重启只沿已保存原Refs顺序读同一原来源，无新发送/文件打开。unknown来源不可用，原额度仍保留，不换attempt。
数据撤销/原Run取消/执行role不可用与费用清理分别处理。按当前数据权限决定正文可读；原已接受Usage和固定结算计划由现有 `recover_file_accounting` 独立恢复，集合读取不调用BudgetService/settle，也不由pending推导零费用。
不持有Tool事务锁调用Reader/BudgetService。恢复读成功不是新执行权，集合读成功不是工具/Task完成或Artifact接受。

## 本轮实际验证和保留记录

回执根 ignored `tests/.artifacts/C/MS-T2i`，独立端口55434；`. ./ops/start-dev-db.ps1 -Session C`、锁定环境alembic upgrade head成功。
完整命令/每节点最终去重与原失败见 verification-index.json；静态ruff/82文件格式/mypy34源码与48新增节点collection单独记录。原单元全模块396通过，加最终集合28中新增八来源边界1个，去重397。SQL原首轮1、主批次13通过/2失败、A桥3、原兼容26；版本变化1通过，UTF8/费用修复各1通过，去重46。
首次直接pytest.exe启动缺tests imports，改为 `.venv/Scripts/python.exe -m pytest`。
首版UTF8测试输入实际56000 bytes，未超过默认65536；显式收紧到50000以独立验证字节总量。一次修复遗漏limits导入也保留原回执，补回并复核。主批次另一失败把取消前后账本整体比较，取消实际改变revision/cancel_requested；改为取消后基准，独立费用恢复复跑通过。运行实现未改，所有失败XML/txt保留。
旧MS-T2h 369/81和更早219SQL不计作本轮新运行；最终按本轮实际XML去重，只报告本轮受影响复跑范围。

## A接线与整链验收

A注入真实已登记原来源路由及当前数据授权，Context每项仍external低信任材料；Artifact沿原观察/片段Refs引用，不用集合成功推定接受。
A/D提供actual installed/native/root/channel/current key来源，本人目录与任务接受仍由本人完成；缺源503，不注册受控Reader为产品能力。
共享schema/ports/锁/flags无需本包变更，未更改Context/Agent/composition或固定用户模型。后续跨模块消费者和汇合全量由A执行；本包完成后停止，不扩完整MS-T2。
