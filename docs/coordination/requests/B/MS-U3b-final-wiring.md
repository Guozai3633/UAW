# MS-U3b 最终生命周期接线与真实认证 pending

2026-10-11；实际 `E:/UAW/.worktrees/context` / `dev/context`。这是 MS-I2l 同轮续包，不是新轮，也不是 P1/文件整链接受。

## 固定来源与提交

原HEAD `8a590123c1aa166688e7ed830e8c9c5d2d76e89b`，原工作区干净。fetch origin --tags；只读 origin/integration:docs/coordination/DISPATCH.md 正式续包记录，核对 ls-remote 与本地准确标签：

| 来源 | 固定SHA |
| --- | --- |
| 执行 ms-i2l-a8 | 06ff3ef56b68d391387bc7b154fa58ecb00571f9 |
| 源码 ms-i2l-a8-source | 16e0efaf6daff2fbbd0281473a8c6cc1f652d0e6 |
| 只读文档 ms-i2l-a8-followup | 610a920d9cc83900f056b0eb2ccfaf13cb122ff8 |

只 merge --ff-only ms-i2l-a8，开工HEAD与执行标签完全相等。新规则用git show文档tag读取，未合followup或浮动integration。读取A7 browser-installed-v1、A8 installed-file-sources与session/B；原ms-i2l-start未移动，全部原B提交/handoff保留。uv sync --frozen、原store pnpm冻结离线安装成功；本续包未改锁。

| 交付 | 提交 |
| --- | --- |
| M1 固定接口源码 | 8271fd9e7467870e6e147eb7e00ff3d583f23e8b |
| M1 阶段接口文档 | 017741b9a3a8f0bdf0b416289ea706f4c99f1f38 |
| M2 页面源码 | 81e128cf505fb7d62a1980d975b2302e6f60bd11 |
| M2 阶段构建文档 | 533fc7ca45e44381f706d28ee83fd760e53ef673 |
| 最终M3/M4源码 | 394d78579bb6841bd936b11af557bc401d0b2dba |

最终独立handoff与本页在后续docs提交；完整文档SHA见最终回报/git log。M1/M2交付后持续本包，不等待A或其他worker完成。

## 私有前端接口与错误语义

```ts
class HttpInstalledLaunchPort implements InstalledLaunchPort {
  constructor(client: UawClient, storage?: Storage);
  lookup(): LaunchLookup | undefined;
  start(signal: AbortSignal, recoverOriginal?: boolean): Promise<InstalledView>;
  get(id: string, signal: AbortSignal): Promise<InstalledView>;
  stop(old: InstalledView, signal: AbortSignal): Promise<InstalledView>;
  clear(): void;
}
// InstalledView = Schema['InstalledLaunchView']；lookup返回副本。
// LaunchLookup = {requestId, launchId?, revision?, stop?: {requestId,revision}}
```

client.localStart/localGet/localStop精确消费三个固定HTTP；严格 HttpRunnerLocalBegin/Get/StopResult，payload为InstalledLaunchView：

| 操作 | 线上请求 |
| --- | --- |
| 本人点击启动 | POST /v1/runner/local，{meta:{request_id,schema_version},payload:{}} |
| 原实例只读 | GET /v1/runner/local/{launch_id}，无query |
| 本人停止 | POST /v1/runner/local/{launch_id}/stop，payload={}、原request_id与observed expected_revision |

没有owner/path/approved/proof/module/期限/模型或flag入参，没有新API。运行时schema完整保留固定源25paths/28methods/188defs，逐定义比对包含嵌套业务description与if/then；ready必须包含enrollment_id/device_ref/expires_at，未知字段拒绝。validator导入使用标准ESM扩展名与JSON attribute，browser与Node消费同一严格源，不改公开签名或schema。

```ts
const port = new HttpInstalledLaunchPort(client);
// 仅本人点击：
const original = await port.start(signal);
// 刷新与重新打开，只读同一个已知ID：
const current = await port.get(original.id, signal);
// 本人停止，先读原实例再绑定当前CAS：
await port.stop(current, signal);
// 丢启动回复且没有id：只由本人明确点击恢复，复用原request_id：
await port.start(signal, true);
// 注销清查找记录；服务端web logout自己负责关闭/drain实例。
port.clear();
```

普通start有原ID时先GET，原实例非closed/failed/unavailable拒绝新实例；没有IDunknown拒绝换request_id，start(signal,true)仅重放原请求。GET复核原id/request/revision/workspace kind及当前身份；迟到GET与最新operation lookup比较，不回退已观察版本。stop先GET当前原版本，未知stop持有原stop ID/CAS，先GET而不重发；只由实际终态读回清掉停止对账。双击一个写入，等待后身份/Abort/clear generation复核；写前持久保存失败则不POST。确定ApiFailure清该次unknown元数据，waiting/transport/malformed/Abort保留原请求，不能冒充成功。

查找key `uaw.web.local-launch.v1` 只保存完整browser identityKey和原IDs/CAS；不持久保存state/ready/权限/root/设备/证明/正文/token/key/path。当前principal必须user；同账号新Web session也不能继承旧实例，注销/身份变化clear+Abort。权限仍每次服务端复核，lookup不会授予执行能力。

## 页面与恢复

原本机对话框内 InstalledConnection(port?,identity,connected,pollMs?,pollLimit?)，默认实HTTP，可由已认证同源host注入window.uawWebHost.installedLaunch。原设备登记/正文/逐项核验/Ref/hash/合同接受与原全局Recovery不扩展。

只有本人点击“连接本机只读目录”才POST；打开页面/对话框/切换会话/刷新不自动启动。明确系统窗口三步：账号设备确认、本人目录选择、只读范围确认。实际starting/waiting_device/connecting/selecting_directory/ready/closed/failed/unavailable及原ID/版本/原expiry/有界failure_code展示；202仅登记，ready仅连接，均不提供file Tool执行许可。材料/root/Tool/Run/审批/预算仍独立复查，未猜新目录HTTP。

串行2秒轮询，默认本次最多120读取，15秒原HTTP超时保留；终态停止，达到次数上限转手动读取，不延长native15/90/root120/lease最早期限。关闭组件/pagehide/注销/身份变化Abort清显示；错误隐藏旧ready而保留原lookup。停止时取消本组件GET并先复读CAS，unknown显示只查询。无ID丢回复提供“恢复原连接请求”，刷新不会POST。

页面ready不改变聊天模型/Run状态/草稿/审批或文件开关；原文为基准，完成仍只取服务端Run与独立接受回执，不代置completed。本包未重做Context或多Run调度，不代点native/成果接受。

## 真实认证：原拥有者上下文，当前 pending

用户明确：新launch创建新Web session，不能读取旧session的本机实例。原认证脚本已移除新launch交换，保留pending；不能用新会话接管旧实例。

A可在其原浏览器生命周期内直接复用测试帮助函数：

```ts
import {verifyOwnedInstalledPage} from './tests/u3b-readonly/owned-page';
await verifyOwnedInstalledPage(originalOwnerPage, actualOriginalLaunchId);
```

该函数不创建Page/context，不交换launch、不导出或复制cookie/storageState；只GET当前真实WebSession及原InstalledLaunchView，完整principal/原expires固定，原ID/request/version和刷新后的原身份复查；仅把经实际GET验证的原lookup ID/CAS保存到原页面允许的查找key。刷新并从页面GET原状态，结尾再GET当前身份。阻止全部非GET /v1请求，不点击连接/停止/native/接受。guard只防写，不替换服务端结果；退出时移除自己route/listener，不关闭A浏览器或注销A用户。

可选CLI附着方式（必须由A明确提供，不扫描端口）：

```powershell
# 由A受保护环境提供原上下文与唯一既有页面，不是新launch链接。
# UAW_U3B_WEB_URL = 原页面准确URL
# UAW_U3B_OWNER_CDP_URL = A明确提供的loopback原浏览器CDP入口
# UAW_U3B_LOCAL_LAUNCH_ID = 原拥有者的本机实例ID
pnpm --dir apps/web exec node scripts/u3b-readonly.mjs --authenticated
```

只接受loopback/http原page、loopback http/ws CDP、不带user/password/query凭据，原page不得含launch fragment；已有page匹配必须唯一。不创建context/page，不接管同账号的新Web session；CDP只由测试worker退出断开自己的连接，A browser/page不close。A直接调用helper时也需在本人不进行其他操作的只读检查时段使用；防写route只在检查中存在。

trace/screenshot/video关闭，PLAYWRIGHT_NO_COPY_PROMPT=1禁自动失败DOM快照，catch只给固定错误，不记录cookie、launch、proof、原正文/响应。当前三环境变量都未提供，入口exit2；u3b-authenticated-pending.json明确pending，不以收集/受控结果算真实通过。原helper只在受控Page做了一项GET/reload回归，不能宣称认证真实源已通过。未使用A私有配置、key或旧session凭据，未运行原U2真人决定suite。

## 真实回执与原失败

```powershell
uv sync --frozen
pnpm --dir apps/web install --frozen-lockfile --offline --store-dir apps/web/.store
pnpm --dir apps/web generate
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web test:e2e   # 含tsc/build，controlled only
pnpm --dir apps/web exec node scripts/u3b-readonly.mjs
pnpm --dir apps/web exec node scripts/u3b-readonly.mjs --authenticated
```

最终78单元（原66+本包12）、36受控Chromium（原29+本包7）各0失败/错误/跳过，完整原Review/Recovery兼容保留。类型、冻结安装、schema逐定义字段/重复生成字节一致、构建/diff-check通过。不累加M1 72、M2独立3、M3 77或反复浏览器次数。固定Node脚本24.21.0/宿主22.13 engine warning与>500KB chunk warning保留，不宣称性能验收。

本包较早真实匿名1节点在2026-10-11T11:20:28Z（19:20:28+08）通过，实际8000/5178 GET401/denied、刷新无POST；XML保存。后续最后复探localhost不可达/非原401，exit2/pending，u3b-anonymous.log现为最新缺源，旧成功XML单独保留时点，不称当前服务通过。没有启动/停止A服务来制造结果。认证/原拥有者实例正向读取与SQL均未由B实跑，pending A有效原上下文；A8自己的SQL/OS回执不计为B通过。

保留失败及修复：

- 新并发GET回退测试原1失败/6通过：迟到旧响应按开始时lookup比较，错误回退version；改返回前按最新lookup比较，最终9端口节点通过。u3b-m3-concurrent-initial.log/.xml保留。
- 新浏览器测试正文换行转义错误：tsc失败，未启动浏览器；修字面\n，保留u3b-m4-type-initial.log，不假报browser pass。该入口初次辅助Copy XML可能是上次旧XML，不能当本次失败或覆盖节点回执。
- 同Page验证器最初Node ESM无法加载Ajv无扩展名，继而JSON缺attribute；修标准导入，约束未变。u3b-owner-validator-initial.log/u3b-owner-json-initial.log保留；均是收集失败，不计browser节点。
- 六节点收尾复验曾被自动审批额度服务中断，动作未执行、不是unsafe判定；用户后续原上下文修改按正常审批获准，正常完成复验，没有绕审批。u3b-approval-review-interruption.json保存元数据。

最后节点/时间/原loghash/精确产物hash：自身ignored apps/web/.test-results/u3b-final-receipts.json；u3b-final-unit.log/.xml、u3b-final-browser.log/.xml、u3b-final-typecheck.log、u3b-final-generate.log、u3b-final-build.log及真实pending。受控u3b-controlled-ready.png已目视核对，原期限为fixture2099，不是真实native/window/目录或grant证据。原U3/U2各阶段回执未删。

## A只读构建消费与未通过项

A只读复制 `E:/UAW/.worktrees/context/apps/web/.test-results/u3b-final-dist/`；源码 394d78579bb6841bd936b11af557bc401d0b2dba。不要运行或安装B环境。M2独立dist/hash同样保留，以下为最后准确构建：

| 文件 | bytes | SHA256 |
| --- | ---: | --- |
| index.html | 411 | b4cdd8fa390aaa4dd13abeae3db08d1ba9cf8cb45be411d7c8b22dc4e8dc2309 |
| assets/index-BUbKOXkF.js | 813556 | 3835e36ca28637c7ac9a1b8c616c32d34257ccd6ca2d57da5a9b293d82508ee2 |
| assets/index-6xmg8RKr.css | 17880 | d5e8fd0de31fc2425cc287db863e06022dc9e3fcfac4bffef6e115b8fac43e4f |

A沿同源cookie/Origin/CSRF部署准确构建；lifecycle来源及stop/logout/drain由A owning domain负责。若注入host，只提供InstalledLaunchPort，原session身份仍必须一致，不赋Tool权限。生产configured来源默认缺时503，UI不假造空成功。A7可以立即消费，不等待A9；后续新增public DTO需A固定阶段标签，不合浮动integration。

未通过：当前认证原会话/原launch GET与刷新正向实连、本人native/目录授权、A9生产file provider与固定Run准入/文件→Context→Model→成果、本人接受/审批取消、汇合全量。SQL对本前端无直接适配场景，本包没有B SQL通过声明；相关真实后端验证由A执行。缺源与本人门槛保留pending，不称完整MS-U3b产品完成、MS-I2l/P1 accepted。默认模型/flags/子Agent/DAG/写入安装exec不变；同轮续包源码与独立handoff提交后停止，不自动扩包。

## 相对A8执行快照的全部源码/测试修改

- `apps/web/scripts/generate.mjs`
- `apps/web/scripts/u3b-readonly.mjs`
- `apps/web/src/features/devices/InstalledConnection.tsx`
- `apps/web/src/features/devices/installed.ts`
- `apps/web/src/features/workspace/Workspace.tsx`
- `apps/web/src/lib/api/client.ts`
- `apps/web/src/lib/api/generated/openapi.d.ts`
- `apps/web/src/lib/api/generated/schema.json`
- `apps/web/src/lib/api/generated/source.json`
- `apps/web/src/lib/api/validation.ts`
- `apps/web/src/main.tsx`
- `apps/web/src/styles.css`
- `apps/web/tests/e2e/controlled/u3b-installed.spec.ts`
- `apps/web/tests/installed-fixtures.ts`
- `apps/web/tests/u3b-readonly/anonymous.spec.ts`
- `apps/web/tests/u3b-readonly/authenticated.spec.ts`
- `apps/web/tests/u3b-readonly/owned-page.ts`
- `apps/web/tests/unit/installed-ui.test.tsx`
- `apps/web/tests/unit/installed.test.ts`
- `apps/web/u3b-readonly.config.ts`

文档仅B/MS-U3b-stage-interface.md、本页与handoffs/B.md。后端/公共schema/shared/composition/锁/worker均没有B修改。
