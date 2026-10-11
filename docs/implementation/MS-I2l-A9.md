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
已写明责任与回归门槛，尚未授权/正式派发。A继续负责控制端与实际来源适配。

实际后台8000和准确B构建5173已启动，匿名同源会话接口401正确；
当前没有原拥有者浏览器页和有效新本人实例。
[B认证只读准备](../coordination/requests/A/MS-I2l-A9-B-authenticated-readonly.md)
仍pending。未进行新本人确认、用户文件读取或模型调用；不代成果接受。

默认 flags、子Agent、DAG、写入、安装和exec保持关闭。
汇合全量在实链修复后执行，本阶段不标 MS-I2l/P1 accepted。
