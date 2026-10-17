# 明确受控的错误/重试/Reviewer漏判统计样例

三条构造观测：旧answer失败、原逻辑请求第二attempt返回构造错误6、构造Reviewer verdict=passed；独立标签basis=controlled_test，明确不是人审或真实模型。

用于核对：attempt=3、failure=1、retry=1、input_tokens known=22、output_tokens known=6且unknown_attempts=1、active=1700ms、attempt墙钟和=3000ms、实验墙钟=3000ms。构造金额confirmed=0.07/pending=0.02 USD，不是现实账单、实际新费用或用户预留；零可接受输出的单位成本N/A。

答案错误1/1、Reviewer漏判1/1；样本needs_human_review、human_reviewed_cases=0、各率provisional。CLI预期退出1/blocked（已知受控反例），仍保留人工未审与controlled provenance，不能把这组计成实际模型失败或发布结果。
