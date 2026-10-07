from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from uaw.shared.errors import CapabilityUnavailable, DomainError
from uaw.shared.schema import ContractViolation
from uaw.workspace.binding import RootBindings
from uaw.workspace.ports import Admission
from uaw.workspace.repository import MemoryAdmissionRepository, MemoryRootRepository

from .conftest import NOW, wire


def test_selection_single_use_and_missing_trusted_adapter(setup):
    _, selection, bindings, _, authority, _, _, _ = setup
    options = dict(
        principal_id="u1",
        device_id="d1",
        workspace_ref=authority.value.workspace_ref,
        capabilities=frozenset({"read"}),
        now=NOW,
    )
    with pytest.raises(DomainError):
        bindings.bind(selection, **options)
    with pytest.raises(CapabilityUnavailable):
        RootBindings(MemoryRootRepository()).bind(selection, **options)
    options["capabilities"] = frozenset({"read", "exec"})
    with pytest.raises(CapabilityUnavailable):
        bindings.bind(selection, **options)


def test_expired_selection_is_not_consumed(setup):
    _, selection, bindings, _, authority, _, _, _ = setup
    expired = selection.model_copy(update={"expires_at": NOW.isoformat()})
    with pytest.raises(DomainError) as error:
        bindings.bind(
            expired,
            principal_id="u1",
            device_id="d1",
            workspace_ref=authority.value.workspace_ref,
            capabilities=frozenset({"read"}),
            now=NOW,
        )
    assert error.value.failure.code == "stale_resource"


@pytest.mark.parametrize(
    "path",
    [
        "../outside",
        "/absolute",
        "C:relative",
        "C:/root",
        "\\\\server/share",
        "source.txt:stream",
        "source.txt.",
        "NUL",
    ],
)
def test_unsafe_path_dialects_are_denied(setup, path):
    _, _, bindings, _, authority, _, _, _ = setup
    with pytest.raises((DomainError, ContractViolation)):
        bindings.check_scope(
            root_handle="r1",
            principal_id="u1",
            device_id="d1",
            workspace_ref=authority.value.workspace_ref,
            expected_revision=0,
            relative_path=path,
        )


def test_revocation_cas_and_retry_do_not_restore_access(setup):
    _, _, bindings, command, _, _, _, protocol = setup
    protocol.admit(wire(command), now=NOW)
    revoked = bindings.revoke("r1", expected_revision=0)
    assert revoked.revoked and revoked.revision == 1
    with pytest.raises(DomainError) as error:
        bindings.revoke("r1", expected_revision=0)
    assert error.value.failure.code == "revision_conflict"
    assert bindings.revoke("r1", expected_revision=1) == revoked
    with pytest.raises(DomainError, match="revoked"):
        protocol.admit(wire(command), now=NOW)


def test_binding_principal_device_and_root_identity(setup):
    root, _, bindings, _, authority, _, _, _ = setup
    options = dict(
        root_handle="r1",
        principal_id="u1",
        device_id="d1",
        workspace_ref=authority.value.workspace_ref,
        expected_revision=0,
        relative_path="source.txt",
    )
    assert bindings.check_scope(**options) == root / "source.txt"
    for field in ("principal_id", "device_id"):
        with pytest.raises(DomainError):
            bindings.check_scope(**{**options, field: "other"})
    grant = bindings.repository.get("r1")
    bindings.repository._roots["r1"] = replace(grant, file_identity=(-1, -1))
    with pytest.raises(DomainError):
        bindings.check_scope(**options)


def test_atomic_concurrent_deduplication_and_conflict():
    repository = MemoryAdmissionRepository()

    def reserve(index):
        return repository.reserve("u1", "d1", Admission("cmd", str(index), "digest"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(reserve, range(32)))
    assert len(set(results)) == 1
    with pytest.raises(DomainError):
        repository.reserve("u1", "d1", Admission("cmd", "retry", "changed"))
