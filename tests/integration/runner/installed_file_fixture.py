"""Real A8 Web/SQL/OS/IPC sources, disposable controlled native/config decisions.

No product flags, existing Run sources, human UI or external model are changed.
"""

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import delete

from tests.integration.agent.test_installed_launch import cleaned
from tests.integration.test_browser_sessions import ORIGIN, envelope, login
from tests.integration.test_control_plane import meta, seed
from tests.integration.test_runtime_sources import profile
from uaw.infrastructure.blob.filesystem import FSBlobStore
from uaw.infrastructure.db.models import OutboxRow
from uaw.infrastructure.db.transactions import reference
from uaw.infrastructure.enrollment_launch import PreparedEnrollmentLaunch
from uaw.infrastructure.installed_files import assemble_installed_file
from uaw.infrastructure.installed_lifecycle import InstalledLifecycle
from uaw.infrastructure.installed_receipt import current_root
from uaw.shared.contracts import Principal, Ref, Scope, TrustedExecutionContext
from uaw.tool.providers.file_read import file_read_spec
from uaw.tool.registry import AdapterBinding, ToolRegistry

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class InstalledFileCase:
    container: object
    client: object
    owner: Principal
    workspace: Ref
    ctx: TrustedExecutionContext
    root: Path
    trace: Path
    headers: dict
    metrics: dict = field(default_factory=lambda: {"queries": {}, "phases": {}, "sends": []})
    bindings: object = None
    identifier: str = ""
    grant: object = None
    raw: dict = field(default_factory=dict)

    @asynccontextmanager
    async def phase(self, name):
        started = time.perf_counter()
        try:
            yield
        finally:
            self.metrics["phases"][name] = time.perf_counter() - started
            await asyncio.to_thread(
                (self.trace.parent / "phase-metadata.json").write_text,
                json.dumps(self.metrics),
                encoding="utf-8",
            )

    async def approve(self):
        async with self.phase("approval_query"):
            waiting = await self.bindings.tool.facade.invoke(self.raw, self.ctx)
        assert waiting["kind"] == "waiting", waiting
        assert (
            await self.bindings.tool.ledger.get(
                "tool.budget.reserved", self.ctx.attempt_id, self.ctx
            )
            is None
        )
        async with self.phase("controlled_sql_decision"):
            service = self.bindings.tool.approvals
            record = await service.get(self.owner, waiting["wait_ref"]["id"])
            await service.decide(
                self.owner,
                {
                    "approval_id": record["id"],
                    "decision": {
                        "decision": "approve_once",
                        "expected_arguments_hash": record["arguments_hash"],
                        "expected_resource_refs": record["resource_refs"],
                        "reason": "D controlled disposable test decision; not human consent",
                    },
                },
                meta("d-fixture-decision", record["revision"]),
            )
        return waiting

    async def child_metrics(self):
        return await asyncio.to_thread(lambda: json.loads(self.trace.read_text(encoding="utf-8")))


async def new_run(c, owner, workspace):
    config, run = c.configuration, c.run_service
    admin = Principal(
        id=c.settings.development_admin_id, kind="admin", auth_session_id="d-admin-fixture"
    )
    # Explicit component availability fixture BEFORE new Run; production default stays empty.
    c.tool_access.implemented_flags = frozenset({"file_access"})
    active = await seed(config, admin)
    # BEFORE a new Run: fixture-only connected model metadata, no model request.
    row = await c.records.get(config.platform, "providers", "fixture-provider")
    await c.records.put(
        config.platform,
        "providers",
        row.payload["id"],
        "ProviderBinding",
        {**row.payload, "revision": 2, "state": "active"},
        expected_revision=1,
        request_id="d-fixture-provider-connected",
    )
    model = (await c.records.get(config.platform, "models", "fixture-model")).payload
    await config.register(
        admin,
        "model",
        {
            "entry": {
                k: v
                for k, v in {
                    **model,
                    "provider_ref": reference("provider", row.payload["id"], 2),
                }.items()
                if k not in {"revision", "status"}
            }
        },
        meta("d-model-fixed", 1),
    )
    value = {
        **active,
        "revision": 4,
        "provider_refs": [reference("provider", row.payload["id"], 2)],
        "model_refs": [reference("model", "fixture-model", 2)],
        "feature_flags": [
            {**f, "enabled": f["id"] == "local_files"} for f in active["feature_flags"]
        ],
    }
    await c.records.put(
        config.platform,
        "configurations",
        active["id"],
        "ConfigurationVersion",
        value,
        expected_revision=3,
        request_id="d-new-fixture-config",
    )
    await c.records.put(
        config.platform,
        "configuration.pointer",
        "current",
        "Ref",
        reference("configuration", active["id"], 4),
        expected_revision=1,
        request_id="d-new-config-pointer",
    )
    conv = await run.create_conversation(
        owner,
        {
            "title": "D disposable installed chain",
            "model_choice": {"mode": "explicit", "model_id": "fixture-model"},
            "memory_policy": {
                "revision": 0,
                "read_enabled": False,
                "contribute_enabled": False,
                "scope": {"resource_refs": []},
            },
        },
        meta("d-conversation"),
    )
    admitted = await run.submit(
        owner,
        {
            "conversation_id": conv["id"],
            "text": "保留  原文\r\n固定用户模型",
            "attachment_refs": [],
        },
        meta("d-new-run"),
    )
    await run.advance(owner, admitted["id"], "preparing", meta("d-prepare", 1))
    binding = (await c.records.get(owner, "run.bindings", admitted["id"])).payload
    assert binding["configuration_ref"] == reference("configuration", active["id"], 4)
    capabilities = ["tool.invoke", "workspace.process", "file.read"]
    policy = {
        "id": "d-disposable-policy",
        "revision": 1,
        "allowed_capabilities": capabilities,
        "denied_capabilities": [],
        "resource_scope": {
            "conversation_id": conv["id"],
            "task_id": admitted["task_id"],
            "resource_refs": [workspace.wire()],
        },
        "network_allowlist": [],
        "feature_flag_refs": [],
    }
    await c.records.put(
        owner,
        "execution.policies",
        policy["id"],
        "CapabilityPolicy",
        policy,
        expected_revision=0,
        request_id="d-policy",
    )
    ctx = TrustedExecutionContext(
        principal=owner,
        scope=Scope(
            principal_id=owner.id,
            conversation_id=conv["id"],
            task_id=admitted["task_id"],
            capabilities=tuple(capabilities),
            resource_refs=(workspace,),
        ),
        conversation_id=conv["id"],
        task_id=admitted["task_id"],
        run_id=admitted["id"],
        operation_id="d-file-operation",
        trace_id="d-file-trace",
        attempt_id="d-file-attempt",
        deadline=admitted["budget"]["deadline"],
        capability_policy_ref=Ref.model_validate(reference("policy", policy["id"])),
        model_policy_ref=Ref.model_validate(binding["model_policy_ref"]),
    )
    registry = ToolRegistry()
    spec = file_read_spec(Ref.model_validate(value["provider_refs"][0]))
    registry.register(
        spec,
        expected_revision=0,
        binding=AdapterBinding(
            Ref.model_validate(spec["provider_ref"]), frozenset({"development"}), implemented=True
        ),
    )
    tool_ref = Ref.model_validate(registry.reference(registry.snapshot()[1][0]))
    role = await c.tool_access.register_role(
        profile(spec["categories"]), meta("d-role", 0), authenticated_service=config.platform
    )
    await c.tool_access.bind(
        ctx, role, meta("d-role-bind", 0), authenticated_service=config.platform
    )
    return ctx, registry, tool_ref


@asynccontextmanager
async def installed_file_case(web, tmp_path, monkeypatch):
    c, client = web
    c.blobs = FSBlobStore(tmp_path / "private-blobs")
    public = await login(client)
    owner = Principal.model_validate(public["principal"])
    workspace = Ref(kind="workspace", id="d-disposable-workspace", version="1")
    root = tmp_path / "disposable-root"
    await asyncio.to_thread(root.mkdir)
    await asyncio.to_thread((root / "read.txt").write_bytes, "actual 中😀\r\nKeeṕ exact  ".encode())
    ctx, registry, tool_ref = await new_run(c, owner, workspace)
    c.settings = c.settings.model_copy(
        update={
            "installed_state_directory": tmp_path.resolve(),
            "installed_workspace_id": workspace.id,
        }
    )
    c.installed_lifecycle = InstalledLifecycle(c)
    trace = tmp_path / "child-metadata.json"
    case = InstalledFileCase(
        c,
        client,
        owner,
        workspace,
        ctx,
        root,
        trace,
        {"Origin": ORIGIN, "X-UAW-CSRF": public["csrf_token"]},
    )
    get = c.records.get

    async def measured_get(*args, **kwargs):
        started = time.perf_counter()
        try:
            return await get(*args, **kwargs)
        finally:
            row = case.metrics["queries"].setdefault(args[1], {"calls": 0, "seconds": 0.0})
            row["calls"] += 1
            row["seconds"] += time.perf_counter() - started

    c.records.get = measured_get
    prepare = PreparedEnrollmentLaunch.prepare

    async def controlled_prepare(*args, **kwargs):
        env = dict(kwargs["environment"])
        env["PYTHONPATH"] += os.pathsep + str(ROOT)
        env.update(
            UAW_D_INSTALLED_FIXTURE="1",
            UAW_D_FIXTURE_BASE=str(tmp_path.resolve()),
            UAW_D_FIXTURE_ROOT=str(root.resolve()),
            UAW_D_METRICS=str(trace.resolve()),
        )
        return await prepare(*args, **{**kwargs, "environment": env})

    monkeypatch.setattr(
        "uaw.infrastructure.enrollment_launch.MODULE",
        "tests.integration.runner.installed_file_child",
    )
    monkeypatch.setattr(
        "uaw.infrastructure.installed_lifecycle.PreparedEnrollmentLaunch.prepare",
        controlled_prepare,
    )
    try:
        async with case.phase("web_launch_to_callback_ready"):
            response = await client.post(
                "/v1/runner/local", headers=case.headers, json=envelope("d-installed-original")
            )
            assert response.status_code == 202, response.json()
            case.identifier = response.json()["payload"]["id"]
            async with asyncio.timeout(150):
                while True:
                    view = await c.installed_lifecycle.record(owner, case.identifier)
                    if view["state"] in {"ready", "closed", "failed", "unavailable"}:
                        break
                    await asyncio.sleep(0.2)
            assert view["state"] == "ready", view
        launch = c.installed_lifecycle.active.launch
        await asyncio.to_thread(
            (tmp_path / "private-cleanup-locator.json").write_text,
            json.dumps(
                {
                    "namespace": c.settings.platform_id,
                    "handles": launch.handles,
                    "roles": str(launch.state.path),
                }
            ),
            encoding="utf-8",
        )
        case.grant = await current_root(launch)
        async with case.phase("a8_assembly"):
            case.bindings = await assemble_installed_file(
                c,
                owner=owner,
                workspace=workspace,
                registry=registry,
                tool_ref=tool_ref,
                provider=Principal(id="d-file-service", kind="service", auth_session_id="internal"),
                money_ceiling="0.05",
            )

        def measure(port, method, label):
            original = getattr(port, method)

            async def measured(*args, **kwargs):
                started = time.perf_counter()
                try:
                    return await original(*args, **kwargs)
                finally:
                    row = case.metrics.setdefault("operations", {}).setdefault(
                        label, {"calls": 0, "seconds": 0.0}
                    )
                    row["calls"] += 1
                    row["seconds"] += time.perf_counter() - started

            setattr(port, method, measured)

        for port, method, label in (
            (c.budgets, "reserve", "budget_reserve"),
            (c.budgets, "dispatch", "budget_dispatch"),
            (c.execution_leases, "acquire", "lease_acquire"),
            (case.bindings.control.commands, "register", "command_register"),
            (case.bindings.control.commands, "collect", "command_collect"),
            (case.bindings.bridge, "resolve", "bridge_source_checks"),
            (case.bindings.bridge.pipe, "read", "signed_pipe_exchange"),
        ):
            measure(port, method, label)
        case.raw = {
            "tool_ref": tool_ref.wire(),
            "action_id": "d-original-read",
            "arguments": {"workspace_ref": workspace.wire(), "path": "read.txt"},
        }
        session = case.bindings.bridge.pipe.session
        send = session.send

        async def counted_send(kind, body):
            case.metrics["sends"].append(kind)
            return await send(kind, body)

        session.send = counted_send
        yield case
    finally:
        entry = c.installed_lifecycle.active
        cleanup_failure = None
        async with case.phase("cleanup"):
            try:
                await c.installed_lifecycle.close_owner(owner)
            except BaseException as exc:
                cleanup_failure = exc
                case.metrics["cleanup_failure"] = type(exc).__name__
            if entry is not None and entry.launch is not None:
                # Drain the exact owned launch even if A lifecycle stop itself fails.
                # The original failure is re-raised below, never relabelled as passed.
                await cleaned(entry.launch)
                case.metrics["cleanup"] = {
                    "credential_handles_absent": len(entry.launch.handles),
                    "role_keys_revoked": len(entry.launch.keys),
                    "child_exited": entry.launch.helper.process.poll() is not None,
                    "proof_pipe_closed": entry.launch.proof.listener is None
                    or entry.launch.proof.listener.connection.closed.is_set(),
                }
        if trace.exists():
            case.metrics["child"] = await case.child_metrics()
        await asyncio.to_thread(
            (tmp_path / "metadata.json").write_text, json.dumps(case.metrics), encoding="utf-8"
        )
        c.records.get = get
        async with c.database.sessions.begin() as session:
            await session.execute(
                delete(OutboxRow).where(OutboxRow.principal_id == c.configuration.platform.id)
            )
        if cleanup_failure is not None:
            raise cleanup_failure
