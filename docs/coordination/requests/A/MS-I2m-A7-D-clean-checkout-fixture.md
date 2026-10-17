# A7 → D：干净目录中 SQL 回执准备缺口

2026-10-17。原 MS-K1 收尾的具体修复请求，尚未发送成功。

## 准确来源和失败

D 源码 `d836bad6cf5b8d2ed04aba3811c5296f33fb0f3b`，handoff `35c43c1d4642fb0c2a2c9183a0e1f7fafb2d6ddf` 已普通合入 A；A55432 首批 [原回执](../../../implementation/evidence/ms-i2m-a7-owned-clock-first.xml)保留。

`tests/integration/run_clock/conftest.py:own_cleanup_ledger` 在 `target.open('a')` 前没有建立 `tests/.artifacts/D/MS-K1`。此目录 ignored，不随提交出现。A 干净 integration 环境中47个 SQL 节点在准备阶段报 FileNotFoundError；原 D 环境已存在该目录，54组件通过回执不作废。这不是时钟算法失败。

## 允许修改与最小结果

仅 D 已有允许路径：`tests/integration/run_clock/conftest.py` 及其专属测试、D 接线/handoff。建议在打开回执前用 `target.parent.mkdir(parents=True, exist_ok=True)` 建立准确父目录，保留 append 和已有回执。不截断或删除旧记录，不改公共 tests/conftest、Run/预算/时钟语义、公开接口或 flags。

在原 D 工作区保留最终提交，自行提交此定向修复及准确 SHA；核验全新回执目录可以运行，保留首轮失败及复跑。无需合浮动 integration，也不要求消费未发布 A7。A 的二次澄清少 tick 问题由 A 修复，不能据此改 D。

## 当前停止点

自动审批拒绝了向既有 D 会话发送本修复请求，认为这份新消息未获单独明确授权；没有把消息写入 D 的文件或改其工作区绕过。等待本人许可后再发送。A 可以在自己的 integration 建立测试所需回执目录继续受影响验证，仍明确记录原源码的准备前提，不能因此声称该源码已自行支持干净目录。
