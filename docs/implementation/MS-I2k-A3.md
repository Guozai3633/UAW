# MS-I2k A3：首次候选、控制证明与真实页面修复

2026-10-10。阶段交付；不是本轮整链接受或全量回归。

## A新增与真实边界

- `OwnedEnrollmentCandidates.capture`只供可信本机组装调用，从D已准备但未启动的自有helper、独立Windows进程实例、当前角色目录和已认证Web owner生成候选。正文/API/模型不能提交PID、公钥或approved来登记。持久Reader每次复查完整owner、原角色key、两OS实例、期限和原记录；重建Reader也不能放过撤销或退出。
- `WindowsEnrollmentControlProof.issue`只签服务保存的原登记挑战，控制进程必须是原OS实例；OS密钥读取前后复查双方角色、私钥/公钥、原challenge及当前认证。普通RunnerCommand签名门槛未改变，不让任意JSON借此进入命令签名入口。
- native producer必须显式检查控制证明verify的返回值，错误证明在凭据读取/弹窗前拒绝；同时检查当前key_id/device_id。原完成服务本来已拒绝错误证明，此修复把拒绝提前到实际窗口之前。
- `assemble_enrollment_sources(container,directory=...)`显式绑定这些当前来源和原native journal Reader；默认compose不启用。实际首次控制证明到独立设备的保护交付、本人窗口与D已配对factory仍需生产接线。账号设备确认不授予目录；实际目录选择/文件到模型仍pending。
- `FirstEnrollmentDeviceFactory`在D已配对factory之前运行：先验当前设备/原控制证明，真实native producer产生双方签名journal后提交原登记active，再调用已配对factory。缺first-proof transport或下游factory在弹窗前不可用；重读active不重弹窗，当前来源抛错/撤销时释放已分配的自有helper。保护交付port默认缺失，不伪造已配对peer来解除启动循环。

## 验证

23个不同受影响登记节点最终通过，包含原20个当前Web/SQL、签名/CAS、实际OS凭据/helper候选节点，另加first-device缺源/错证明/受控Yes激活与清理3节点。原20节点运行于0d8e633源码；随后显式composition在1f10bf6用同一个候选节点定向复跑，覆盖新装配与缺真人证据拒绝。不能把20＋同节点复跑计为21个不同节点。188核心/Runner源码Mypy通过；核心、改动的测试及新ops代理Ruff通过。

受控Yes只替换native窗口结果，实际OS设备匹配、OS密钥、密码学、原SQL与owning journal仍实跑；控制候选/双方角色fixture受控。此节点不是真人选择、真实首次保护交付或生产D helper/IPC接受，实际窗口未打开。

初次控制测试把普通命令签名的ContractViolation误期待成DomainError，按真实合同纠正；随机OS测试凭据在finally删除并404复查。3文件单独Mypy首次未加载Runner源码，完整187源码检查通过；广扫旧ops发现12个既有格式问题，原日志保留，本阶段检查范围明确为当前核心和本轮新ops，未修改无关运维脚本。实际组装的导入排序失败已修复并复查。

## 实际页面

A用B已交付构建物提供localhost静态页面，核对每份源码/日志/构建hash，不安装依赖、不执行或修改B环境。A代理漏转Referer已修，后端精确Origin/Referer、CSRF、cookie未放宽。

实际认证页面发现B生成器误删业务description定义，B修复3799b92/6c74937已合入3f67e54；原TaskFrame已实际显示、新建恢复。实际UTF-8文本参数被拒绝，B修复106fecdb/31951f6再次精确合入并复验，完整正文和逐项核验已显示。B对应48/20与后续51/21是各自覆盖，不能累加为独立节点或称真人验收。

新的办公原文确实通过页面提交，原Run为run-eb7af1282636488f99e6559898e0623f。3次真实固定DeepSeek已返回，模型用量与未结费用单独记录；合同需要用户接受，未接受不能说completed。页面对running状态的合同等待错误禁用接受正在同包修复，完整真实wire已给B只读参考。学术会话与草稿已创建，但原全局Recovery暂阻止发送，原查阅ID保留，不删除缓存或重发。

## 下一门槛

继续原办公接受/完成、刷新原请求恢复，随后学术、审批拒绝/取消和真实native文件链；全部模型失败、费用未结及页面失败逐项保留。只有实际消费者汇合后做一次全量，上次1691仍单独留旧来源。本阶段不发布新开发包，不启用子Agent/DAG/本机写入安装exec或默认文件flags。
