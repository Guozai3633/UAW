# MS-I2j M1：本机浏览器身份

日期：2026-10-10。旧MS-I2i先以原固定来源完成1691项并发布 `ms-i2i / 6f1db65`；随后实现本页能力。本阶段不是MS-I2j整包验收。

## 实际交付

- 四个新HTTP：CLI用户生成一次启动链接、浏览器交换会话、读取当前身份与CSRF、退出撤销。接口精确字段见[阶段清单](../coordination/requests/A/MS-I2j-stage-api.md)。
- 独立Web签名密钥、随机短期ticket、真实PostgreSQL串行一次消费，HttpOnly/Host-only/SameSite Strict cookie；记录不含启动code、cookie、CSRF或原主凭据。
- 精确loopback Host、实际peer、Origin/GET Referer与修改CSRF校验；拒绝管理员浏览器权限和Bearer混用，转发头不能自报本机来源。
- 原无Origin的CLI Bearer路径保持。原用户API可通过会话认证受理Run，但实际后台Agent执行仍在M2；202或queued不是完成。

会话固定最多8小时、默认1小时；链接2分钟一次。服务重启同密钥可恢复，消费过的ticket不会复活；用户密钥/Origin/签名密钥变化失效，退出后的原cookie/CSRF不能再修改。配置是本机开发身份，不是公网OIDC账号。

## 本机启动

```powershell
. ./ops/start-dev-db.ps1 -Session A
.venv/Scripts/python ops/provision_dev_auth.py
.venv/Scripts/python -m uaw.application serve --config ops/browser-development.toml
# 在另一终端、同样设置开发数据库变量后取得一次URL
.venv/Scripts/python ops/web_launch.py --config ops/browser-development.toml
```

前端固定 `http://127.0.0.1:5173`。B的Vite `/v1` 代理目标8000需设置 `changeOrigin:true`（后端Host为127.0.0.1:8000），保留浏览器Origin，不启用xfwd伪造peer。或直接访问API8000并credentials:include，精确CORS只允许上述origin。默认旧启动配置没有Web开关，缺配置/来源仍不可用。

用户打开输出的短期fragment URL；B交换后立刻移除fragment，CSRF只在内存。脚本不打印管理员/模型密钥。原始HTTP请求和服务端日志不得保存这个短期code。

## 实际验证与原失败

当前最终聚焦36个不同节点通过，0失败/错误/跳过：14配置单元、20实际SQL/HTTP会话边界、原CLI兼容及新增浏览器会话→Conversation→Run受理/去重→退出后拒绝修改。

原准备命令因新回执目录不存在未启动pytest；补目录后首轮33节点中18失败/15通过，原因是新schema未同步到运行资源。同步既有 `ops/sync_runtime_contracts.py` 后原33通过；补充3个实际边界节点后36通过。旧失败XML/日志保留，最终数不累加复跑。

Ruff及核心Mypy通过。证据见[阶段回执](evidence/ms-i2j-m1.json)；[旧1691项](MS-I2i.md)来源独立，不宣称已经验证本轮运行代码。前端真实点击、模型执行、成果HTTP、人工本机选择与文件读取均留给M2–M4；写入/安装/exec、子Agent/DAG未开放。
