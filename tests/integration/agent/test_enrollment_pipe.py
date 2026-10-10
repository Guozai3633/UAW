"""Actual Windows two-process pipe and SQL; child challenge/owner are controlled fixtures."""

import asyncio
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import SecretStr
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi
from uaw_runner.state import LocalState

from tests.integration.agent.test_enrollment_postgres import enrollment_case as enrollment_case
from tests.integration.test_browser_sessions import web as web
from tests.integration.test_control_plane import meta
from uaw.infrastructure.credentials import WindowsCredentialStore
from uaw.infrastructure.enrollment_candidates import OwnedEnrollmentCandidates
from uaw.infrastructure.enrollment_control import WindowsEnrollmentControlProof
from uaw.infrastructure.enrollment_pipe import EnrollmentProofClient, EnrollmentProofServer, decode
from uaw.shared.errors import DomainError
from uaw.shared.runner_signatures import VerificationKey

ROOT = Path(__file__).resolve().parents[3]

CHILD = """
import asyncio,copy,json,sys
from pathlib import Path
from uaw_runner.ipc.windows_pipe import WindowsApi,connect_pipe
from uaw_runner.state import LocalState
from uaw.infrastructure.enrollment_pipe import EnrollmentProofClient
from uaw.shared.contracts import Principal
async def main():
 actual=WindowsApi().current()
 print(json.dumps(actual.__dict__),flush=True)
 path=json.loads(sys.stdin.buffer.readline())
 v=json.loads(Path(path).read_text(encoding='utf-8'))
 class Original:
  async def challenge(self,owner,key):
   assert owner.wire()==v['document']['owner'] and key==v['document']['enrollment_id']
   return copy.deepcopy(v['document'])
 owner=Principal.model_validate(v['document']['owner'])
 directory=LocalState(Path(v['keys']))
 if v['mode'] in ('malformed','wrong_peer'):
  c=await connect_pipe(name=v['name'],logon_sid=actual.logon_sid)
  try:
   await c.identify()
   key='wrong' if v['mode']=='malformed' else v['document']['enrollment_id']
   await c.send(json.dumps({'protocol':'uaw-enrollment-proof-v1','enrollment_id':key}).encode())
   await c.receive()
  finally: await c.close()
 else:
  c=EnrollmentProofClient(Original(),directory,owner=owner,enrollment_id=v['document']['enrollment_id'],pipe_name=v['name'])
  proof=await c.current(v['document']['enrollment_id'],owner=owner)
  assert isinstance(proof,str) and len(proof)>40
 print('verified',flush=True)
try: asyncio.run(main())
except Exception as e:
 print('denied:'+type(e).__name__+':'+getattr(getattr(e,'failure',None),'code',''),flush=True)
 sys.exit(2)
"""


@pytest.mark.parametrize("mode", ["success", "malformed", "wrong_peer"])
async def test_original_control_proof_actual_two_process_pipe(enrollment_case, tmp_path, mode):
    p = enrollment_case
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), str(ROOT / "apps/local_runner"), str(ROOT / ".venv/Lib/site-packages")]
    )
    child = await asyncio.to_thread(
        subprocess.Popen,
        [sys._base_executable, "-u", "-c", CHILD],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=environment,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    credentials = WindowsCredentialStore("enrollment-pipe-test-" + uuid4().hex)
    handle = "control-" + uuid4().hex
    server = work = None
    credential_created = False
    try:
        async with asyncio.timeout(10):
            observed = OsIdentity(**json.loads(await asyncio.to_thread(child.stdout.readline)))
        assert observed.pid == child.pid
        api = WindowsApi()
        process, actual_child = api.process(child.pid)
        try:
            assert actual_child == observed
        finally:
            api.k.CloseHandle(process)
        control = api.current()
        p.candidate["control"]["identity"] = OwnedEnrollmentCandidates.identity(control)
        if mode != "wrong_peer":
            p.candidate["device"]["identity"] = OwnedEnrollmentCandidates.identity(observed)
        else:
            p.candidate["device"]["identity"]["user_sid"] = control.user_sid
            p.candidate["device"]["identity"]["logon_sid"] = control.logon_sid
        keys_path = tmp_path / "roles.sqlite"
        directory = LocalState(keys_path)
        for role in ("control", "device"):
            directory.register_key(
                VerificationKey(
                    role + "-key",
                    p.candidate["device_id"],
                    p.keys[role].public_key().public_bytes_raw(),
                    role,
                )
            )
        await credentials.put(
            handle, SecretStr(base64.b64encode(p.keys["control"].private_bytes_raw()).decode())
        )
        credential_created = True
        started = await p.service.begin(p.owner, p.candidate["id"], meta("first-pipe-begin"))
        issuer = WindowsEnrollmentControlProof(
            p.service, directory, credentials, control_credential_handle=handle
        )
        server = EnrollmentProofServer(issuer, owner=p.owner, enrollment_id=started["id"])
        name = await server.prepare()
        with pytest.raises(DomainError) as twice:
            await server.prepare()
        assert twice.value.failure.code == "enrollment_pipe_used"
        fixture = tmp_path / "original-public-fixture.json"
        fixture.write_text(
            json.dumps(
                {
                    "name": name,
                    "keys": str(keys_path),
                    "mode": mode,
                    "document": started["proof_document"],
                }
            ),
            encoding="utf-8",
        )
        work = asyncio.create_task(server.serve_once())
        child.stdin.write((json.dumps(str(fixture)) + "\n").encode("ascii"))
        child.stdin.flush()
        if mode == "success":
            try:
                await work
            except BaseException:
                if child.poll() is not None:
                    print(
                        "Child diagnostic:", child.stdout.read().decode("utf-8", errors="replace")
                    )
                raise
            expected = b"verified\n"
        else:
            with pytest.raises(DomainError) as denied:
                await work
            assert denied.value.failure.code == (
                "enrollment_pipe_peer_denied" if mode == "wrong_peer" else "enrollment_pipe_invalid"
            )
            expected = b"denied\n"
        async with asyncio.timeout(12):
            result = await asyncio.to_thread(child.stdout.readline)
            exit_code = await asyncio.to_thread(child.wait)
        if mode == "success":
            assert result.replace(b"\r\n", b"\n") == expected
        else:
            assert result.startswith(b"denied:"), result
        assert exit_code == (0 if mode == "success" else 2)
        assert (await p.service.get(p.owner, started["id"]))["state"] == "pending"
        with pytest.raises(DomainError) as reused:
            await server.serve_once()
        assert reused.value.failure.code == "enrollment_pipe_used"
    finally:
        if work is not None and not work.done():
            work.cancel()
            await asyncio.gather(work, return_exceptions=True)
        if server is not None:
            await server.close()
        if child.poll() is None:
            child.terminate()
        await asyncio.to_thread(child.wait, timeout=10)
        if child.stdin:
            child.stdin.close()
        if child.stdout:
            child.stdout.close()
        if credential_created:
            await credentials.delete(handle)
    with pytest.raises(DomainError) as cleaned:
        await credentials.resolve(handle)
    assert cleaned.value.status_code == 404


@pytest.mark.parametrize("data", [b"[]", b"{}{}", b'{"a":1,"a":2}', b"x" * 4097])
def test_enrollment_proof_message_rejects_ambiguous_or_unbounded(data):
    with pytest.raises(DomainError) as denied:
        decode(data)
    assert denied.value.failure.code == "enrollment_pipe_invalid"


async def test_first_proof_client_wrong_owner_denied_before_os_or_io(enrollment_case):
    p = enrollment_case
    client = EnrollmentProofClient(
        p.service, None, owner=p.owner, enrollment_id="original", pipe_name="not-a-pipe"
    )
    with pytest.raises(DomainError) as denied:
        await client.current("different", owner=p.owner)
    assert denied.value.failure.code == "enrollment_pipe_owner_denied"


async def test_first_proof_cancel_drains_late_owned_windows_listener(
    enrollment_case, tmp_path, monkeypatch
):
    from threading import Event

    from uaw.infrastructure import enrollment_pipe

    p = enrollment_case
    control = WindowsApi().current()
    p.candidate["control"]["identity"] = OwnedEnrollmentCandidates.identity(control)
    for field in ("user_sid", "logon_sid"):
        p.candidate["device"]["identity"][field] = p.candidate["control"]["identity"][field]
    directory = LocalState(tmp_path / "cancel-roles.sqlite")
    for role in ("control", "device"):
        directory.register_key(
            VerificationKey(
                role + "-key",
                p.candidate["device_id"],
                p.keys[role].public_key().public_bytes_raw(),
                role,
            )
        )
    started = await p.service.begin(p.owner, p.candidate["id"], meta("pipe-cancel-begin"))
    issuer = WindowsEnrollmentControlProof(
        p.service, directory, None, control_credential_handle="not-read"
    )
    server = EnrollmentProofServer(issuer, owner=p.owner, enrollment_id=started["id"])
    created, release = Event(), Event()
    listeners = []
    original = enrollment_pipe.WindowsPipeListener

    def delayed(**kwargs):
        listener = original(**kwargs)
        listeners.append(listener)
        created.set()
        assert release.wait(5)
        return listener

    monkeypatch.setattr(enrollment_pipe, "WindowsPipeListener", delayed)
    task = asyncio.create_task(server.prepare())
    try:
        assert await asyncio.to_thread(created.wait, 5)
        task.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert len(listeners) == 1 and listeners[0].connection.closed.is_set()
        assert (await p.service.get(p.owner, started["id"]))["state"] == "pending"
    finally:
        release.set()
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await server.close()
