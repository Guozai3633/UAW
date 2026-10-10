# MS-T2h：原文件资料 Reader 最终接线

最终源码3ed6ef3434c024d00e6e7794e5bace28914fe426（含M2运行实现54d474e）。全部369单元和81不同真实SQL最终通过，0最终失败/错误/跳过；首次失败和修复回执完整保留。实际分支dev/tool，目录E:/UAW/.worktrees/tool，正式固定基线b7b79b150470a80f37b28fd52a2177f6de5b3124/ms-i2k-start。MS-T2g原源码/交接/219SQL回执保留。

## A消费示例

```python
from uaw.tool.providers.file_material import FileMaterialAdapter, FileMaterialLimits

# binding为A的assemble_file_tool(...)，其receipts是原完整ToolRef/provider owning source。
reader = FileMaterialAdapter(binding.receipts)  # 默认16384字符/64KiB UTF-8
material = await reader.export(original_action_id, original_ctx)
# Context/Artifact之后再次消费时重新检查当前资料权限和真实原journal。
current = await reader.read(material.material_ref, original_ctx)
body = current.content     # 既有严格FileContent，实际原文/selection，不含完整snapshot
observation = current.observation_ref
fragment = current.fragment_ref
# A将body作为低信任原资料接Context recipe，规则不从正文升级；成果引用用准确Refs。
```

Reader只消费原call/spec/ctx/attempt；没有executor、预算reserve/dispatch/retry或文件open入口。读资料不以新执行gate/旧approval当授权；缺source/current data access/bridge/signatures/verifier返回dependency_unavailable。已有material SQL/Blob/缓存仍要重新调用owning Reader，不能拿well-formed Ref或旧snapshot自报owner/approved。

FileMaterial内部值只冻结已有FileContent/Usage/Principal/Ref的严格canonical bytes；属性content/usage/owner返回新的dict/model副本，冻结值不被消费方修改。text/file_hash、material_ref/observation_ref/fragment_ref/command_ref/runner_receipt_ref/raw_result_ref/provider_ref/call_ref可直接消费；没有snapshot/绝对目录/new authority字段。它不是新公共wire DTO，不作为model输入、HTTP授权对象或公共Object记录序列化。A需外部传输时统一发布具名DTO/C请求，不让C改shared/schema。

## 原证据与持久一致性

1. source.read_observation核对当前数据权限、原命令登记/journal、实际签名/完整snapshot/selection；原snapshot只来自同次原执行。source.read_raw从实际原blob读FileContent并重新验owning verifier。导出确认两者正文/Usage一致，不从Runner ok/HTTP/费用状态推正文成功。
2. FileContent.content_hash = 原整体文件SHA256；fragment_ref.content_hash = 精确返回片段UTF-8 bytes SHA256；material_ref.content_hash = 既有FileContent canonical bytes SHA256。不得用片段或资料信封hash替代完整文件hash。
3. observation_ref固定原command_ref/receipt_ref/owner/device/完整snapshothash/实际selection。命令/回执仍可经原Reader获取，不能凭content kind通用读取原设备资料。
4. Tool独占tool.file.material.refs/observations/fragments/commands/receipts/providers/calls/owners/usages，分别使用既有Ref/Principal/Usage，正文沿原FileContent blob，不复制新正文权威或私有Object。短SQL CAS原attempt固定，命令/回执/观察/归属/Usage变更冲突，不覆盖“修复”旧行。
5. CAS发布前后均复核实际来源和当前权限；Bridge/Reader/Blob/预算调用均在Tool事务锁外。重复/read/new process恢复不execute、不新开原文件，文件变化/删除不能重读补快照。发布回复丢失只读原refs/原来源，不换request/attempt。

默认consumer界限16384字符、64KiB UTF-8，显式更小界限拒绝而不截断/拼页/规范化。FileMaterialLimits可在C层显式采用不超过既有64KiB的未来consumer范围，但不授予生产桥新能力。当前实际A/D RegisteredFileBridge whole≤16384字符，lines/text_span/cursor明确503，没有完整原snapshot来源不能拼接或重读补全。非空project_id仍按原公共准入拒绝，C不自行解禁。

## 数据权限与费用

material正文读取和原fees结算分别授权。数据/root/device/key/session/scope/model/provider版本撤销后read/export拒绝，即使旧material已缓存/SQL记录仍存在。已授权返回的值不能撤回调用者已看见的字节；它不代表后续自动读取的授权，A需要每次Reader复查。

取消/期限结束不成为新准入，原数据是否可读由当前owning authority决定。旧recover_file_accounting(ledger,budgets,original_ctx)只消费当前BudgetState/Budget和已接受原Usage/已有原固定计划，不读正文/native root/journal，不新增账单观察或费用推断；数据/root/key撤销后仍可重放原账务回执。pending Usage未知money继续held，原明确金额计划不变。材料导出不调用ToolResults完成/费用服务，不声称Task通过。

## A/D缺口与组装责任

- 真实FileDeviceRoutePort、完整当前用户session/role/provider/model与native root/key/设备/channel来源仍由A注入；D本机真人确认、首次账号设备bootstrap和实际用户目录的完整链独立验收pending。受控SQL/pipe/role/root/signatures目录不作为生产源注册。
- A按完整原ToolRef/hash/provider选择专用FileReceiptStore和对应material Reader；不能同provider就误接text/算术/JSON的结果Source。C没有改Context/Agent/composition/API/flags/模型/锁。
- Context低信任资料分区、recipe、引用落成果/Verification/Task完成归A。C提供准确旧FileContent/Refs/Usage及当前Reader，不生成Task完成结论、不拿成功资料导出当核验ok。
- 当前生产paging/lines真实原snapshot/cursor登记来源未提供，保持明确unavailable；新shared DTO须A生成并发布固定阶段标签。M1/M2接口无需新增公共DTO/依赖/迁移。

## 验证范围和回执

M1源码5c8854c713c6a9aa1f265016f5d6e875688f10e2，阶段815544c；M2源码54d474e2f6492bd5877df0cfb4ba358ab3cf867d，阶段f2b55e3。369单元通过（原358+新11），m2-unit.xml 20.84秒，0失败/错误/跳过。

| 回执 | 实际结果 |
| --- | --- |
| material-first.xml | 1失败：fixture尝试修改既有frozen Location模型，完整失败保留 |
| material-fixed.xml | 15通过，503.35秒，fixture改为修改wire副本 |
| a-bridge.xml | 11通过，59.69秒，基线A桥到C资料消费/丢回应/撤销/whole边界 |
| material-recovery.xml | 6通过，212.88秒，新process无open及原费用独立恢复/metadata篡改 |
| material-extra.xml | 4通过，97.75秒，用户ID/UTF8限额/当前device版本/key撤销 |
| original-affected.xml | 45通过，984.98秒；41原文件+4text/办公兼容节点 |
| 静态 | Ruff通过；Mypy33源码通过；76文件format-check通过；diff-check通过 |

新SQL去重36节点最终全部通过；原219SQL基线保留，此轮按影响复跑41文件节点和4text/办公兼容节点，其余174未改不以本轮重跑宣称覆盖。本轮SQL去重81个节点（新增36+原受影响45）全部通过；verification-index.json记录每个最后节点，重试不累加。

命令：`. ./ops/start-dev-db.ps1 -Session C`、锁定`.venv/Scripts/python.exe -m alembic upgrade head`；`-m pytest tests/unit/tool -q -p no:cacheprovider`；新SQL三个`test_file_material*_postgres.py`及原两个file模块/4兼容node，均`-v -p no:cacheprovider --require-postgres`，独立basetemp与junitxml。新process仅stdin公开测试公钥，不复制生产凭据。

本session真实55434，通过. ./ops/start-dev-db.ps1 -Session C与锁定.venv alembic upgrade head；资料/A桥/新process/原受影响模块SQL全带--require-postgres，ignored tests/.artifacts/C/MS-T2h保留首次失败和修复，随机主体清理不操作其他库或复制私有配置。实际OS临时根/Ed25519/SQL/Blob/RunnerCommands/RunnerPipeClient/C owning source有回执；控制transport/当前role/root/device登记与公钥来源明确为受控组件，无真人点选、生产账号/bootstrap、真实LLM/Context成果整链声明。


## 重复、拒绝和回退

成功：已拥有原工具调用/实际签名FileContent，export得到固定material_ref及实际content/Usage。费用pending仍保持未知额度，资料导出不改变Task状态。
拒绝：没有真实来源503；超过当前实际字符/UTF8范围413，原文不截断；撤销或跨用户/session/project/attempt、错Ref/hash/selection或metadata冲突拒绝，旧记录不成为权限、不覆盖修复。
重复：read/ref或export再次核对同次原journal与实际内容，返回相同不可变值；实际原文件改/删后不重新open，丢material CAS回执重启查原固定ref。当前数据拒绝仍可按独立当前预算权限重放已接受原固定费plan，不能反向获取正文。
回退仅撤销A对资料adapter的显式组装，原FileReceiptStore/三个办公工具继续可用；不要reset worker历史或覆写共享schema。包后停止，下一包需要正式派发。
