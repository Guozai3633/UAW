# MS-I2k：页面接线、文件资料与本机服务开发包

日期：2026-10-10。正式开发包；开工以 DISPATCH 的 ms-i2k-start 准确 SHA 和远端标签核对为准。

四个会话原来都因标签未发布而等待。A 已恢复审批服务，补齐桥接静态/类型及真实SQL验证，审阅正常合入三个组件。MS-I2j 的真人授权/实际浏览器与最终全量仍未完成；这些作为本包明确任务继续，不将旧轮标 accepted，也不要求这些待实现结果反过来成为所有 worker 的开工条件。

## 1. 为什么这样分

下一轮围绕真正可操作的用户闭环：B 消费已经存在的 HTTP；C 加强文件观察进入任务/成果的 owning Reader；D 完成实际本机启动与授权来源适配；A 负责账号控制源、装配和整链。四方各自可先做接口和本模块行为，不等待另外三包全部结束。暂不增加子 Agent/DAG/写入/安装/exec。

## 2. 来源与目录

A 发布 **ms-i2k-start**，包含已合入 B/C/D 最终源码、已验证的原 Tool 桥接适配及[固定输入协议](MS-I2k-input-contracts.md)。准确 SHA 以 DISPATCH 和远程核对为准，不用浮动 integration 代替。旧 ms-i2j-start、a1、a2 不移动。

准确标签 SHA：**b7b79b150470a80f37b28fd52a2177f6de5b3124**；运行源码提交 d52ed515f9def6b2d0144e779a5793a7022bf676。标签还包含准备说明/回执，后续仅发布元数据的 integration commit 不要求 worker 追随。

| Session / 包 | 保持目录与分支 | 独占开发范围 |
| --- | --- | --- |
| A / MS-I2k | E:/UAW，integration | A 原保留 api/run/agent/model/infrastructure/composition/共享契约、部署配置与 A 测试/全局文档 |
| B / MS-U2 | E:/UAW/.worktrees/context，dev/context | apps/web、B requests/handoff；本轮暂停 Context 优化 |
| C / MS-T2h | E:/UAW/.worktrees/tool，dev/tool | src/uaw/tool、C 单元/SQL和 C requests/handoff |
| D / MS-R2h | E:/UAW/.worktrees/runner，dev/runner | apps/local_runner/uaw_runner、D 原 workspace 允许文件、D 测试和 requests/handoff |

worker 自行检查干净→fetch tags→快进正式标签→核对 SHA→锁定依赖。任何失败保留现场，不 reset/rebase/stash。A 不切 worker 分支或修 worker 业务源码。M1/M2 阶段提交到即审阅，不等三包齐。模块 SQL 仍由 worker 的独立数据库执行。

## 3. A / MS-I2k：真实控制源与用户整链

| 里程碑 | 每轮任务和实现目标 | 交付及验收 |
| --- | --- | --- |
| M1 | 补完 RegisteredFileBridge 静态/SQL/实际 IPC；固定原 ToolCall/request hash、独立预算与根权限。发布可信账号→设备→通道挑战内部来源契约、缺失错误与撤销规则 | A 保留目录/契约与 tests/integration；原 ctx 不改，unknown 不重发，旧 check 兼容 |
| M2 | localhost 实际后端启动/关闭；同用户 Web 身份与服务端持久控制登记绑定，D 启动进程独立验账号、OS 实例及当前 keys。A2 列表/原请求/成果 API 服务 B | API 可达且实际用户登录；不从模型 body/SID 单独推导 UAW 账号，不发布公网 OIDC 承诺 |
| M3 | C 原文件调用→真实登记/审批/预算→D 当前授权根/命名管道→签名原 journal→文件观察→Context/成果引用。实际 revoke、logout、取消、旧版本与丢回应恢复 | 明确整个源链，文件正文不能升级规则；无真人选择不启用用户目录 |
| M4 | B 真实页面办公/学术/文件、人工审批/拒绝、取消/刷新、用户接受；所有失败/费用记录，逐包接受后一次完整里程碑回归 | 真浏览器与真实模型分开计数；人工缺口标 pending，原全量保留来源 |

## 4. B / MS-U2：A2 真实客户端与完整成果

M1：从正式固定基线生成 A2 已实现 DTO/API；真实 server conversations.list 分页、turns.lookup RecoveryPort、RunDeliveryView ReviewPort。ReviewSnapshot 绑定准确 artifact/bundle/contract/report，接受后查实际 receipt/Run。默认入口可用，不要求注入测试 host。

M2：会话列表加载/刷新/跨登录历史；整份正文、逐项理由/限制/引用、等待接受；与实际 backend 联调完整原文→理解→成果。缺成果 404 是尚无结果，不当作完成或重新发送。

M3：未知提交/接受、分页过期、旧 artifact hash、取消与接受竞争、退出/身份切换、刷新无自动 POST。接受未知先读实际 acceptance；没有原 receipt 时保持不确定，不换 request_id 重发。明确错误恢复按钮。

M4：类型、冻结安装、构建、必要单元与受控 Chromium；A 提供可达 backend/短期 launch 后真实 suite。禁止读取 A 私有配置/key；不把受控浏览器计入真实场景。文件授权只显示实际服务端状态，浏览器不授予 path 权限。

设计目录：apps/web/src/lib/api（固定客户端和生成物）、features/workspace（列表/恢复）、features/review（内容/核验/接受）、tests/unit、tests/e2e/live。阶段源码/最终源码/handoff 分开。

## 5. C / MS-T2h：文件资料与实际证据消费

M1：固定 FileReceiptStore 当前数据权限、read_observation/read_raw/read_outcome 与 A Context/Artifact 消费签名；同一个原 full snapshot/selection/hash/Usage，不能直接读 SQL 绕过 owning Reader。列明确 whole、lines/cursor/16384 字符的实际生产边界。

M2：实现有界文件观察导出/资料适配，固定完整原命令/签名/selection、不可变正文来源和归属。A 接 actual Model/Context；C 不修改 Context 或 Agent 源码。新具名 DTO/公共变更提案 A，不能自加 Object 授权字段。

M3：数据撤销与账务恢复独立，取消/跨用户/会话/根/设备/版本、原内容变更、丢回应/重启无新打开。若 A 实际桥仅 whole，分页保持 unavailable；不能扩大 Spec 的实际能力承诺。

M4：55434 独立 SQL 验实际 Reader→原证据→资料/预算恢复，原 219 SQL 仅因影响范围复跑；统计最后节点，不叠加重试。A 实际桥到达先跑一个跨边界样例，缺真人确认标 pending。默认 flags 不改。

设计目录：src/uaw/tool/providers/file_store.py 及新增 file material adapter、C 自身单元/integration；工具失败仍由 Tool Runtime 持有，任务通过由完成控制器判断。

## 6. D / MS-R2h：实际本机服务装配与授权流程

M1：按 A 已发布可信挑战/设备/通道登记接口，固定本机 bootstrap consumer。精确 schema/签名/key role/期限、原完整用户会话与 OS 创建时间；缺来源不可用。A 未发布时先交输入提案和独立装配接口，不能自行更改公共 pair.complete。

M2：可运行的只读本机 helper 启动/关闭，默认隐藏进程；只有本人目录选择/确认窗口可见。ProtectedSigner、CurrentKeyDirectory、ConnectionRegistry、NativeReadAuthorization 和 ReadOnlyPipeEndpoint 用同一真实当前来源。

M3：root selection 一次消费、当前 workspace mapping、撤销/断线/重连、原 journal 恢复及自有资源清理。绝对目录仅本机；unknown recover 不发 command；pairing proof 不来源于网页 approved/path 或测试账号。

M4：实际 Windows 组件、双进程 IPC 与 helper lifecycle；准备本人确认步骤与可审阅界面，A/用户实际点选后记录独立回执。不自动点击批准，不拿 typed UI double 当真人确认。不开放安装/写入/exec。

设计目录：apps/local_runner/uaw_runner/bootstrap/runtime 适配与既有 native_*、ipc，D unit/integration/manual。实际启动接口由 D owning module 交付，A 负责 HTTP/账号控制源。

## 7. 正式发布门槛

1. A 的桥接代码实际检查通过，跨模块来源差异已验证，合并后的受影响回归有准确 commit/原 XML。
2. 下一轮公共输入接口、允许目录、错误及实际未完成门槛固定；不要求 worker 猜来源。
3. A 提交计划/提示词，创建新标签并 push/ls-remote 核对，DISPATCH 明确已派发。
4. 正式固定基线发布前不开始新包；发布以后 worker 可做本模块实现，真人授权/页面联调/首次配对来源作为明确汇合门槛，不能因缺来源伪造通过。
