# 共享支撑与控制层 · 接口入口

[总覆盖图](../COVERAGE.md) · [详细设计](../../../docs/design/modules/support.md)

计划代码：`src/uaw/shared/__init__.py`。状态：完整节点仍按设计建设，已实现操作见下方接口及实施记录。

这是相关独立设施的汇总入口，不引入第八条Runtime流水线。下面列出各子组件接口。

- [http · connections.list](../interfaces/http--connections-list.md)
- [http · connections.begin](../interfaces/http--connections-begin.md)
- [http · connections.revoke](../interfaces/http--connections-revoke.md)
- [http · admin.configuration.get](../interfaces/http--admin-configuration-get.md)
- [http · admin.configuration.stage](../interfaces/http--admin-configuration-stage.md)
- [http · admin.configuration.validate](../interfaces/http--admin-configuration-validate.md)
- [http · admin.configuration.activate](../interfaces/http--admin-configuration-activate.md)
- [http · admin.providers.configure](../interfaces/http--admin-providers-configure.md)
- [http · admin.secrets.put](../interfaces/http--admin-secrets-put.md)
- [http · admin.policies.register](../interfaces/http--admin-policies-register.md)
- [http · admin.providers.revoke](../interfaces/http--admin-providers-revoke.md)
- [component · support.configuration](../interfaces/component--support-configuration.md)
- [http · skills.list](../interfaces/http--skills-list.md)
- [http · admin.extensions.install](../interfaces/http--admin-extensions-install.md)
- [http · admin.extensions.activate](../interfaces/http--admin-extensions-activate.md)
- [http · admin.extensions.revoke](../interfaces/http--admin-extensions-revoke.md)
- [http · admin.extensions.validate](../interfaces/http--admin-extensions-validate.md)
- [http · admin.extensions.rollback](../interfaces/http--admin-extensions-rollback.md)
- [component · support.extensions](../interfaces/component--support-extensions.md)
- [http · sources.delete](../interfaces/http--sources-delete.md)
- [http · memory.forget](../interfaces/http--memory-forget.md)
- [http · admin.policies.register](../interfaces/http--admin-policies-register.md)
- [component · support.cache](../interfaces/component--support-cache.md)
- [http · admin.traces.list](../interfaces/http--admin-traces-list.md)
- [component · support.observability](../interfaces/component--support-observability.md)
- [http · admin.evaluations.run](../interfaces/http--admin-evaluations-run.md)
- [http · admin.evaluations.get](../interfaces/http--admin-evaluations-get.md)
- [component · support.evaluation](../interfaces/component--support-evaluation.md)
- [component · support.stores](../interfaces/component--support-stores.md)
