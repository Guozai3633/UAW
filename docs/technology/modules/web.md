# Web：聊天、成果与用户控制 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Node.js](https://nodejs.org/en/about/previous-releases) | `Node.js` | 前端构建环境 | 24 LTS / P1 |
| [pnpm](https://pnpm.io/installation) | `pnpm` | 前端依赖与锁文件 | 稳定版/Node 24兼容 / P1 |
| [React](https://react.dev/learn) | `react/react-dom` | 聊天与工作区UI | 19.x稳定组合 / P1 |
| [TypeScript](https://www.typescriptlang.org/docs/) | `typescript` | 前端严格类型 | 稳定版/strict模式 / P1 |
| [Vite](https://vite.dev/guide/) | `vite/@vitejs/plugin-react` | SPA开发与静态构建 | Node 24兼容稳定版 / P1 |
| [Tailwind CSS](https://tailwindcss.com/docs/installation/using-vite) | `tailwindcss/@tailwindcss/vite` | 产品样式和主题token | 4.x / P1 |
| [Radix Primitives](https://www.radix-ui.com/primitives/docs/overview/introduction) | `所用@radix-ui/react-*包` | 对话框/菜单/开关的交互基础 | 与React兼容稳定版 / P1 |
| [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview) | `@tanstack/react-query` | 服务端状态读取/刷新 | 5.x稳定线 / P1 |
| [React Router](https://reactrouter.com/start/declarative/installation) | `react-router` | 项目/会话/成果导航 | 稳定版，declarative模式 / P1 |
| [Monaco Editor](https://github.com/microsoft/monaco-editor) | `monaco-editor` | 实际代码/文本Diff查看 | 稳定版/worker自托管 / P1/P3 |
| [react-markdown](https://github.com/remarkjs/react-markdown) | `react-markdown/remark-gfm` | 安全报告和引用展示 | 稳定版/原始HTML关闭 / P1/P2 |
| [PDF.js](https://mozilla.github.io/pdf.js/) | `pdfjs-dist` | 获准PDF页预览 | 稳定版/worker自托管 / P2，格式范围待D05 |
| [Ajv](https://ajv.js.org/json-schema.html) | `ajv/ajv-formats` | 前端2020-12边界校验 | 8.x / Ajv2020 / P1 |
| [openapi-typescript](https://openapi-ts.dev/introduction) | `openapi-typescript/openapi-fetch` | 从契约生成HTTP类型/客户端 | 稳定版/OpenAPI 3.1验证 / P1 |
| [Dexie/IndexedDB](https://dexie.org/docs/) | `dexie` | 账号隔离的页面缓存与草稿 | 稳定版 / P4 |
| [Playwright](https://playwright.dev/docs/intro) | `@playwright/test` | 真实页面与API事件场景 | 稳定版＋对应浏览器锁定 / P1 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 页面骨架

React+TypeScript+Vite做SPA，Tailwind主题token与Radix交互组件组成自有视觉层。React Router负责项目/会话/成果导航；TanStack Query管服务端读取，组件局部状态管草稿和展开。首版不再叠加独立SSR服务或多个全局状态库。

主界面保留会话侧栏、聊天、输入框上方浅色理解提示、成果/变更侧区。‘努力奔跑中’等文案由真实事件状态映射，事实进度和需介入事项仍显示；动画系统后续单独设计。

### 类型、事件和缓存

openapi-typescript/openapi-fetch从已实现API契约生成客户端。Ajv2020校验SSE/Runner展示数据等动态载荷，不能用默认draft-07模式加载2020-12；自定义format显式登记，未知格式不能静默跳过。

事件客户端用fetch ReadableStream解析SSE，支持AbortController、cursor、重复seq去重和最终快照；ItemReducer从协议更新内容，不能解析LLM文字猜命令完成或进度百分比。

Query cache是读取投影。P4用Dexie/IndexedDB保存显式允许的草稿/近期页面投影，按issuer/subject/workspace/配置纪元分区；退出/换账号/撤销清理。令牌、审批与权威Run状态不持久缓存；离线只显示标明版本的内容，不继续执行获准动作。

### 变更与引用

Monaco Diff展示实际ChangeSet，局部选择以服务端unit ID提交，版本Hash/CAS由Workspace决定。react-markdown禁用原始HTML并校验URL协议；PDF.js按获准Reference取内容，worker与资源自托管。

生成HTML预览置独立受限来源/iframe，不携带控制面cookie；可执行脚本、联网等能力另限制。引用走ReferenceResolver，未知本地路径不能点击读取。局部接受、撤销、模型继承和memory开关各自对应真实API。

### 页面验证

Playwright验收真实提交/审批/取消/SSE重连/Diff/局部接受/角色创建及权限拒绝。Mock用于控件错误分支，阶段验收另保存真实后端和模型回执。UI可展示可信状态，不代替后端授权。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `ui` | React、TypeScript、Vite、Tailwind CSS、Radix Primitives、TanStack Query、React Router、Ajv、openapi-typescript | 真实Item/Event驱动页面，详情按需展开；技术模块web | [设计](../../design/components/ui.md) / [接口](../../api/nodes/ui.md) |

## 4. 目录与依赖位置

- `apps/web/src/features/`
- `apps/web/src/lib/api/`
- `apps/web/src/lib/events/`
- `apps/web/src/lib/cache/`
- `apps/web/src/components/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P1-10 最小API与真实聊天工作区](../../plan/rounds/P1-10.md) | 让用户从页面完成第一条任务和审阅。 | planned |
| [P2-08 角色与子任务页面](../../plan/rounds/P2-08.md) | 用户可查角色、修改配置并了解子任务结果。 | planned |
| [P3-06 块级审阅、局部应用与撤销](../../plan/rounds/P3-06.md) | 用户能选择具体改动和反馈位置。 | planned |
| [P3-07 复杂运行干预与多会话任务](../../plan/rounds/P3-07.md) | 处理目标修订、排队、部分交付和同用户共享任务。 | planned |
| [P4-09 草稿提示、用户控制与完整管理页面](../../plan/rounds/P4-09.md) | 完成实际能力的可理解交互，区分用户和管理员。 | planned |
| [P5-05 单用户工作区受控试用准备](../../plan/rounds/P5-05.md) | 把可用能力交给真实用户，保留账号和设备边界。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

