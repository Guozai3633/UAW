# MS-I2m A/M1：B/D可消费阶段

2026-10-16，准确source/tag见DISPATCH页首M1发布回执；共同worker开工基线仍ms-i2m-start，不移动原标签。

## B

五个固定控制HTTP已在本阶段候选源码安装，生成契约和实际OpenAPI标注0.2与`acceptance_only_no_resume`。实际字段/URL与原固定AD合同一致。`ConversationControls.view`从持久问题返回精确ID和CAS；answer/correct返回accepted原Run回执，lookup返回最新状态。标准浏览器Cookie/Origin/CSRF/退出失效已真实SQL+ASGI测，实际localhost新服务尚未部署，H01-v5保持旧快照。M4真实页面联调继续pending，不用旧端口当新服务。

## D

```python
from uaw.run.clock_sources import RunIdleEffects
# 在你的固定ExecutionClocks构造器消费同一records与此真实库存。
clocks = ExecutionClocks(records, effects=RunIdleEffects())
```

`check(tx,actor,run_id)`只在提供的原事务里读取所属会话、Run、根账本、实际Model/Tool调用与效果、逐项accounting/reservations；没有commit/新事务/假想空列表/授权或期限变更。可执行held/未结束model/unknown/未confirmed工具/未结算reservation拒绝；已知调用money pending保留且可进入真正idle。原签名/native链不在此适配器里伪造。

D的change写clock+binding，A后续改input_revision/completion_mode时须重读最新row，不能覆盖clock_ref。当前A admission/ask/reply仍使用原已验证计时逻辑，待D真实组件与CAS回执到达后由A替换；D不改conversation_entry.py。A不会临时写一个D实现或把受控clock当生产。

## 实际回执与边界

[74节点/全部失败记录](../../../implementation/evidence/ms-i2m-m1.json) · [实现策略](../../../implementation/MS-I2m-M1.md)。20不同SQL＋54契约节点最终通过；原失败和定向复跑分别保留。没有新增真实LLM请求或费用，没有启用flags或操作本人接受/本机确认。

本阶段只完成读取与受理，原Run续跑/applied/长等待、真实B页面与H02质量门槛仍待M2–M4。新控制目前附件摄取明确503，原粘贴文字64KiB/16补充限制不放宽。继续本包，不启动新包或把P1-14标accepted。
