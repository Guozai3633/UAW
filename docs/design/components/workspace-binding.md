# 项目绑定与本地授权：开发设计

节点 `workspace.binding` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

配对设备/Runner，明确项目根与读写执行范围。

- 计划主文件：`src/uaw/workspace/binding.py`。
- 统一业务入口：`bind/check_scope`；只允许所属 facade 或获准适配器调用。
- 上层归属：`workspace`。该节点是逻辑组件，不默认独立服务。
- 硬约束：上传路径、符号链接或子目录不能绕过根边界。

## 输入、输出与调用协议

输入请求 `WorkspaceBindingRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
device_id: ID; project_root_choice: Path; requested_capabilities: set[read,write,exec]; expected_binding_revision: int?
```

领域输出：ProjectRootBinding。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 由用户选择设备/项目根并确认能力。
2. 本地Runner解析真实路径、链接和平台边界。
3. 服务端保存设备/根/范围绑定，Runner保存本地授权。
4. 每次操作同时核对绑定/授权与实际解析路径。
5. 断开/撤销停止新动作并告知未决进程。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

绝对路径是受控元数据；服务端scope不能替代Runner真实授权。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 路径越界拒绝。
- 设备不匹配返回binding_mismatch。
- 链接逃逸拒绝。
- Runner断开不可伪装读取成功。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

只缓存绑定元数据，写/exec当前复核；敏感本地路径不送普通诊断正文。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 输入C盘路径不会获全盘访问。
- 符号链接越界被阻止。
- 切设备旧句柄无效。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/workspace.binding.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 本节点 → 下游 | 调用：获准的项目 | [输入基础状态](workspace-base.md) |

## 参考与需要验证的选择

- [Runtime · 执行环境/恢复](https://app.notion.com/p/3f06ccd32c878070921ce42ff22e6257)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · 沙箱/本地边界](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

