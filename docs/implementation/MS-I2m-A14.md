# A14：提供方报告换行编码兼容

2026-10-18。处理[H02-I02本人失败](human-tests/H02-I02.md)，范围仅A拥有的Model adapter；B/C/D、公共schema、用户模型配置、提示词、锁及flags均保持。

| 目录 | 策略 |
| --- | --- |
| `src/uaw/model/structured_text.py` | 先严格解析；明确json_object模式才允许字符串内LF/CR/TAB的确定性等价转义；再次严格解析，不修改结构或字符串值 |
| `src/uaw/model/adapters.py` | 仅完整stop的结构输出消费兼容函数，随后按原完整schema校验；原raw/text/usage保持 |
| `tests/unit/model/test_structured_whitespace.py` | 18节点覆盖正文保持、转义/引号/反斜杠、重复键/NaN/NUL/截断/包裹/非法结构拒绝、原生模式严格和一次发送 |
| `tests/integration/model/test_structured_whitespace_postgres.py` | 2新真实SQL节点：原raw/text/structured_data持久化，严格拒绝额外字段，重读幂等与费用不免费 |

实际两个失败响应离线回放通过；正文未改、模型未重发，原Run仍failed。共29单元＋4SQL节点通过（含11原adapter/2原gateway回归），248源码类型通过；原复现5失败/13通过与静态格式修正保留。[逐项证据](evidence/h02-i02-a14.json)。

## 边界与后续

此修复处理已观察到的JSON字符串换行编码问题。错误引号、缺括号、未知动作/参数、截断、外层无效响应仍拒绝；不使用通用JSON修复库或自动模型重试。它不能保证所有提供方响应成功，也不证明报告事实正确。

长期仍应降低控制结构和长正文耦合：原文生成、正式成果、动作授权需各自有明确边界；不能把未经核验的正文猜成工具动作。本轮不重写既有公开协议，先完成该具体缺陷的固定候选、真实报告及H02体验更新。实际部署回执另记录，不把离线回放当服务已修复。

## 实际部署与同题诊断

H02-v5已使用本轮固定源码和原B前端，原数据库/认证/settings保持。2次真实模型调用形成可读报告（2506字），阶段耗时22.581秒、5455输入/1827输出Token、2笔金额未知pending；原两个失败调用与费用不归零。新响应本身合法，兼容分支由两份原实际响应回放及SQL证明。不是一般性能或事实准确率保证。

切换前确认无未完成任务，39条原失败相关记录逐项未变，旧失败仍failed；原Page已连接。探针只取消自己的待接受诊断，不替本人接受或重发。H02-v4及更早快照保留，当前版本按DISPATCH与`.data/human/H02-current.json`定位。
