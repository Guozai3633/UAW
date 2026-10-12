# A16：D SQL/本机监控续项精确合入验收

2026-10-12，继续原 MS-I2l，上一 A 发布 ed429c6232505f86e98bf073efb977861dccc0e5。
D 最终源码 c3153522617a719e9f92f922116f54418d946544、独立 handoff
92259195c50bbf59e42e83de804b0ab39e81bf50 合入 A integration，merge
71a0d319070ac64764947d331c842d48ae7cf698。M1源码c5b310f、阶段文档492d825、
原预算说明6247b72、最终说明5cb6243一起保留原历史；没有替worker同步或修改其业务源码。

## 审阅与实际装配

1. ReadOnlyHelper 原 current_source 非空时，向 endpoint 显式装配
   LocalReadInvalidation(helper.roots)，同一 NativeRootSource 与 Reader/registry/directory/credential。
   A15原installed super参数已经兼容，无需新增公共 DTO/port 或配置。
2. 原 frame/ref/channel/actor 只选择独立来源，watch 自己读取原 Reader 和纯 factory，
   SQL初始化在独立 task 执行，不借用 dispatch 的允许结论。
3. connection检查立即开始：真实双方 key/OS/live pipe/local OS private 当前匹配；
   active 分支同时运行原 wait_changed 与 native SQLite Ticket/grant/签名/根检查。
   任一路正常返回、异常、取消、到期均终止 work，取消并 drain 监控任务。
4. SQL wait_changed 初次完整校验后仅比较原捕获输入变化；实际执行仍完整 current/CAS/句柄检查。
   旧签名 journal（含重复command）继续独立数据权限，不启动 active execution SQL monitor。
5. 普通15秒/首次90秒、reply10秒、lease30秒、root120秒及更早源期限保持。
   不缓存allowed、不延deadline、不使用SQL unchanged授予执行；unknown不重发。

D报告271不同节点通过，包含248受影响回归、8 SQL消费者和15真实installed失效来源；
该数字是worker分批去重，不作为A重新全量测试。按组件/接口接受，不将完整MS-R2或产品标完成。

## A合入后定向回归

- 32项通过，36.87秒：监控终止/原deadline、本机双方key/OS/私钥/pipe/root失效、
  实际双进程原signed journal恢复、8实际SQL变化消费者。
- 2项通过，147.85秒：实际installed Web账号退出与lease变化停止受控执行等待；
  command各1/open各0；每实例4凭据不存在、2keys撤销、child退出、proof关闭。
- 212源文件Mypy、11受影响文件Ruff/格式通过；无新模型调用、本人操作、用户正文或flags修改。

这34项是分批定向，非全量。原1691全量属于MS-I2i；历史回执不重新累加为当前全量。
历史累计不同节点346未全部重跑；458源码摘要已更新。实际首次文件链另单独保留原成功断言运行：
**1失败/59.56秒，command1/open1，原一次execution claim1，receipt_data/ref均空**。
工具返回invocation_interrupted；未完成内容/签名/原journal恢复断言，不重发unknown。
所有6次composite与1次wait_changed使用同一原reply期限，3次runner.current累计7.967秒，
6次composite累计10.252秒包含监控初次current的并行，不能与墙钟相加。
独立本机监控133次/2.180秒，全生命周期123次session.check/10.694秒，不是单个reply段成本。
随机4凭据/2keys/child/proof清理完成；此失败不计入34通过节点。
不会把受控执行等待的两项误报为真实文件成功。

## 当前剩余工作归属

D当前组件包已交付，停在原点；A承担原登记/发送/生产来源成本和真实汇合。
打开后的current仍须完成两轮完整来源和外部本机复查。初次SQL监控也跑一个完整图，
不能把其并行累计时间与执行墙钟相加，也不能仅靠减少后台轮询推断原reply达标。
后续优化必须用同一固定source/Ref/owner语义对比SQL次数与效果边界，生产输入优化仍默认关闭。

A优先处理自己所属原source重复展开/发送前检查；有新D业务缺陷才给原worker具体修复。
B/C保持交付点，不分配缺输入的等待包，不开启子Agent/DAG/写入安装exec。
原材料→Context→固定模型→准确引用/Artifact/Verification→原本人接受与汇合全量仍待实际通过。

当前进度入口已更新：[2026-10-12](../../../implementation/PROGRESS-2026-10-12.md)。
实际回执：[A16](../../../implementation/evidence/ms-i2l-a16.json)。
