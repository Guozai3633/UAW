# Session D：Runner协议与授权组件

[并行开发总入口](../PARALLEL.md)

状态：MS-R2b已接受；MS-R2c已由用户确认开工，开发签名终态回执journal，实际登记Reader/IPC仍待A。以DISPATCH的固定版本与派发为准。

## 工作位置和顺序

- 实际分支：`dev/runner`。
- 实际worktree：`E:/UAW/.worktrees/runner`。
- 首包：MS-R1；后续：MS-R2a、MS-R2b、MS-R2c、MS-R2。
- 交接记录：[docs/coordination/handoffs/D.md](../../coordination/handoffs/D.md)。
- 公共变更提案目录：`docs/coordination/requests/D/`。

## 可修改路径

- `src/uaw/workspace/binding.py`
- `src/uaw/workspace/contracts.py`
- `src/uaw/workspace/ports.py`
- `src/uaw/workspace/repository.py`
- `apps/local_runner/uaw_runner/`
- `tests/unit/runner/`
- `tests/integration/runner/`
- `docs/coordination/handoffs/D.md`
- `docs/coordination/requests/D/`

忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。

## 具体边界

- 先落实可信命令信封、期限/主体/签名校验port、授权根和撤销状态。
- RootSelection只由可信本机用户入口生成；测试根限制在本session临时目录。
- D03未决定前不开放安装/写入/exec；仅协议组件不能宣称配对或OS隔离已经可用。
- 签名算法或新依赖需要契约/ADR提案，由A集中落地后再验证真实签名。

公共schema/port/依赖有缺口时，提交有字段、示例、错误语义和受影响调用方的提案，A合入并发布新基线后再使用；不在私有DTO中偷偷加不兼容字段。

## 对应工作包

### MS-R1：Runner协议与授权范围校验

对应原轮：[P1-04](../rounds/P1-04.md)。
开发前置：MS-00。

任务：

1. 落实RunnerCommand/Receipt DTO校验与签名验证port，校验期限、主体、根句柄、fencing和稳定command_id。
2. 实现获准根/相对路径/真实路径校验与撤销模型；临时目录验证链接越界。
3. 设计配对nonce/一次码及RootSelection的来源/有效期/一次使用，不把聊天路径当授权。
4. 列出真实IPC、签名实现、配对存储与D03决定所需接线；包外依赖交A审批合入。

交付检查：

- 组件校验和真实本机临时路径验证有证据；签名替身只算协议测试。
- 不连接真实用户项目、不安装系统环境、不开放exec。
- 没有真实配对/签名/执行权限回执时P1-04不能标accepted。

### MS-R2a：真实签名适配和配对一次使用状态

对应原轮：[P1-04](../rounds/P1-04.md)。
开发前置：MS-I2a。

任务：

1. 消费统一Ed25519原语并落实当前可信key目录/撤销/密钥角色；私钥不进入普通记录或模型。
2. 实现配对nonce/一次码/挑战和RootSelection的持久CAS状态，缺可信IPC/证明不批准。
3. 提出异步Runner权威port与配对证明DTO接线提案，验证真实签名与一次使用/过期/撤销并发。

交付检查：

- 签名测试使用真实密码学；持久一次消费与权限来源有真实测试，不以测试布尔量自证。
- D01/D03和IPC未满足项明确，不开放安装/写/exec，不声称真实用户配对完成。

### MS-R2b：异步Runner协议消费入口

对应原轮：[P1-04](../rounds/P1-04.md)。
开发前置：MS-I2c。

任务：

1. 使用共享AsyncRunnerAuthorityPort和RunnerAuthoritySnapshot，在D目录增加严格typed wrapper与异步admit入口。
2. 认证主体由可信适配器独立传入，当前权威与command声明逐项比较；没有真实映射/authority/IPC不开放入口。
3. 每次await后重查实际时钟、取消/撤销/版本/租约/fence；关键检查后再取当前权威，拒绝参数或授权变化，不缓存执行许可。
4. 保留同步接口兼容；测试异步期间过期/撤销/主体变化、阻塞和取消、重启/并发admission；无asyncio.run桥接。

交付检查：

- 协议使用公开JSON DTO并保持真实签名与当前key检查；组件authority替身不宣称实连。
- 本轮不发布配对V2或重解释私有Ticket签名；D01/D03和OS凭据/真实IPC仍待实际接线。

### MS-R2c：签名终态回执持久journal

对应原轮：[P1-04](../rounds/P1-04.md)。
开发前置：MS-I2e。

任务：

1. 通过可选ReceiptCommandReaderPort读取独立登记RunnerCommand/device/owner；当前身份来源不取自receipt请求体。
2. publish/read保存并返回严格RunnerReceipt及实际固定Ref，复用真实Ed25519 receipt域与既有command/attempt/action/资源核验。
3. 开发SQLite仅保存终态，唯一身份CAS、相同内容去重、冲突拒绝、当前key/来源复查，支持重启及进程并发。
4. waiting、实际Reader、IPC、配对V2和执行保持不可用；恢复不生成not_applied或零费用结论。

交付检查：

- 真实签名和持久/跨进程验证通过；受控登记源只算组件，无私钥/凭据进入账本。
- 不把admission当执行，不从Runner ok推导Tool applied；精确方法/范围见MS-I2e-next-packages。

### MS-R2：真实IPC配对和获准执行接线

对应原轮：[P1-04](../rounds/P1-04.md)、[P1-05](../rounds/P1-05.md)。
开发前置：MS-I2、MS-R2a。

任务：

1. 落实实际签名/可信IPC/用户确认配对及授权句柄的存储。
2. D03确定且真实权限到位后才能进入输入快照、隔离和进程；安装另走审批。

交付检查：

- 实际配对/权限有回执，scope逐次复核。
- 代码隔离不声称OS隔离，真实代码任务仍需实际test与交付验证。

## 可复制到新session的开工说明

下面只启动本session任务；用户在独立工作区新建聊天后粘贴。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session D：Runner协议与授权组件。
当前工作目录必须是E:/UAW/.worktrees/runner，分支必须是dev/runner。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/D.md。
读取docs/coordination/DISPATCH.md。首次开工核对HEAD与parallel-wave-1解析出的commit相同；后续按A发布的新基线同步。
当前执行MS-R2c。工作区干净后fetch origin --tags，使用git merge --ff-only ms-i2e同步本工作分支；失败先报告，不reset，保留已有历史。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
