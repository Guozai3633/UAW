"""Connection authority uses real SQL; HTTP responses remain controlled fixtures."""

import pytest

from tests.integration.model.test_gateway import case as case
from tests.integration.test_control_plane import domain as domain
from tests.integration.test_control_plane import meta
from uaw.model.connection import ModelConnectionAcceptance
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError


async def test_connection_requires_owned_finished_matching_probe(case, domain):
    config, run, admin = domain
    service = ModelConnectionAcceptance(config)
    provider = Ref.model_validate(case.request["model_config"]["provider_ref"])
    with pytest.raises(DomainError):
        await service.accept(
            admin, provider, case.ctx.principal, case.ctx.attempt_id, meta("missing", 2)
        )
    assert (await run.store.get(config.platform, "providers", provider.id)).payload[
        "state"
    ] == "disconnected"
    result = await case.model.generate(case.request, case.ctx)
    assert result["kind"] == "ok"
    with pytest.raises(DomainError):
        await service.accept(
            case.ctx.principal,
            provider,
            case.ctx.principal,
            case.ctx.attempt_id,
            meta("not-admin", 2),
        )
    other = case.ctx.principal.model_copy(update={"id": "unrelated-probe-owner"})
    with pytest.raises(DomainError):
        await service.accept(admin, provider, other, case.ctx.attempt_id, meta("other-owner", 2))
    active = await service.accept(
        admin, provider, case.ctx.principal, case.ctx.attempt_id, meta("connect", 2)
    )
    assert active["state"] == "active" and active["revision"] == 3
    configured = await run.store.get(config.platform, "provider.configs", provider.id)
    assert configured.revision == 3 and active["config_ref"]["version"] == "3"
    assert (
        await service.accept(
            admin, provider, case.ctx.principal, case.ctx.attempt_id, meta("connect", 2)
        )
        == active
    )
    assert len(case.requests) == 1


async def test_connection_rejects_finished_failed_or_mismatched_probe(case, domain):
    config, run, admin = domain
    service = ModelConnectionAcceptance(config)
    provider = Ref.model_validate(case.request["model_config"]["provider_ref"])
    result = await case.model.generate(case.request, case.ctx)
    assert result["kind"] == "ok"
    row = await run.store.get(case.ctx.principal, "model.invocations", case.ctx.attempt_id)
    await run.store.put(
        case.ctx.principal,
        row.namespace,
        row.resource_id,
        row.schema_name,
        {**row.payload, "state": "claimed"},
        expected_revision=row.revision,
        request_id="unfinished",
    )
    with pytest.raises(DomainError) as denied:
        await service.accept(
            admin, provider, case.ctx.principal, case.ctx.attempt_id, meta("reject-incomplete", 2)
        )
    assert denied.value.failure.code == "connection_probe_invalid"
    current = await run.store.get(case.ctx.principal, row.namespace, row.resource_id)
    await run.store.put(
        case.ctx.principal,
        row.namespace,
        row.resource_id,
        row.schema_name,
        {
            **row.payload,
            "result": {
                "kind": "failed",
                "output_refs": [],
                "failure": {
                    "code": "test_failure",
                    "category": "model_protocol",
                    "message": "Controlled failed result",
                    "retryable": False,
                },
            },
        },
        expected_revision=current.revision,
        request_id="failed",
    )
    with pytest.raises(DomainError) as denied:
        await service.accept(
            admin, provider, case.ctx.principal, case.ctx.attempt_id, meta("reject-failed", 2)
        )
    assert denied.value.failure.code == "connection_probe_invalid"
    assert (await run.store.get(config.platform, "providers", provider.id)).payload[
        "state"
    ] == "disconnected"
