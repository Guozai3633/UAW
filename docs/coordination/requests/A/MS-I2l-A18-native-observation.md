# A18：同次角色观察合并线程等待

2026-10-12，继续原MS-I2l，父发布6159bb4860c445f60ca641b94d651514d7753d6a；
运行父源码ms-i2l-a17-source / 4f4680a0522cee4574d74067e40f271313adfc79。
只改A的enrollment_peers、enrollment_candidates及A验证；不改D业务/分支、公共契约、flags或期限。
准确本阶段SHA由DISPATCH随后发布，不建立新共同start或新worker包。

## 先行候选与失败

A17纯格式计算减少后，A在新临时Run显式打开既有checked_metadata候选，
验证当前行输入单次复用/最终fresh witness与A17组合，保持完整首次成功/恢复断言。
父进程仅测试本Container，child要求fixture1、特定测试namespace和额外candidate1环境；
退出恢复False并清空locator plans，记录actual reset；没有管理员/HTTP/模型可启用的配置。
诊断入口installed_metadata_candidate.py仅显式收集，不加入默认完整链重复执行。

该候选91.01秒失败，command1/open0、无签名journal；原回复deadline没有延长，unknown不重发。
4随机凭据、2keys、child/proof清理通过，child reset确认默认关闭。候选不因此投入生产。
期间大量本机身份/key的分散线程等待仍有成本，不能将SQL输入复用当作整个问题已解决。

## 实际改动

observe_windows_role(directory, *, pid, key_id, device_id)内部只返回刚观察到的OS身份和VerificationKey。
同一worker先WindowsApi.process观察进程，关闭该本次句柄，再执行当前directory.lookup；
读取顺序与原分散调用相同，失败或后续key错误不泄漏进程句柄。没有缓存值或执行许可。

EnrolledPeerRegistry._role_observation在使用默认真实Windows观察器时调用该方法；
自定义async观察器保持原await observe +独立to_thread lookup，不能把自定义接口当同步实现。
_checked_peer仍在owning enrollment/journal/SQL等待前后各观察角色并比较原OS/key，
_external_original和user owner分支也保留原双方独立观察/比较。只将每对线程提交合成一次。

OwnedEnrollmentCandidates.current也将每角色OS/key放进同一worker。
提取_peer只是对刚读输入执行原角色/key/digest格式比较，不从proof/body中获得密钥或权限。
capture/peer原入口继续实际directory读取；候选当前性、Web账号、原行末尾新鲜复查保持。
directory/key/OS读取次数和原业务谓词不减少，SQL/两轮current/final witness/native/目录/CAS仍原样。
本次不启用checked_metadata生产候选，保留原10秒reply/30秒lease/120秒root与更早期限。

## 定向验证

| 回执 | 实际结果 | 边界 |
| --- | --- | --- |
| a18-role-unit.xml | 4通过/0.38秒 | 两次观察确实重新读OS/key，同次线程一致、句柄关闭、错误与custom async保留 |
| a18-role-sql.xml | 56通过/65.77秒 | 原SQL/候选/两角色key/账号/journal/owning owner/统一current、取消与期限 |
| a18-role-measure.xml | 1通过/25.30秒 | 实际Windows双角色原连接，两种角色等待构造结果/读取次数一致，command0/open0 |

真实Windows测量OS8→8、key8→8、SQL22→22，角色worker waits8→4。
墙钟样本0.083→0.077秒；candidate观察在两个样本中都用新机制，
所以只证明registry角色提交次数减半，不是整个旧程序/新程序或生产整链同比。
前述3份分批不同节点61，无失败/错误/跳过；历史并集由JSON计算，不称一次全量。
212源码Mypy、6受影响文件Ruff/格式通过，首次链另单独复验保留原断言/失败。

实际后续默认链55.39秒失败，command1/open1、execution claim1，无receipt_data/ref；
打开后的完整current等待被原期限取消，未完成内容读取/签名/恢复断言。
native等待合并后再测checked-input组合候选54.89秒失败，command1/open0、claim0、无签名回执，
结束确认candidate default restored。三个独立Run（含先行91.01秒候选）都没有重发unknown。
默认链6composite累计10.014秒含SQL监控与执行并行，3runner.current累计8.140秒，
不能与墙钟相加；所有original deadline一致。跨轮负载不同，不能从104.73→55.39宣称通用提速。
每实例4随机凭据/2keys/child/proof清理完成；测量command0/open0同样清理通过。
本阶段61通过、3首次链失败分别保留；373历史并集未全部重跑，466源码摘要固定。

## 来源、归属和后续

完整文件首次结果以ms-i2l-a18.json为准；候选失败与default新链不能混为同一source/成功。
运行native输入/审批/model-provider初始元数据为受控，实际Web/SQL/OS/keys/双进程为真实；
不访问用户材料、不触发真人窗口、无新模型调用、flags不变。
B/C/D保留当前交付点，无新worker包。A继续原注册/发送与重复来源图成本，业务缺陷才返原worker。
未知命令不重发；未完成签名journal不得造回执或推not_applied/零费用。
固定模型材料成果、准确引用/Verification、原本人接受和汇合全量仍待实际完成。
实际证据见docs/implementation/evidence/ms-i2l-a18.json。
