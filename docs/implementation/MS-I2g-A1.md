# MS-I2g-A1：当前来源、阶段接口与逐包接线

日期2026-10-08；A / E:/UAW / integration；开工基线ms-i2g-start。**本阶段开发与受影响范围验证完成；完整MS-I2g里程碑仍等待B的最终交接及里程碑全量。**

已验证源码/证据提交：`8b581af6eca951a2af2919361feaaeb85afa2477`。固定阶段标签ms-i2g-a1包含随后状态记录；worker正在开发的固定标签ms-i2g-start保持不变。

## 1. A实际实现

- `run/execution_sources.py`：当前实际Run/政策链/配置和用户固定模型选择来源；结果数据读取与新执行准入分开。
- `run/tool_sources.py`：可信服务登记RoleProfile、每Run/Agent槽位的完整身份/session/范围/政策绑定、CAS和撤销；实际当前ToolAccess、纯文本资源Reader及结果恢复数据权限。
- `run/context_sources.py`：注册Context使用实际Run/固定模型；非空工具集核对当前确切ToolSpec、角色、提供方、权限及flags。没有默认生成权限或替换用户模型。
- `run/runner_mapping.py`：从实际RunnerDevices/current通道获得完整owner，适配D关键字接口。
- `composition.py`：内部 `assemble_registered_context`、`assemble_text_tool`、`assemble_runner_control`。Context接实际登记→快照→通用Model输入；Text接实际审批/预算/一次调用→输出验证→回执/费用核对→ToolResult与当前数据读取；Runner接当前设备mapping、独立根factory、动作gate、控制签字和登记Reader。

新增严格对象RunToolAccessBinding，复用既有RoleProfile、SQL记录表和具体schema；没有新公开HTTP操作或共享port破坏性修改，没有依赖/迁移新增。内部构造的service/provider身份仍必须来自可信部署入口；框架不从模型正文创建认证。默认公开Agent/Tool/Workspace与通用Context的产品启用仍须后续验收。

详细方法、输入输出、命名空间和策略见 [MS-I2g接线](../coordination/requests/A/MS-I2g-wiring.md)；对象字段见 [RunToolAccessBinding](../api/objects/RunToolAccessBinding.md)。

## 2. 逐包合入和接受

| 包 | 实际提交/合入 | 本阶段决定 |
| --- | --- | --- |
| B/MS-C5 | 阶段源码d0ad58f → 80b86b7 | 阶段接口和登记源合入；继续本包后半段，最终包未接受 |
| C/MS-T2d | 阶段717c237 → e1503dc；最终859f5d0/db09a69 → 5721ad4 | 162单元、100个不同当前SQL通过；最终组件范围接受 |
| D/MS-R2d | 阶段1287a05 → 0be96be；最终7d946de/366c916 → b735407 | 326项通过，真实Windows凭据passed/cleaned；最终组件范围接受 |
| A当前来源 | 72abb2b及随后装配提交 | 当前角色/Run/模型/结果数据权限、三个装配入口与跨模块链验证 |

全部是正常merge，没有冲突；worker原分支、允许目录、交接及基线保持。B开发中不要求换基线；C/D没有自动进入新包。合入没有等待三包最终提交齐备。

C的100个SQL为原70和最终新增30的不同节点覆盖，并非一次100项运行。首轮96passed/1failed的回执保留；错误为新测试误用deny替代decline，全部最终新增SQL复跑通过。两项旧参数测试后来重命名，接收统计排除了旧名字，未重复计数。A也核对原SQL源文件与固定基线字节一致。D326是worker模块及原共享回归；A复核其实际JUnit和真实OS回执，不接管重复全模块执行。

完整提交SHA、回执路径/摘要和计数见 [worker证据索引](evidence/ms-i2g-worker-receipts.json)。原worker报告保留在 [C](../coordination/handoffs/C.md)、[D](../coordination/handoffs/D.md)。

## 3. A实际检查

| 回执 | 范围 | 实际结果 |
| --- | --- | --- |
| [focused](evidence/ms-i2g-focused-tests.xml) | 当前来源、Context单元、Text与控制密钥受影响用例 | 234 passed，55.57s |
| [wiring](evidence/ms-i2g-wiring-tests.xml) | 当前来源及真实SQL审批/文本结果、Context到Model输入、Runner控制签字/归属、原模型路由与理解接线 | 41 passed，491.23s |
| [Tool focused](evidence/ms-i2g-tool-focused-tests.xml) | C最终规范结果和实际文本原语 | 27 passed，14.40s |

三个批次有重叠，**去重后268个通过节点**；无最终失败/错误/跳过。Ruff通过、186文件格式通过、Mypy117源码文件通过。合同检查1282命名schema/272接口/26已实现公开操作，304反例拒绝；50轮/115节点和31包依赖/目录检查通过。合同与计划检查不代替运行验证。

历史全量841项仍对应ms-i2f2，没有把它改称当前全量。环境记录211个当前源文件摘要，另有48个相对准备版改变的受审阅文件，明确记载新的focused/worker回执和历史全量的关系，见 [环境与验证关系](evidence/environment.json)。完整MS-I2g全量放在B最终包接受后的集成里程碑。

开发中修复了新schema资源副本同步、测试使用effect=read、错误码断言、fixture attempt绑定/取消入参和结果tools元组等接线问题，均在最终实际用例中复验。源码与测试有阶段记录，不把失败或collect-only当成成功。诊断停止的本包临时fixture凭据已限定随机测试身份/确切原handle与值清理，没有操作既有用户凭据。

## 4. 已观察到的性能问题

单材料Context整链反复展开来源/配方/权限，在build.prepare结束前诊断已读到12,000次SQL。A去掉了自身重复的base/current权限链调用，保留当前检查。完整数据链仍较慢；权限和来源没有改成跨请求TTL缓存，不能声称性能已达可用产品水平。

具体计数、重复来源和B后续改进边界见 [Context读取反馈](../coordination/requests/A/MS-C5-read-amplification.md)。这个问题可继续优化，不影响本次已通过数据/权限边界的事实，也不能因通过就忽略延迟。

## 5. 尚未完成的门槛

B最终完整SQL/快照/引用/进程回执、完整MS-I2g里程碑回归仍待完成。真实LLM/D06、可信IPC、实际用户本机确认、正式control/device/key生命周期、实际文件/进程执行与D03尚未验收。Agent有限步任务循环、交付核验和真实页面仍在后续关键路径。内部文本工具的成功不表示Agent已完成用户任务。

所有源缺失仍返回明确不可用，flags未启用；本阶段不接受完整P1、MS-T2或MS-R2。代码可通过正常revert回退；回退不删除原账本、已保存内容或已有真实证据，也不代表撤销外部效果。
