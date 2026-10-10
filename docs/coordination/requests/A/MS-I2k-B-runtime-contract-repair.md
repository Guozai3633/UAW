# MS-U2 实际页面契约修复请求

2026-10-10；A运行源码4c3f159，B构建来源ab14fe3063d4a1e781196aeab8a81e452cd5f207。

## 已复现

真实localhost登录成功，GET会话/列表/条目/事件/事件正文均200。B页面读取`task.frame.committed`时显示“连接中断，请重新读取”，新建/发送禁用。原合法事件的TaskFrame.output_specs[].description被B schema拒绝为additionalProperties。

`apps/web/scripts/generate.mjs`的clean对所有对象递归删除key=description，包括properties映射中的业务字段名称。当前原公共OutputSpec允许description，生成后的properties丢失该定义。此错误与A1新增登记DTO无关，同一ms-i2k-start即可复现；不能用放宽additionalProperties或跳过事件验证修复。

## B本包修复范围

1. 保留JSON Schema properties/$defs等名称映射中的所有业务字段；仅在确认是schema对象时去除说明元数据，或直接保留description说明。运行时约束及字段定义必须与固定原公共schema一致。
2. 重新生成runtime schema与类型、构建；固定来源SHA和原失败回执保留。
3. 用含OutputSpec.description的真实TaskFrame事件做生成契约回归；同时检查嵌套说明和业务description字段，拒绝非法未知字段仍生效。
4. 检查遇到一个历史读取故障时新建/恢复入口是否永久失效；按实际产品语义提供可恢复路径，不能伪造connected/Run状态。
5. 提交精确源码/交接SHA及已有构建物hash；A收到即合入、复制已交付构建物重做实际页面，不安装或执行B依赖环境。

A临时静态代理Referer漏转发已在A自己的ops修正；后端精确Origin/Referer、CSRF及原cookie策略未放宽。首次真人配对/目录授权仍独立pending。A未修改B源码或worker分支。
