# MS-I2h-A2：三份组件审阅集成与 DeepSeek 验收准备

日期2026-10-09。A / E:/UAW / integration。**本阶段开发集成范围接受；完整MS-I2h和P1仍未接受。**

## 1. 审阅与合入

| 包 | 最终源码 / handoff | 正常merge | 复核结果 |
| --- | --- | --- | --- |
| B / MS-C6 | 467b743 / 1cd90da | 2969551 | 14个允许文件；246单元＋105不同SQL，共351通过 |
| C / MS-T2e | 27fe04f / 94c7506 | 32961fd | 11个允许文件；218单元＋124不同SQL，共342通过 |
| D / MS-R2e | ced4137 / 7d6ee06 | cb087d0 | 13个允许文件；431通过；真实Windows签名/读取回执passed、cleaned |

核对实际分支/HEAD、工作区干净、固定基线祖先、逐文件目录归属、最终源文件与提交摘要、公共文件不变，以及原始JUnit。C的100项原SQL有1个超时；保留原失败，用未改变断言/时限的3项模块复跑与最终24项SQL去重，当前124个SQL节点均有通过回执。原worker分支、worktree、提交和标签没有改动，没有聊天派发。

原始回执已复制到A版本化[evidence目录](evidence/ms-i2h-workers/B-final-unit.xml)，完整计数/摘要/文件列表及接受范围见[审阅索引](evidence/ms-i2h-worker-receipts.json)。各模块覆盖有共享回归，不能把三个总数相加当项目完成度。

## 2. A实际接线和修复

- `composition.assemble_registered_context(..., rule_assessor=...)`消费B正式port。默认无真实评估器，多规则仍明确不可用；受控建议没有被安装成生产LLM。
- `assemble_text_tool(..., retriever=...)`及`assemble_agent_runtime(..., retriever=...)`接C检索；Agent Context从实际候选重新读取ToolSpec，复查权限/目录，最多32个检索候选。默认小目录兼容，semantic-required缺embedding仍不可用，不用hash向量伪造语义。
- 根Agent的JSON决策此前没有看到`ModelPrompt.tools`里的工具。现在把当前过滤后的工具固定Ref、描述和input_schema登记成external材料，同时保留独立ModelToolSet验证；描述不能授权，模型选择后仍由Tool Runtime审批/预算/参数检查。
- 同topic/value的语义建议不能证明两段重要规则正文完全相同。保留不同的重要正文，只有已验证的显式纠正才替换；平台/权限规则保护与冲突处理继续有效。
- 接受D精确提案：仅`FileContent.text`提升至65536字符，通用Text仍16384；实际Runner返回仍限64KiB UTF-8、全文1MiB。实际ASCII64KiB读取、Unicode字节限制、句柄/签名/去重恢复已验证。未接生产IPC/本机确认，也未把Runner ok直接推断成Tool applied。
- 模型配置显式增加JSON-object模式、include_n和批准的默认推理档位；本地schema校验、完整原生输入估算及实际配置记录保留。默认原生JSON-schema模式不变，不自动降级或换用户模型。DeepSeek缓存用量别名必须与输入总数一致。

详细参数与目录见[A接线](../coordination/requests/A/MS-I2h-Agent-wiring.md)、[B](../coordination/requests/B/MS-C6-final-wiring.md)、[C](../coordination/requests/C/C-008-ms-t2e-index-wiring.md)、[D](../coordination/requests/D/MS-R2e-ports.md)。新凭据CLI为`ops/store_provider_key.py`，TTY隐藏输入不可用时停止，不回退明文读取。

## 3. A实际验证

去重**421个不同通过节点**；当前接受覆盖无失败/错误/跳过。Ruff、228文件格式和包含CLI的Mypy138源码通过，合同与来源摘要另有检查回执。完整里程碑没有重跑；上次完整1077仍对应ms-i2g。

原始批次及最终通过节点来源见[证据索引](evidence/ms-i2h-a2.json)、[去重汇总](evidence/ms-i2h-a2-accepted-tests.xml)：

| 实际批次 | 结果及后续 |
| --- | --- |
| 合入受影响组件/Windows读取 | 208通过/1新测试失败；错误为测试对None调用实例估算方法，生产方法未改，9项adapter复跑通过 |
| Context规则兼容 | 246项通过，覆盖重要规则正文保留修正 |
| 原跨模块批次 | 2通过/2失败；通过的是原实际审批→text→观察→下一Model链及原Model默认行为 |
| 多规则/检索定向修复 | 多规则实际登记→build→ModelPrompt通过；发现JSON决策工具定义不可见，保留失败 |
| 最终工具可见性 | 1项实际根步骤通过：新检索、实际固定模型、JSON-object请求、默认none档位、工具定义可见、Run未completed |

后续成功覆盖最初所有失败节点；汇总使用最新通过结果，重复用例不累加。最后工具可见性调整只复跑受影响根节点，不声称最后修改后执行完整421项单批。HTTP响应、embedding数值和多规则语义建议受控；真实SQL/Windows计算是真的，实际LLM质量仍未验证。

## 4. 为什么之前没做真实LLM，以及现在需要什么

此前没有管理员批准的实际提供方/模型和API Key，无法发送可信的真实调用。当前JSON兼容代码与隐藏录入工具已准备，**真实LLM调用数仍为0**，没有凭据时不能把fixture记作DeepSeek通过。

用户在本机录入Key后提供credential_handle和模型名；随后登记/发布配置，先实连协议，再跑真实理解、根任务、工具选择和质量样例。完整步骤、命令及官方协议来源见[DeepSeek验收说明](DEEPSEEK_ACCEPTANCE.md)。当前固定Model规则评估器、真实embedding、生产认证/IPC/用户确认与专业交付仍待完成。

默认公开Runtime绑定与flags不变，写入/安装/exec未开放。三个worker组件按各自范围接受；本阶段标签与代码提交见[DISPATCH](../coordination/DISPATCH.md)。
