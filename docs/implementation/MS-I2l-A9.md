# MS-I2l A9：文件准入、原审批与交付来源的组件阶段

2026-10-11。源码以 `ms-i2l-a9-source` 固定，准确 SHA 由 DISPATCH 发布。
这是同轮组件阶段，**完整本机文件读取、真实文件模型交付和本人页面验收未通过**。
没有建立新一轮开发包，旧 start、A1–A8 标签与旧全量保持。

## 已实现的 A 接线

1. 管理员只读 provider：闭合安装 profile、实际 availability、原 revision 接受接口。
   缺 native 原来源仍不可用；接受 provider 不激活配置或开启 flags。
2. Run 原准入：提交事务固定原账号会话、工作区、模型、配置、provider、
   实例和原根证据摘要；等待后重新检查，不凭模型提供的路径或 owner 授权。
3. 每 Run 混合 office/file runtime：消费 C 严格工具与结果路由，保留各自
   ledger、executor、预算和审批；HTTP 审批从原绑定选择所属服务。
4. 原文件材料到外部低信任 Context；模型仍固定为用户所选。
   成果核验使用原观察与准确 fragment 引用，接受前再次核对来源。
5. 子端消费已存在的原审批和真实控制签名，不申请新审批或发送新动作。
   原通道双方使用同一原登记截止时间，修复两端本地时钟起算差导致的来源不一致。
   此期限不晚于任一 session，可能比原握手后窗口更短，不能描述为时限增加。
6. 原 cleanup drain 不被第二次 stop 取消；当前 metadata 检查复用短
   READ COMMITTED 连接，每次仍实际 SELECT。没有权限/结果缓存，等待后复查保留。

## Worker 消费

- B 最终源码 `394d78579bb6841bd936b11af557bc401d0b2dba`。
- C 最终源码 `223c9a9963414bdc1ae71d3e723224d0958ab63c`。
- D 最终源码 `acd7bd9d10387566c634b87d99fe3c01c165f618`。

以上已按准确提交合入 A；没有同步或改写 worker 工作区/业务源码。
组件交付不是完整产品接受。

## 实际回执

[阶段证据](evidence/ms-i2l-a9.json)记录去重并集 **191 项通过**：59 单元、132 集成。
集成范围包括实际 PostgreSQL 和真实双进程 OS/IPC，也有明确受控的
pipe/native/材料输入；不能把132项全部称作本人实链或 SQL。
各批回执与摘要保留，重叠不求和。208源码 Mypy通过，运行代码及A新测试Ruff通过。

原混合批读单元 fixture 缺已发布的 read_many port，出现51通过/1失败；
补齐受控 Reader 后原顺序、重复读取和撤销断言不变，52项复跑通过。
两次受限单元运行在 Windows socketpair 创建停住，尚未进入异步测试；
保留 faulthandler 诊断并停止仅本次自有进程，允许本机通信后正常复跑。
遗漏 Runner 目录的 Mypy 和通用 contracts 既有466项风格检查失败也单独保留。

A8原XML/environment字节已另存，当前契约证据明确改为A9组件范围；
旧1691全量和外部模型费用不更新。

## 尚未通过的关键链路

Windows原 FileTool实链 source2–source12失败均保留。
最近 source12：103.47秒，原 command 发1次，文件打开0次，ipc_broken；
4随机凭据、2角色key、原子进程与proof pipe均清理。
注册/审批/根/执行器中重复展开完整来源消耗了原lease/响应期限。
没有以延长期限、重发unknown或删除关键等待后检查处理此失败。

[A/D具体修复请求](../coordination/requests/A/MS-I2l-A9-D-original-read-budget.md)
已写明责任与回归门槛；2026-10-11 用户授权后，按准确 journal 源码正式发布并直接发送现有 D。
A继续负责控制端与实际来源适配。

实际后台8000和准确B构建5173已启动，匿名同源会话接口401正确；
当前没有原拥有者浏览器页和有效新本人实例。
[B认证只读准备](../coordination/requests/A/MS-I2l-A9-B-authenticated-readonly.md)
仍pending。未进行新本人确认、用户文件读取或模型调用；不代成果接受。

默认 flags、子Agent、DAG、写入、安装和exec保持关闭。
汇合全量在实链修复后执行，本阶段不标 MS-I2l/P1 accepted。

## 原 journal 恢复续项

A追加`InstalledJournalRecovery`与RunnerPipeClient的可信recovery port。
仅installed装配注入原目录的ReadExecutionJournal/ReceiptJournal和同一个原命令Reader；
该Journal verifier没有执行authority或owner mapping，不会构造新的执行准入。
已有发布Ref读取后核对原签名、exact command/owner/attempt/bytes，再复查当前来源与journal。
首次command仍单次发送；后续材料复读不再向只处理一次命令的原helper发送recover。

新6项实际SQL/SQLite/签名组件检查通过，覆盖原文件被移除后读取、无回执、未发布、
签名变化、设备撤销及读取后撤销；明确受控的执行/通道来源不算真人或首次Windows实读。
首次测试错误调用ReceiptJournal.save（既有名称publish）造成5项准备失败，已保留；
修正调用名后6项复跑通过。209源码Mypy与源码Ruff/格式通过。
[续项证据](evidence/ms-i2l-a9-journal.json)将组件去重并集更新为197，
原191/A8和失败回执各自保留。已失效原通道仍拒绝，不自动新建数据授权或重连。
原首次文件实读、真实固定模型/本人页面及全量门槛没有变化。

## 原 authority 短连接续项

`RunnerCommands.collect` 的两次完整检查及 `RegisteredRunnerAuthority.current` 的
前后 registered command 查询共用短 owning-task READ COMMITTED 连接范围。
每次 get 仍执行 SELECT；原完整检查、等待后比较、期限和拒绝行为均保留。
连接在返回当前来源前释放，不带入调用方 IPC/文件执行，不共享给子任务。

56 个实际 SQL/Ed25519 回归节点通过，含新增4个检查：正常两轮检查、
子任务改变模型绑定、撤销命令、取消 Run。后3者被拒绝；子任务使用不同 SQLAlchemy
session，返回或异常后 owning context 清空。channel/root/consent仍为受控组件输入。
209源码Mypy与改动Ruff/格式通过。没有前后耗时基准，不宣称性能提升比例。

[本续项证据](evidence/ms-i2l-a9-current.json)与
[201不同定向节点](evidence/ms-i2l-a9-current-tests.xml)保留原191、journal197、所有失败及旧全量。
D 已收到准确 journal 执行基线和具体任务；本改动没有改变公开 wire 或 D port，
D 不自动消费 A 浮动 HEAD。首次本机读取、模型文件成果、原本人页面与整轮仍 pending。

## D 定向修复与 A 原 owner/current 续项

D最终源码7926160、交接28850ff已审阅合入；B394d785/C223c9a9已在历史内，没有重复合并。
D195不同定向节点是worker组件覆盖，未与A统计直接相加；A复验10个私钥await后拒绝节点通过。

A修复同一原映射对ctx原用户的查询，16个实际SQL/签名节点通过。
原首次文件链两次回执均失败：第一次单独mapping违反helper构造约束（11.86秒），
第二次同一mapping原用户分支消除旧身份拒绝，但原10秒响应仍取消（77.52秒、command1/open0）。
原随机凭据/keys/child/proof均清理，无用户正文、新模型调用或native操作。

A新增有界原command current/watch内部port，14个SQL/签名节点通过，仍是完整来源查询，
未装配D执行端，不将接口通过或timeout拒绝当成本问题解决。
修复前序列化/fixture/受控hook失败保留。210源码Mypy及改动Ruff/格式通过。
详细输入/输出/来源范围/限制见[A10接线说明](../coordination/requests/A/MS-I2l-A10-owner-recheck.md)。
A11 同轮续项见 [checked reads](../coordination/requests/A/MS-I2l-A11-checked-reads.md) 和
[回执](evidence/ms-i2l-a11.json)。93个不同定向节点，含历史组件并集245；非一次全量。
默认关闭的 SQL witness 选项、相同快照 SELECT 42→34 已验证；两次实际候选读取仍失败，
其中最新91.23秒、command1/open0，临时凭据/keys/child/proof清理。未标生产优化或整轮接受。
