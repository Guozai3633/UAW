# UAW 多session开发计划

v0.7 · 2026-10-08 · 方案：**3个开发session＋1个集成session，共4个**。

先让不同session各做一个不重叠的组件包，再由集成session接起来。接口文档使组件能按同一规则开发；完整任务能运行，还需要具体文件归属、固定代码版本和组合验证。

## 1. 当前起点

- P0-01、P0-03、P0-04已验收；P0-02开发存储已验证，D01最终权威位置待定。
- P0-05模型网关已实现；真实模型/API凭据尚未配置，D06及真实LLM验收未完成。
- P1-01原文/逐字来源、理解版本、修订、取消、幂等与当前frame读取的协议检查通过；真实模型语义验收仍待D06。
- 当前全量841项通过，无跳过；真实PostgreSQL＋受控模型响应，未运行实际Agent/Runner任务。
- `E:/UAW`已建立`integration`分支，`origin`关联`https://github.com/Guozai3633/UAW.git`。
- **MS-I2f2已验证，MS-C4/MS-T2c/MS-R2c组件已接受。** A接通登记命令Reader，提供缓存可选组装并统一content回执引用。B/C/D保留交付边界，待明确下一包；A继续完整MS-I2f真实来源接线。接受与安排见[统一派发表](../coordination/DISPATCH.md)。

沿用原三个worktree，开发session自行在包边界同步固定标签；A不改写worker分支。具体见[开工、合并与交接流程](PARALLEL_WORKFLOW.md)。

## 2. 首批session

| Session | 做什么 | 首个包 | 实际分工 |
| --- | --- | --- | --- |
| [A：集成与任务理解](sessions/A.md) | 负责现有P1-01收尾、公共契约、组装根、迁移、依赖锁和合并。 | MS-00 | 推荐4个方案 |
| [B：上下文组件](sessions/B.md) | seed.py和intent.py包含已验证的理解专用实现，归A；B用新文件实现通用Context组件。 | MS-C1 | 推荐4个方案 |
| [C：工具组件](sessions/C.md) | 先做小工具目录、schema规范化、角色/权限/flag过滤和动作身份。 | MS-T1 | 推荐4个方案 |
| [D：Runner协议与授权组件](sessions/D.md) | 先落实可信命令信封、期限/主体/签名校验port、授权根和撤销状态。 | MS-R1 | 推荐4个方案 |
| [E：可选样本与评测](sessions/E.md) | 第5个session可选，负责办公/开发/学术样本、验收表和来源/权限反例。 | MS-Q1 | 第5个可选 |

A既负责当前Intent收尾，也负责后续集成；不额外承担所有模块的开发。B/C/D遇到业务问题自己修复，A集中处理公共接线和归属冲突。

## 3. 为什么这些部分现在可以并行

| 子包 | 首包真正依赖 | 此时暂不接入的部分 |
| --- | --- | --- |
| MS-C1 上下文规则/来源/预算 | 已固定InstructionSet、ContextSnapshot、Scope、Ref和模型窗口契约 | 通用Context到Intent/Model的组装、Runner读文件 |
| MS-T1 工具注册/过滤/schema | 已固定ToolSpec、ToolCall、CapabilityPolicy、flag和错误契约 | 审批、真实Runner派发及全链路结算 |
| MS-R1 Runner协议/授权范围 | 已固定RunnerCommand/Receipt、RootSelection及可信上下文 | 实际账号配对、真实签名、安装/写入/exec授权 |

这里的“无依赖”指首批组件包互不依赖另一个开发session的未完成代码。它们共同依赖MS-00发布的稳定基线。P1-02/03/04整轮本来有依赖，不能直接宣称三整轮都无依赖。

**原50轮主计划和阶段验收门槛继续有效。** 子包可提前开发；整轮接受、能力启用和真实场景验收仍要满足原轮依赖，P0-05待配置的门槛不会因并行安排消失。

## 4. 第一波与第二波

```mermaid
flowchart TD
  A0["A：P1-01收尾、验证、共同基线 MS-00"] --> B1["B：Context组件 MS-C1"]
  A0 --> C1["C：Tool组件 MS-T1"]
  A0 --> D1["D：Runner协议 MS-R1"]
  B1 --> I1["A：Context与Intent/Model接线 MS-I1"]
  I1 --> B2["B：快照与引用 MS-C2"]
  C1 --> I2a["A：审批/签名公共基础 MS-I2a"]
  D1 --> I2a
  I1 --> I2a
  I2a --> C2a["C：账本/审批适配 MS-T2a"]
  I2a --> D2a["D：签名/配对状态 MS-R2a"]
  I2a --> I2b["A：实时父子权限 MS-I2b"]
  C2a --> I2["A：真实权威与公共接线 MS-I2"]
  D2a --> I2
  I2b --> I2
  C2a --> I2c["A：组件接受和消费接口 MS-I2c"]
  D2a --> I2c
  I2b --> I2c
  I2c --> B3["B：Model输入 MS-C3"]
  I2c --> C2b["C：核对 MS-T2b"]
  I2c --> D2b["D：异步协议 MS-R2b"]
  B3 --> I2d["A：根租约与输入路由 MS-I2d"]
  D2b --> I2d
  I2d --> I2e["A：Tool接受及新基线 MS-I2e"]
  C2b --> I2e
  I2e --> B4["B：纯计算缓存 MS-C4"]
  I2e --> C2c["C：统一核对 MS-T2c"]
  I2e --> D2c["D：回执journal MS-R2c"]
  I2e --> I2f1["A：登记/当前权威 MS-I2f1"]
  I2f1 --> I2f2["A：组件接受/恢复Reader MS-I2f2"]
  B4 --> I2f2
  C2c --> I2f2
  D2c --> I2f2
  I2f2 --> I2f["A：真实来源 MS-I2f"]
  I2f --> I2
  C2c --> I2
  D2c --> I2
  I2 --> C2["C：真实dispatch/结算 MS-T2"]
  I2 --> D2["D：真实IPC；获准后执行 MS-R2"]
  B2 --> I3["A：汇合；按原P1轮次进入Agent闭环"]
  C2 --> I3
  D2 --> I3
```

每次合入发布新集成SHA。开发session在包边界同步后进入下一包；未完成的分支不会直接作为另一个session的依赖。MS-I3仅是汇合入口，P1-06变更、P1-10真实界面等原工作包仍须另行完成。

## 5. 开3个或5个怎样调整

| 总session数 | 分配 | 调整 |
| --- | --- | --- |
| 3 | A集成＋B上下文＋C工具 | Runner协议放下一波，由已完成首包的开发session接手；先更新负责人及路径归属，不能默认多出第4个 |
| **4，推荐** | A集成＋B上下文＋C工具＋D Runner | 符合3个session分别开发、另1个负责合并的想法 |
| 5 | 上面4个＋E样本/评测 | E写独立样本与审阅标准，不再让第5个一起改共享基础文件 |

首次尝试先跑完一波小包，再按实际冲突、等待与集成耗时决定是否增加session；不预估线性提速。

## 6. 每个包的交付与正式状态

| 包 | 负责 | 标题 | 组件开发前置 | 原轮 |
| --- | --- | --- | --- | --- |
| MS-00 | A | 收尾并建立共同基线 | 现有进度收尾 | [P0-05](rounds/P0-05.md)、[P1-01](rounds/P1-01.md) |
| MS-C1 | B | 规则、来源与窗口分配 | MS-00 | [P1-02](rounds/P1-02.md) |
| MS-T1 | C | 工具注册、过滤与参数校验 | MS-00 | [P1-03](rounds/P1-03.md) |
| MS-R1 | D | Runner协议与授权范围校验 | MS-00 | [P1-04](rounds/P1-04.md) |
| MS-Q1 | E | 三类样本及语义审阅标准 | MS-00 | [P0-01](rounds/P0-01.md)、[P1-01](rounds/P1-01.md)、[P1-11](rounds/P1-11.md)、[P2-07](rounds/P2-07.md) |
| MS-I1 | A | 合入Context并接Intent/Model | MS-00、MS-C1 | [P1-01](rounds/P1-01.md)、[P1-02](rounds/P1-02.md) |
| MS-C2 | B | 固定快照和引用查询 | MS-I1 | [P1-02](rounds/P1-02.md) |
| MS-I2a | A | 持久人工审批和签名公共基础 | MS-I1、MS-T1、MS-R1 | [P1-03](rounds/P1-03.md)、[P1-04](rounds/P1-04.md) |
| MS-T2a | C | 持久调用账本和审批适配 | MS-I2a | [P1-03](rounds/P1-03.md)、[P1-09](rounds/P1-09.md) |
| MS-R2a | D | 真实签名适配和配对一次使用状态 | MS-I2a | [P1-04](rounds/P1-04.md) |
| MS-I2b | A | 实时父子权限链公共接线 | MS-I2a | [P1-02](rounds/P1-02.md)、[P1-03](rounds/P1-03.md)、[P1-04](rounds/P1-04.md) |
| MS-I2c | A | 接受基础组件并发布恢复/异步消费接口 | MS-I2b、MS-T2a、MS-R2a | [P1-02](rounds/P1-02.md)、[P1-03](rounds/P1-03.md)、[P1-04](rounds/P1-04.md) |
| MS-C3 | B | 通用快照到Model输入转换 | MS-I2c | [P1-02](rounds/P1-02.md)、[P1-07](rounds/P1-07.md) |
| MS-T2b | C | 预算接口收敛和可信结果核对 | MS-I2c | [P1-03](rounds/P1-03.md)、[P1-09](rounds/P1-09.md) |
| MS-R2b | D | 异步Runner协议消费入口 | MS-I2c | [P1-04](rounds/P1-04.md) |
| MS-I2d | A | B/D组件接受、根执行租约与输入路由 | MS-I2c、MS-C3、MS-R2b | [P1-02](rounds/P1-02.md)、[P1-04](rounds/P1-04.md)、[P1-09](rounds/P1-09.md) |
| MS-I2e | A | 接受Tool核对组件并发布下一轮范围 | MS-I2d、MS-T2b | [P1-03](rounds/P1-03.md)、[P1-09](rounds/P1-09.md) |
| MS-C4 | B | 上下文纯计算有界缓存 | MS-I2e | [P1-02](rounds/P1-02.md)、[P4-04](rounds/P4-04.md) |
| MS-T2c | C | 统一核对入口与效果结论读取 | MS-I2e | [P1-03](rounds/P1-03.md)、[P1-09](rounds/P1-09.md) |
| MS-R2c | D | 签名终态回执持久journal | MS-I2e | [P1-04](rounds/P1-04.md) |
| MS-I2f1 | A | 设备/命令登记及当前权威组件 | MS-I2e | [P1-03](rounds/P1-03.md)、[P1-04](rounds/P1-04.md)、[P1-09](rounds/P1-09.md) |
| MS-I2f2 | A | 缓存/工具恢复/journal接受与登记Reader接线 | MS-I2f1、MS-C4、MS-T2c、MS-R2c | [P1-02](rounds/P1-02.md)、[P1-03](rounds/P1-03.md)、[P1-04](rounds/P1-04.md)、[P1-09](rounds/P1-09.md)、[P4-04](rounds/P4-04.md) |
| MS-I2f | A | 实际设备归属、登记命令与当前权威 | MS-I2f2 | [P1-03](rounds/P1-03.md)、[P1-04](rounds/P1-04.md)、[P1-09](rounds/P1-09.md) |
| MS-I2 | A | 合入Tool与Runner并完成真实权威接线 | MS-I2f、MS-T2c、MS-R2c | [P1-03](rounds/P1-03.md)、[P1-04](rounds/P1-04.md) |
| MS-T2 | C | 工具真实dispatch及结算接线 | MS-I2、MS-T2a | [P1-03](rounds/P1-03.md)、[P1-09](rounds/P1-09.md) |
| MS-R2 | D | 真实IPC配对和获准执行接线 | MS-I2、MS-R2a | [P1-04](rounds/P1-04.md)、[P1-05](rounds/P1-05.md) |
| MS-I3 | A | 汇合后进入Agent闭环 | MS-C2、MS-T2、MS-R2 | [P1-07](rounds/P1-07.md)、[P1-08](rounds/P1-08.md)、[P1-09](rounds/P1-09.md)、[P1-11](rounds/P1-11.md) |

开发交付只写各自handoff；A在[统一派发表](../coordination/DISPATCH.md)记录基线、派发与接受。两者是不同文件，减少状态记录冲突。组件交接通过不自动将整轮改为accepted。

## 7. 具体入口

- [文件归属、worktree、公共变更与合并流程](PARALLEL_WORKFLOW.md)。
- [提交交接模板](../coordination/HANDOFF_TEMPLATE.md)与[公共接口变更模板](../coordination/REQUEST_TEMPLATE.md)。
- 各session页末尾有可复制到新聊天的开工说明。
- [机器分工/依赖/归属表](../../planning/parallel-plan.json)与[计划检查结果](parallel-check.json)。
- [并行计划维护源](../../planning/parallel_catalog.py)；运行 `python planning/build_parallel.py`，总计划生成器也会重建本计划。
