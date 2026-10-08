# B / MS-C3：通用模型输入的最小接线说明与提案

日期：2026-10-08。基线 `ms-i2c` / `1411f6aa477b0d000bee871c0f324fbfd67b4ff5`。
状态：组件待 A 审阅；B 未改输入路由、production authority、共享 DTO/锁或能力 flags。

## 公开入口和已有格式

`uaw.context.model_input.GenericModelInputs(composer: Composer | None)`
提供 `async resolve(ref: dict[str, Any], ctx: TrustedExecutionContext) -> ModelPrompt`，
结构兼容 A 发布的 ModelInputPort。不导入 ProviderRequest/ProviderResponse；仅只读导入 ModelPrompt。

A 可注入 `GenericModelInputs(context_components.composer)`。Composer 不存在（包括未注入通用 authority/仓储）时明确 capability_unavailable。此组件只读取 `context.generic.*` 快照；不能用它自动解析 A 的诊断/understanding 专用命名空间。根据来源命名空间/purpose 的生产输入路由仍由 A 决定，禁止失败后把 agent_step 送进理解模板。

`ModelPrompt.tools` 保留实际 ModelToolSet 中的完整 ToolSpec 字典。ms-i2c 的 ModelGateway 按 ToolSpec 校验，provider adapter 才将其转换为 native function.name/parameters。因此 B 不在公开结果中改成 provider 私有格式，也不自造函数名。消息与工具 schema 均计入估算。

## 最小公共改动及消费方

1. A 在 composition 的通用 Context 依赖齐全后创建并注入该解析器；Model 输入路由选择真实固定快照所属命名空间，而非从模型参数推测或 fallback。
2. A 提供目的对应真实 CompositionAuthority/RuleProvider，以及当前真实工具发现结果的能力 Reader；缺少时整个通用分支保持不可用。当前 Reader 检查授权、删除、版本/hash，authority.verify 检查真实 epoch、源依赖、模型/权限政策、工具提供方/角色/资源/flags。
3. A 的 Model Gateway 继续在发送前检查当前执行政策/flags、完整 native 请求（包括输出 schema 和参数）及预算/取消。Context 输入不授权任何动作，不替 Tool 执行准入。
4. 若生产 role/history/tool result 需要原生 assistant/tool 消息和工具 call IDs，先由 A 发布具有实际身份/版本的 port；本包将这些已有 Reading 当来源数据，不假造对话角色。
5. 没有新 HTTP 字段、公共 schema、依赖、迁移、持久写入或事件。消费方只为 A 的组装与 ModelInputPort 路由；现有 seed.py/intent.py 以及 ModelProvider 类型/逻辑保持原样。

## 消息/数据/模型边界

- 从持久固定 InstructionSet 及实际已读规则取得文本，平台和能力政策规则仅在 platform 信任下成为 system 消息。
- 当前用户要求为原始 user 文本；项目/技能/角色/偏好为带 level、scope、source_ref、text 的 registered_instruction JSON user 消息，保持原优先级信息，不升为 system。
- 原始输入 user_input/user 逐字作为 user 消息（空格、CRLF、Unicode、数字不转换）；如果同源已作为当前用户规则发送，只发一次。
- 材料/历史/记忆/工具结果为 context_kind=data 的 JSON user 消息，携带实际来源、kind/trust 和精确 text。资料中的 role/system 或新增工具字符串不能变为结构性系统消息/工具定义。此处验证的是身份/序列化边界，未证明真实 LLM 的语义注入防护。
- 能力集合自身的 JSON 不重复作为用户指令发送；tools 完全来自真实固定读取，只有实际读取结果为空时才返回空 tuple。缺 Reader/authority、源消失/撤销或变化均失败。
- 依次校验固定快照/Run/Scope、完整 Manifest/块/InstructionSet、当前规则/依赖/保护/epoch、能力源和模型窗口；最后再次复核。没有 prompt 缓存、来源写入或修改原文。
- 返回 estimated_tokens 是 UTF-8 JSON 保守估算，计入完整 messages、ToolSpec 的输入/输出 schema 及元数据，加每项序列化余量，并不低于已有快照估算。保留输出/工具及模型 envelope 空间；窗口不足明确 context_insufficient，不能删条件/换模型。
- 撤销和真实发送存在跨域竞态；重复复核不等于跨服务原子授权。A 的发送边界必须继续检查政策/租约/取消。

## 可执行例子和必要验证

B 的 unit fixture 完全标记为受控来源/内存仓储；examples.json 包含成功 prompt、重复、跨 Run 拒绝、撤权、来源 stale 和窗口不足真实组件回执。路径 `tests/.artifacts/B/MS-C3/examples.json`。

真实 SQL 代码 `tests/integration/context/test_model_input_postgres.py` 提供 15 个用例。
快照、受理原文、政策/取消/模型目录和测试规则/工具/epoch/材料实际持久保存；通用规则、工具和 CompositionAuthority 是明确测试注册，不宣称生产 Tool/Runner/LLM 已接入。
包括新数据库连接和新 Python 进程重建 resolver：子进程读取 PostgreSQL，使用发布的 Windows control_plane_loop，连接配置仅通过 stdin，不进命令参数或回执。

B 无 UAW_TEST_DATABASE_URL，仅收集成功，交 A 安排实际运行：

```powershell
./.venv/Scripts/python.exe -m pytest tests/integration/context/test_model_input_postgres.py -q --require-postgres
```

A 在合入 SHA 先跑本包 unit/SQL，再回归 MS-C2、理解专用输入、Model 原生计数与全链路。若需改更宽公共接口，A 公布新固定基线后消费。D01/D03/D06 与完整 P1-02/Agent 的接受状态不由本组件改变。

## 回退

B 新 resolver/测试独立提交，A 的路由接线另提交。正常 revert 不删已有 Context 快照，也不影响现有理解专用 builder；ModelPrompt 是公开边界，provider native 格式继续归 Model owner。
