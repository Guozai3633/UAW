# MS-K1 M1/M2 固定计量和同事务接口

目录 E:/UAW/.worktrees/runner，分支 dev/runner。原317549c干净，fetch tags/远端DISPATCH核对，
依次快进 ms-i2m-start / 1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe、
ms-i2m-a6-source / b16c69a92d81124c00fb859ce8123748f56df054，HEAD准确；uv sync --frozen 64包。
A6 wiring在源码tag后发布的metadata，从origin/integration只读读取，不合浮动分支。

阶段源码 **81d8f9989fc5825c531f9c568cf7898b1252a841**，只新增D本轮execution_clock.py和run_clock测试。

```python
from uaw.run.execution_clock import ExecutionClocks
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.clock_ports import ClockChange

clocks = ExecutionClocks(records, effects=RunIdleEffects())
original = await clocks.current(actor, run_id)  # 原持久快照，不领取/派生执行期限
# A已持有conversation:<id>锁的RecordTransaction：
changed = await clocks.change(tx, actor, run_id,
    ClockChange(original.revision, "waiting_for_user", waiting_item_ref=question_item_ref))
# A必须重读binding再改input_revision/completion_mode，不能覆盖clock_ref。
```

构造固定 `ExecutionClocks(records, *, effects:ClockIdlePort, now:Callable[[],str]=timestamp)`；
缺effects不可暂停，不启动进程/网络。current读取所属Run/conversation/protocol/input/实际clock及rev1原上限；
current原clock pin不改，调用RunExecutionClock.remaining_active_ms(可信服务时间)只读剩余，不是许可。
change只用原RecordTransaction，不commit/另开事务，严格clock CAS及binding.clock_ref/revision同tx写。
原owner/clock pin/原limit/当前具体问题和稳定Item核对，pause必需真实effects.check，await后重查来源/账本。
回调非None或异常/取消不fallback；取消/终态只可stop，stopped不复活，stop保留原在途引用。

纯measure函数是可信时间的脱离引用计量工具；原limit/revision不变，毫秒整数/真超额保存，倒退412。
变更active额度耗尽409、stop仍可保存实际超额；waiting不消耗主动额，可读长于旧deadline的原等待。
不修改Run/input/任务/预算/调用/审批/root/native/旧deadline，也不mint执行段、授权或唤醒。
A6 ExecutionSegments及候选Container装配归A；默认旧关闭兼容，D未接生产服务。

实际8单元＋2D55435 SQL通过（m2-final.xml 10 passed/1.61秒），其中真实A RunIdleEffects已消费；
等待/问题/decision来源是明确持久fixture，不是真实模型/本人回答，未访问用户文件或native窗口。
Mypy1新源码通过，Ruff/5文件格式通过。ignored tests/.artifacts/D/MS-K1保留red灯、初轮缺admission
callback/非法fixture RefKind及取错model_policy_ref的失败，修复均仅D测试；初轮类型/格式失败也保留。
此为优先阶段接口，不是全部M3/M4验证：继续本包真实SQL并发/重启/rollback/撤销与A来源/消费者接线。
全部旧Runner/A21提交、失败及清理记录保留；flags/shared/clock_ports/锁/A/B/C未改。
