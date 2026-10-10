# MS-I2l：A 已登记文件来源到 C 有界集合 / Context

内部 Python 消费，不新增公共 HTTP DTO、正文 Blob、工具尝试或授权。实现位于 `src/uaw/run/file_context.py`，沿 C 的实际 `FileMaterialReaderPort` 和 `FileMaterialSetAdapter`。

## 构造和调用

```python
origins = FileContextMaterials(records, authenticated_controller, actual_file_tool.materials)
fragment = await origins.register(
    original_action_id, original_execution_context,
    authenticated_service=authenticated_controller,
)
reader = RegisteredFileMaterialReader(origins)
material = await reader.read(original_complete_material_ref, current_context)
readings = await origins.read_many(original_fragment_refs, current_context)
```

register 必须当前控制器，先由 C export 原材料；同一短 SQL 事务保存原 ctx、fragment/material/observation Ref 和 material ID→fragment Ref 索引。索引只用既有 Ref 合同，不保存正文；冲突拒绝、不改原来源。事务结束后仍调用当前 owning Reader，重放也不能跳过数据授权。

read_material 首个 await 前冻结完整 wire，按当前 Principal 读取 owning 索引，再复核原 fragment/ctx/材料 pin。当前用户完整会话、Run/Agent/Scope、能力与模型 Ref 必须等于原作用域；当前 deadline 不能延长原期限。只允许 operation/trace/attempt/预算调用标识不同，原调用 ctx 来自登记，不从传入 Ref 猜测。随后沿 C Reader 用原 attempt 读原签名 journal；返回后复查材料、fragment、observation 和索引。旧材料没有索引时明确缺项，不能自动扫描或猜原 ctx；原 register 的授权重放可以补登记。

read_many 输入1–8个原 fragment Ref tuple，C 保持每项原顺序和全部 refs，总量16384字符/65536 UTF8 bytes。C 在全部读取后再次顺序 owning read；A复核对应 fragment 和原登记。任一撤销/版本/主体/模型/期限/总量不满足则整体拒绝，没有部分返回。FileAwareContextInputs 的混合批读接此路径，再与普通材料按原顺序组合；文件 Reading 一律 `trust=external`、`kind=material`、不提升为必须遵守的指令。

## 错误和生命周期

- 精确 hash/fragment/index 改变412；当前作用域或期限扩展403；批数量超界413。
- Reader/控制来源缺失503，原 owning Reader 撤销/缺项错误透传。注册来源冲突409。
- RegisteredFileMaterialReader.export 明确不可用；注册只能由上述控制器入口完成。
- 无自有进程/任务/缓存/文件句柄；数据库、原 Tool Reader 生命周期由 Container 管理。对象重建不新读取文件，合法 recover 仍允许复核原回执；不能把 recover 误当新 command。
- 顺序复核不是跨模块全局原子权限快照；最终复查后撤销不能收回已经返回的字节。后续消费需再走当前 Reader。

## 验证边界

35不同聚焦节点最终通过：7新 A owning-origin SQL，1原 A/C Bridge SQL兼容，27 C集合单元。实际SQL/签名/journal/临时文件单次读取；管道、native肯定来源和当前测试数据权限受控。首轮空字段序列化错误、合法 recover 断言/非法模型Ref测试问题与中断均保留，不称真实本人目录/固定模型文件整链通过。Ruff与194源码 Mypy通过。

真实本人账号/设备第一次确认已另有 journal 与实际 readonly helper ready 回执；当次 finally 已清理临时角色keys/进程，它不是持续有效的文件根。root Ticket/on_connected本人选择、父端当前通道/根/文件路线及 localhost 生产入口仍待M2/M3，默认flags关闭。原学术Run最新只读状态因原Web会话到期已 failed，3次原模型调用和成果保留，不重发或改写失败成接受。
