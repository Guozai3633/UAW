# 任务理解 · Intent：模块开发设计

节点 `intent` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。

[开发设计索引](../README.md) · [目录设计](../../PROJECT_STRUCTURE.md) · [公共契约](../COMMON_CONTRACTS.md)

## 统一入口与状态所有权

计划包：`src/uaw/intent/`，入口：`src/uaw/intent/facade.py`。

入口契约：`IntentRuntime.preview(DraftRequest)、understand(UnderstandingRequest)、revise(FramePatchRequest)`。

所有权：TaskFrame与草稿预览；用户原文只从Run读取。

## 内部组织策略

原文读取→语义解析→按需指代/只读探查→歧义处理→TaskFrame。草稿预览单独只读分支。Semantic Parser可以复用主Agent首次调用结果，不要求一个完整理解流水线先跑完。

facade接收可信请求并协调子组件；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。

## 数据与依赖接口

输入：原文、草稿、必要资料。输出：TaskFrame / DraftPreview。

注入ports：`HistoryReader、ContextFacade、ToolReadOnlyPort、ModelFacade、FrameRepository、EventSink`。

领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。

## 决策、权限与资源策略

preview/parse使用用户选定模型；歧义语义可在同次调用判断。来源读取、版本CAS和权限由代码执行。

预览不替代用户指令；理解可以随证据修订。

每次提交绑定真实版本、当前scope、剩余deadline和预算。固定常规配置与当前撤销分开检查。多模块提交用本地事务或可恢复意图，不能承诺外部动作exactly-once。

## 失败与恢复策略

facade保留失败发生阶段与原始受控引用。参数/依赖/版本冲突回调用者修复；拒绝不通过换工具绕过；副作用unknown先Tool对账。恢复先检查此领域schema/版本兼容，再恢复可继续边界，不用Trace重建权威状态。

## 文件组织规则

- `facade.py`：统一入口、依赖注入、调用编排。
- `contracts.py`：领域请求/结果/版本化对象。
- `ports.py`：存储、跨Runtime与执行器协议。
- 子组件文件/包：实现具体策略，分层节点有自己的facade/contracts/ports。
- `repository.py`：领域存储适配，实现CAS和幂等；业务规则仍在组件。
- `tests/unit/` 与 `tests/integration/`：实现阶段只验证具体风险/门槛，不复制实现。

## 实施与验收门槛

第一条任务验证原文不可覆盖、歧义与资料读取失败；预览失败不影响发送。

首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/intent.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 草稿理解预览 | [intent.preview](../components/intent-preview.md) | `src/uaw/intent/preview.py` |
| 原文读取 | [intent.original](../components/intent-original.md) | `src/uaw/intent/original.py` |
| 语义解析 | [intent.semantic](../components/intent-semantic.md) | `src/uaw/intent/semantic.py` |
| 指代解析 | [intent.references](../components/intent-references.md) | `src/uaw/intent/references.py` |
| 必要信息探查 | [intent.probe](../components/intent-probe.md) | `src/uaw/intent/probe.py` |
| 歧义处理 | [intent.ambiguity](../components/intent-ambiguity.md) | `src/uaw/intent/ambiguity.py` |
| 任务框架 | [intent.frame](../components/intent-frame.md) | `src/uaw/intent/frame.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：发起理解或修订 | [运行控制 · Run](run.md) |
| 本节点 → 下游 | 数据/引用：目标、约束、未知项 | [决策执行 · Agent](agent.md) |
| 本节点 → 下游 | 调用：按需补充理解材料 | [上下文 · Context](context.md) |
| 本节点 → 下游 | 调用：需要语义理解生成时 | [模型调用 · Model](model.md) |

## 参考与需要验证的选择

- [Context · 按目的装配/来源](https://app.notion.com/p/3ec6ccd32c87802fb6c2c7dd51db660d)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Runtime · 状态与循环](https://app.notion.com/p/3f06ccd32c878070921ce42ff22e6257)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

