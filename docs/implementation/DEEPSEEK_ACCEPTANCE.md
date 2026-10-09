# DeepSeek 实连与任务验收

日期2026-10-09。此前缺实际模型与受保护凭据，只有受控协议测试。用户提供模型名和凭据句柄后，已完成13次真实调用及办公、文本工具、学术三个最终有界样例；原失败和修复保留。[实际报告](MS-I2h-A3.md) · [回执](evidence/ms-i2h-a3-live.json)。

## 1. 凭据录入

在E:/UAW的交互式PowerShell终端运行：

```powershell
. ./ops/start-dev-db.ps1 -Session A
.venv/Scripts/python.exe ops/provision_dev_auth.py
.venv/Scripts/python.exe ops/store_provider_key.py --provider-id deepseek-live
```

最后一个命令使用隐藏输入，把凭据写入Windows凭据库，通过实际ConfigurationService登记CredentialMetadata。只输出provider_id、credential_handle和版本；不启动HTTP服务器，不打印Key，不保存到Git或命令参数。它要求受保护的本机开发管理员身份和实际开发数据库。用户提供输出句柄、期望模型名与实际endpoint后，A再登记和发布提供方/模型配置。

已有配置可直接给句柄和模型ID；provider-id与CredentialMetadata的绑定必须匹配。当前句柄已核验属于deepseek-live；用户显示模型DeepSeek-V4.1-Flash对应deepseek-flash，真实鉴权模型清单也核验通过。[官方说明](https://api-docs.deepseek.com/news/news260910/)。私人测试材料和完整输出保存在ignored `.data`/私有Blob，公开验收记录只收脱敏状态、来源和摘要。

## 2. 显式协议配置

DeepSeek官方接口列出的结构化返回是`json_object`，与原适配器的原生`json_schema`格式不同；当前模型和参数必须按其[Chat Completions文档](https://api-docs.deepseek.com/api/create-chat-completion/)及[JSON输出指南](https://api-docs.deepseek.com/guides/json_mode/)确认。

管理员配置示意，模型名和credential_handle使用实际批准值：

```json
{
  "id": "deepseek-live",
  "kind": "model",
  "endpoint": "https://api.deepseek.com/v1",
  "profile_ref": {"kind": "provider_profile", "id": "model.chat_completions", "version": "1"},
  "credential_handle": "实际录入返回的句柄",
  "settings": {
    "model_name": "deepseek-flash",
    "timeout_ms": 60000,
    "output_token_parameter": "max_tokens",
    "reservation_money": "0.25",
    "allow_temperature": false,
    "structured_output_mode": "json_object",
    "include_n": false,
    "reasoning_levels": ["none"],
    "default_reasoning_level": "none"
  }
}
```

以上仍是配置形状示例，当前实际开发配置已通过ConfigurationService发布。`reservation_money`只是每次开发尝试的预留估计，不能当实际单价或账户费用上限。真实用量读API响应，未知费用仍由账本保留；不得把pending记成免费。

`json_object`模式发送JSON格式和明确schema指令，UAW仍用同一个有界JSON Schema验证完整返回，错误结果不能进入工具执行。其含义是UAW的schema校验协议可用，**不声称供应商原生严格保证schema**。省略该字段保持原有`json_schema`请求，不对供应商报错自动降级。实际原生请求包含schema指令的完整估算，再走预算/窗口准入。

默认推理档位必须在管理员批准的reasoning_levels中，并写入ModelOutput.actual_config；用户明确提供的档位优先。include_n只控制是否发送n=1；返回仍只允许一个choice。缓存命中/未命中的DeepSeek用量别名需与总输入数一致，不伪造缓存命中或账单。

## 3. 真实验收顺序

1. **连通与协议。** 使用已有`ops/model_probe.py`，固定模型发送明确的小任务，核对实际模型名、结束原因、Token和输出；再验证JSON对象加本地schema拒绝行为。
2. **理解与执行。** 输入真实的办公、开发或学术小样例，核对原文/修订、实际TaskFrame、根固定模型、工具选择、审批、真实结果和下一步回答。
3. **规则与工具质量。** 多规则冲突用实际固定Model评估器验证；工具向量召回须另有真实embedding提供方。不能把已知数值向量叫作语义质量，也不能假设DeepSeek聊天API就是embedding服务。
4. **成果验收。** 核对引用和实际成果，保存失败/返工原因。答复成功、HTTP200、框架END都不自动标Run.completed；缺独立交付核验仍明确不可用。

每项记录实际提供方/配置/模型版本、调用次数、原始回执的私有路径与摘要、取消/未知发送行为和费用状态。具体费用额度及样例在正式执行前按实际Run预算与用户输入约束；不连接真实用户项目、不开放本机写入/安装/exec。

## 4. 当前状态

- 已接入实际DeepSeek-V4.1-Flash / deepseek-flash，13次调用包含首次失败；总输入17895、输出3525 Token。Usage报告缓存2176 Token；解析失败调用的缓存明细没有进入Usage，不能把它当完整缓存总数。费用pending。
- 三个最终小样例及31个不同受影响回归通过；办公直接回答，文本任务由模型选择工具、脚本批准精确只读动作、执行与观察后回答，学术样例说明观测与不确定性。运行未标completed，未证明通用专业成果质量。
- 真实调用与受控自动回归分别登记，受控HTTP/数值embedding仍只验证组件机制。首个办公引用定位失败、学术截断与JSON漏字段失败都有独立回执，没有用后一次成功覆盖原失败。
- 多规则、工具检索与Windows只读组件已在MS-I2h-A2按组件接受；实际Model评估器、真实embedding、生产认证/IPC/用户确认、专业交付和公开flags仍按各自门槛验收。

## 5. 有界实跑命令

每次明确的新逻辑验收使用唯一request-id。既有回执不能直接覆盖或盲目重试。

```powershell
. ./ops/start-dev-db.ps1 -Session A
.venv/Scripts/python.exe ops/agent_probe.py --model-id deepseek-flash --text-file .data/your-task.txt --request-id your-explicit-new-probe --max-steps 3 --max-output-tokens 2048
```

需测试精确文本工具审批时，显式追加 `--approve-text-inspection`；它只授权开发样例的原始只读text.inspect，不是自动批准任意动作。输入/完整输出不提交Git，输出限额和当前账本继续执行。
