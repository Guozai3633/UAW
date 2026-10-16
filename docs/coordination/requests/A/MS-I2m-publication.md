# MS-I2m固定基线与同步回执

共同标签 `ms-i2m-start`，准确源码 `1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe`，2026-10-16。

[分包范围](MS-I2m-parallel-packages.md) · [固定接口](MS-I2m-AD-contract.md) · [四份提示词](MS-I2m-session-prompts.md) · [机器摘要](../../../../planning/current-dispatch.json) · [接口验证](../../../implementation/evidence/ms-i2m-preparation.json)。

## worker开工

```powershell
git status --short
git fetch origin --tags
git show origin/integration:docs/coordination/DISPATCH.md
git rev-parse 'ms-i2m-start^{commit}'
# 上述SHA必须为 1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe
git merge --ff-only ms-i2m-start
git rev-parse HEAD
```

只在自己的原worktree/分支执行，工作区干净；HEAD与固定SHA一致后按锁同步独立环境。发布前只读检查三个原分支均为共同源码祖先；若之后自身又有新提交使不能快进，保留现场向A报告，不reset/rebase/stash、不改写原提交或合浮动integration。A保留本checkout发布元数据HEAD，不退回worker基线。

基线内准备行是提交时状态；固定标签不会包含后续发布记录。远端DISPATCH正式SHA+tag同时一致即满足开工，不以旧准备行重新阻断。

## 固定文件摘要

| 文件 | SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `5cf32a6fa9ae227a4b91e6cedc63e4db98e4d045b73bfacdcbf33d381895721c` |
| `contracts/conversation_catalog.py` | `d108c3e23c9ae19a846e063eb5b1517842a738e53ded05748120ae5a8760d9d1` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `src/uaw/shared/ports.py` | `4c80e4666c2c7cfe3bf8befec48e8d7a6d864f5ae94abef0b1d729720567aa21` |
| `src/uaw/shared/conversation.py` | `bff466f64f2fc37692dc9f60f3d97146a9b3815510898b272cafb53259eb3e00` |
| `src/uaw/run/clock_ports.py` | `6c924e0859f7304e0f5960835e113968ae2a28ae3f6dbce0d50bd97b3ae56461` |
| `uv.lock` | `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f` |
| `src/uaw/resources/prompts/conversation-v1.txt` | `fa6ee17b82bfadfd2c514acc893265df2e987f612f08eeaf7267d50d7f70ed47` |

摘要校验共同接口/锁/提示词来源，不能替代业务/授权或实际模型验收。不要为了同步摘要重写原失败证据。公共变更由A合入并发布新的具名阶段SHA，不移动此标签。

## 本次实际门槛

54个相关节点最终通过；初轮6失败（runtime包schema漏同步、原接口数量断言）与原JUnit保持；221源码类型、4文件静态/格式通过。现有1399 schema结构完全相同，新增3结构，打包schema字节同源；1402正例与336反例通过。当前worker允许路径互不重叠，51历史及当前包、56主轮、296接口关联和新文档链接核对通过。没有SQL或真实模型新调用，没有新增模型费用。

本次不启动H02、不替用户发送或接受，不修改H01-v5快照/账号/历史/flags。新五个控制HTTP仍implemented=false，待A真实阶段接线；D clock与C评测尚待各worker实现。
