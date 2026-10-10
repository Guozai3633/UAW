"""First device gate runs before D's paired helper factory; no synthetic peer."""

import asyncio
from typing import Protocol

from uaw_runner.helper_host import HelperApplication, HelperAssemblyPort
from uaw_runner.ipc.windows_pipe import OsIdentity, WindowsApi

from uaw.infrastructure.db.records import parameter_hash
from uaw.infrastructure.enrollment_candidates import OwnedEnrollmentCandidates
from uaw.infrastructure.enrollment_native import WindowsEnrollmentConfirmation
from uaw.run.enrollment import RunnerEnrollments
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.runner_bootstrap import FirstStartPolicy, FirstStartProgressPort


class CurrentEnrollmentControlProofPort(Protocol):
    async def current(self, enrollment_id: str, *, owner: Principal) -> str:
        """Original control OS protected proof, delivered through trusted bootstrap.

        No caller document, approved flag, PID ownership or plaintext-key fallback.
        The returned signature remains checked against the original current role
        key/challenge by the actual device producer. Missing transport is unavailable.
        """
        ...


class FirstEnrollmentDeviceFactory:
    """Trusted installed D factory wrapper, explicitly configured per first launch.

    D prepare reports a process; A captures it and registers a pending challenge.
    Only this separate first device gate may open the account native confirmation.
    Once both proofs and the current Web owner commit active, D's existing factory
    may construct its paired runtime. No prepared/pending peer is passed as paired.
    """

    def __init__(
        self,
        service: RunnerEnrollments,
        *,
        owner: Principal,
        enrollment_id: str,
        native: WindowsEnrollmentConfirmation | None,
        proofs: CurrentEnrollmentControlProofPort | None,
        paired_factory: HelperAssemblyPort | None,
        progress: FirstStartProgressPort | None = None,
    ) -> None:
        if native is not None and native.service is not service:
            raise ValueError("Original enrollment service required")
        self.service, self.owner, self.key = service, owner, enrollment_id
        self.native, self.proofs, self.paired_factory = native, proofs, paired_factory
        self.progress = progress

    async def create(self, identity: OsIdentity) -> HelperApplication:
        if self.native is None or self.proofs is None or self.paired_factory is None:
            raise CapabilityUnavailable("enrollment.first_device_bootstrap_sources")
        # A restart can read the same active proof; it cannot change original
        # process bindings or silently display a second native window.
        document = await self.service.challenge(self.owner, self.key)
        actual = await asyncio.to_thread(WindowsApi().current)
        if actual != identity or document["device"][
            "identity"
        ] != OwnedEnrollmentCandidates.identity(actual):
            raise reject(
                "enrollment_first_device_denied", "Original device OS instance differs", 403
            )
        async with asyncio.timeout(10):
            proof = await self.proofs.current(self.key, owner=self.owner)
        if not isinstance(proof, str) or len(proof) > 240:
            raise reject("enrollment_control_proof_denied", "Current control proof is invalid", 403)
        if await self.native.checked(self.owner, self.key, proof) != document:
            raise reject("enrollment_first_source_changed", "Original device source changed", 412)
        state = await self.service.get(self.owner, self.key)
        if state["state"] == "pending":
            if self.progress is not None:
                policy = FirstStartPolicy(
                    expires_at=self.service.instant(document["expires_at"]),
                    challenge_hash=parameter_hash(document),
                )
                async with asyncio.timeout(5):
                    await self.progress.waiting(policy)
                # A progress callback may wait or fail; it never grants permission.
                if await self.native.checked(self.owner, self.key, proof) != document:
                    raise reject(
                        "enrollment_first_source_changed", "Source changed after progress", 412
                    )
            # Only the real native producer reaches Yes. An empty HTTP confirmation
            # or supplied signature by itself cannot replace the owning UI journal.
            await self.native.confirm(self.owner, self.key, control_proof=proof)
            state = await self.service.complete(
                self.owner,
                self.key,
                RequestMeta(
                    request_id="first-native-activate-" + self.key,
                    schema_version="0.1",
                    expected_revision=state["revision"],
                ),
            )
        if state["state"] != "active" or state["proof_document"] != document:
            raise reject("enrollment_first_not_active", "Current native pairing is not active", 403)
        if await self.service.get(self.owner, self.key) != state:
            raise reject("enrollment_first_source_changed", "Current pairing changed", 412)
        application = await self.paired_factory.create(identity)
        if not isinstance(application, HelperApplication):
            raise reject("dependency_protocol_invalid", "Paired helper factory type differs", 503)
        try:
            if await self.service.get(self.owner, self.key) != state:
                raise reject("enrollment_first_source_changed", "Current pairing changed", 412)
        except BaseException:
            # A current Reader can throw (logout/revocation), not only return a
            # different row. Close owned adapters on either failure or cancellation.
            await application.helper.close()
            raise
        return application
