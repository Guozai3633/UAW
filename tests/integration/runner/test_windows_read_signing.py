"""Real Windows vault/control+device signing/read/journal, random namespace cleaned.
Confirmation, ownership and channel are explicit controlled fixtures, NOT actual IPC.
"""

import json
import uuid

from uaw_runner.keys import ProtectedSigner

from tests.integration.runner.test_native_root_source import bind, make_native_case
from tests.integration.runner.test_read_executor import (
    child_registry,
    child_run,
    configure,
    execute,
)
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.shared.errors import DomainError


async def test_actual_os_keys_signed_read_journal_restart_and_cleanup(tmp_path):
    namespace = "D-MS-R2e-test-" + uuid.uuid4().hex
    handles = ["device-" + uuid.uuid4().hex, "control-" + uuid.uuid4().hex]
    store = WindowsCredentialStore(namespace)
    report = {
        "backend": "keyring.backends.Windows.WinVaultKeyring",
        "namespace": namespace,
        "handles": handles,
        "status": "not_verified",
        "cleaned": False,
        "channel": "controlled_component_fixture_not_IPC",
    }
    attempted = False
    try:
        for handle in handles:
            try:
                await store.resolve(handle)
            except DomainError as exc:
                assert exc.failure.code == "credential_missing", "Actual OS backend unavailable"
            else:
                raise AssertionError(
                    "Random handle already exists; no existing credential modified"
                )
        attempted = True
        case = await make_native_case(
            tmp_path, credentials=store, device_handle=handles[0], control_handle=handles[1]
        )
        await bind(case)
        case["tmp"] = tmp_path
        case["target"] = case["root"] / "os-file.txt"
        case["target"].write_bytes("actual OS signed read 中😀\n".encode())
        await configure(
            case, parameters={"workspace_ref": case["workspace"].wire(), "path": "os-file.txt"}
        )
        receipt = await execute(case)
        assert (
            receipt.kind == "ok"
            and receipt.payload["result"]["text"] == "actual OS signed read 中😀\n"
        )
        # Reopen actual vault, prove current key hold and sign the same observed receipt.
        signer = ProtectedSigner(case["state"], WindowsCredentialStore(namespace))
        await signer.check_private(device_id="d1", key_id="device1", credential_handle=handles[0])
        assert (
            await signer.sign_document(
                receipt.wire(),
                device_id="d1",
                key_id="device1",
                domain="receipt",
                credential_handle=handles[0],
            )
            == receipt.signature
        )
        recovered = await child_run(await child_registry(case), "recover")
        assert recovered["receipt"] == receipt.wire()
        report["status"] = "passed"
        report["receipt_command_id"] = receipt.command_id
        report["receipt_attempt_id"] = receipt.attempt_id
        report["file_hash"] = receipt.payload["result"]["content_hash"]
    finally:
        if attempted:
            for handle in handles:
                try:
                    await store.resolve(handle)
                except DomainError as exc:
                    assert exc.failure.code == "credential_missing"
                else:
                    await store.delete(handle)
                try:
                    await store.resolve(handle)
                except DomainError as exc:
                    assert exc.failure.code == "credential_missing"
                else:
                    raise AssertionError("Random credential cleanup failed")
            report["cleaned"] = True
        (tmp_path.parents[1] / "windows-read-receipt.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
