# 固定模型实连操作说明

本轮可执行明确的模型诊断调用；自动Agent任务尚未接入。管理员先按[控制层说明](CONTROL_PLANE.md)存储密钥、登记模型及发布配置。

## 1. 选择明确协议

提供方改用 `model.chat_completions@1`；将下列示例替换成获批准的实际配置，`.invalid`不能连通：

```json
{
  "provider": {
    "id": "approved-provider",
    "kind": "model",
    "endpoint": "https://provider.invalid/v1",
    "profile_ref": {"kind": "provider_profile", "id": "model.chat_completions", "version": "1"},
    "credential_handle": "使用密钥写入返回的实际句柄",
    "settings": {
      "model_name": "approved-model",
      "timeout_ms": 30000,
      "output_token_parameter": "max_completion_tokens",
      "reservation_money": "0.25",
      "allow_temperature": false
    }
  }
}
```

输出参数选择 `max_completion_tokens`或`max_tokens`必须按供应商实际支持确定。推理档位通过可选reasoning_levels声明；响应别名通过allowed_response_models声明，二者都不表示可以替换目录模型。reservation_money是每attempt的开发USD额度估计，不是费用；未知账单仍保留额度。

旧profile的settings没有这些声明，不能直接联网。更新提供方需当前expected_revision，再登记引用新修订的模型、创建新配置草案并校验/激活。只开放实际验证支持的text/json_schema/tool_calls能力。

## 2. 显式执行一次模型调用

在 `.data/prompt.txt`写入希望发送的原文，然后从项目根目录执行：

```powershell
./ops/start-dev-db.ps1
.venv/Scripts/python.exe ops/model_probe.py --model-id 实际目录模型ID --text-file .data/prompt.txt --request-id first-model-check --max-output-tokens 512
```

该CLI需要本机受保护的用户身份和数据库配置。它创建明确选模的会话、保存原文、准备最小诊断快照、进行模型调用。不会打开代码/文件工具、换模型或把模型返回误记为整个任务完成。CLI不需要后端HTTP服务同时运行。

输出包括conversation_id、run_id、ModelOutput/明确失败；完整文本在私有Blob中。成功回执摘要写到忽略的 `.data/model-probes/`，只含配置、Token、结束原因、内容摘要等，不含认证头或完整正文。若结束原因是length/refusal，需继续审阅结果，不能仅以kind=ok认定任务成功。

同request-id与原参数重读既有结果，不再发送；改内容/模型/输出上限使用新request-id。可加 `--conversation-id`继续已有会话，但该会话的固定模型必须与model-id一致。claimed未完成的调用明确提示需要核对，CLI不能自行清空意图后重发。

## 3. 验收记录

确认供应商实连、实际模型名、Token与缓存字段及费用状态，再把脱敏结果补入[P0-05](P0-05.md)。当前自动测试是协议fixture；没有账户密钥和实际回执时不宣称模型连通、计费准确或任务质量合格。
