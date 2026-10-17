# MS-E1 离线评测输入

ms-e1-interface 是明确构造的 CLI 示例，不是真实模型输出或人工核对。所有样本 needs_human_review，provenance=controlled_fixture，模型标识 not-a-real-model。

schema唯一类型源：src/uaw/evaluation/contracts.py；导出读本：docs/implementation/evaluation/MS-E1-schemas.json。样本/观测 hash 为规范 JSON SHA256，原输入文件字节 hash 另记报告，不混用。提供方/模型配置与 prompts 固定于 manifest，由 A 原 owning 导出，不让候选答案修改。

命令：`.venv/Scripts/python.exe ops/evaluate_conversation.py --suite tests/fixtures/evaluation/ms-e1-interface/suite.json --manifest tests/fixtures/evaluation/ms-e1-interface/manifest.json --observations tests/fixtures/evaluation/ms-e1-interface/observations.jsonl --reviews tests/fixtures/evaluation/ms-e1-interface/reviews.jsonl --output tests/.artifacts/C/MS-E1/interface-report.json`。

预期退出3/incomplete，pending USD0.02不是确认账单；没有Reviewer为N/A。第二次同路径退出2，不覆盖旧报告。退出0仅完整门槛通过，1 blocked，2 输入/IO拒绝，3 incomplete。没有网络、模型、SQL、真实账号或工具重放。
