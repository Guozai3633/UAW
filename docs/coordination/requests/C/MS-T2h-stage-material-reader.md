# MS-T2h M1：原文件资料 owning Reader 固定签名

实际分支dev/tool，目录E:/UAW/.worktrees/tool。正式ms-i2k-start/HEAD开工SHA b7b79b150470a80f37b28fd52a2177f6de5b3124，fetch/ff-only/锁依赖同步成功，保留MS-T2g提交与回执。
M1源码：5c8854c713c6a9aa1f265016f5d6e875688f10e2。

## A消费

`uaw.tool.providers.file_material.FileMaterialReaderPort`：

```python
async def export(action_id: str, ctx: TrustedExecutionContext) -> FileMaterial: ...
async def read(material_ref: Ref, ctx: TrustedExecutionContext) -> FileMaterial: ...
```

M2实现`FileMaterialAdapter(source: FileReceiptStore | None, *, limits=FileMaterialLimits())`。
source必须是该完整原ToolRef/provider绑定的FileReceiptStore，装有真实bridge/current data access/signatures/verifier；缺来源503。export只能读原attempt观察、原ProviderReceipt/原FileContent；read必须验证准确material_ref和完整当前ctx/数据权限。SQL或Ref本身不是权限，恢复不能走新执行gate。不给调用者new open/send/reserve/retry权。

FileMaterial为内部不可变Python值，content/usage/owner/refs使用既有FileContent/Usage/Principal/Ref严格副本；不是公共wire DTO，不向schema或HTTP增加授权字段。属性content/text/file_hash、usage/owner、material_ref/observation_ref/fragment_ref/command_ref/runner_receipt_ref/raw_result_ref/provider_ref/call_ref。content只含实际selected FileContent，不含原完整snapshot或绝对目录。调用者修改返回dict/model不影响冻结字节。值缓存不能授权后续消费；A的Context/Artifact每次消费需通过read(ref,ctx)当前owning Reader。

默认FileMaterialLimits为16384字符/64KiB UTF-8；显式更小范围拒绝，绝不截断、拼页、Unicode/换行规范化。实际A/D RegisteredFileBridge目前仅whole，拒绝lines/text_span/cursor，最多16384字符和64KiB字节；C不扩生产能力。原snapshot只由同次执行签名whole回执获得，恢复不能重读补全。

## 来源与费用

导出保留准确观察Ref、原call/provider/command/receipt及actual selection。FileContent.content_hash是完整原文件hash，fragment_ref是实际片段UTF-8hash，material_ref是规范FileContent字节hash；三者不得混用。只持久已有具名DTO和实际blob，不扩EffectRecord或自造Object正文权限。

原read_observation/read_raw/read_outcome继续当前权限及真实原签名证据核对。数据撤销/root/device/key/session版本变化后不得消费material缓存；取消后数据是否可读按当前数据许可，不能当新执行权。既有recover_file_accounting仅重放已接受原Usage/固定计划，在当前BudgetState/Budget权限下独立清账，不读正文/文件或新增观察。

A负责实际Model/Context低信任资料分区、Artifact/Verification引用、生产设备/root/channel来源及完整Task结论；C不改Context/Agent/公共契约。M1无公共DTO改动请求；如需要跨HTTP资料协议，由A设计具名DTO后发布基线，不能把内部FileMaterial或snapshot直接序列化成产品正文。

M1验证：6单元通过，实际字节副本/不可变性及边界；Ruff/Mypy通过。回执ignored tests/.artifacts/C/MS-T2h/m1-unit.xml/txt。继续M2/M3/M4，不等待整链，不把受控Reader当真人授权。

## M2可接线源码与具体构造

M2源码54d474e2f6492bd5877df0cfb4ba358ab3cf867d（原Tool369单元通过，Ruff/Mypy33源码通过）。实现FileMaterialAdapter(source,limits=FileMaterialLimits())；source是`assemble_file_tool(...).receipts`的专用FileReceiptStore。原A桥无需改签名：`reader=FileMaterialAdapter(binding.receipts)`；`material=await reader.export(original_action_id,original_ctx)`；后续`await reader.read(material.material_ref,original_ctx)`。缺生产数据权限/routes/pipe/key时503，不新建Source或Reader替身。

正文`material.content`既有FileContent，`material.text`精确原片段；位置来自原selection，metadataRefs从该原attempt证据核对导出，整体/片段/资料canonical哈希分开。当前权限和原journal在命名CAS持久化之后再次读取，记录不能变成授权。原Usage保持pending未知维度，费用入口不被资料导出调用。

内部持久行tool.file.material.{refs,observations,fragments,commands,receipts,providers,calls,owners,usages}只用已有Ref/Principal/Usage，正文沿原FileContent blob。没有新公共DTO、迁移、依赖、Object授权字段。真实SQL已启动55434，初次fixture试图修改既有frozen Location模型而失败，已改成wire副本修改并保留初轮回执；本阶段不计SQL通过，继续M3/M4和A桥样例。
