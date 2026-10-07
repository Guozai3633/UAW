# ADR-0001：工程起步与开发部署

日期：2026-10-07。范围：开发环境；不替用户决定D01的最终历史部署位置。

- 按技术栈主线使用项目内Python 3.14和uv.lock；不更换系统Python。
- 后端使用FastAPI lifespan；composition统一注入七Runtime port，未注入能力明确不可用。
- 公共Python类型只落实当前需要的子集，并以统一JSON Schema再次核验；分发副本由ops脚本同步、摘要检查防止漂移。
- 工程启动仅监听loopback，开发主体来自进程配置；此入口不作为公网账号登录。
- PostgreSQL开发实例仅用于实现/验证持久化。最终本地/服务端权威位置仍是D01；没有双主历史或云部署。
- 模型、搜索、MCP、工具执行和本地Runner尚未接入，不通过空实现宣称可用。
- LangGraph依赖单独成组锁定；本轮只核对基础导入/图API，完整工具、审批和恢复案例在P1/P5。

实际兼容修正：Windows控制面使用显式Selector loop工厂，避免Psycopg不支持默认Proactor循环；本地Runner仍在独立进程处理子进程。选择依据见[Psycopg说明](https://www.psycopg.org/psycopg3/docs/advanced/async.html)与[Python loop_factory](https://docs.python.org/3/library/asyncio-runner.html)。
