"""Fresh key authorization and protected signing. No plaintext private-key fallback."""

import asyncio
import base64
import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import SecretStr

from uaw.shared.contracts import JsonObject
from uaw.shared.credentials import CredentialStorePort
from uaw.shared.errors import CapabilityUnavailable, DomainError, reject
from uaw.shared.runner_signatures import KEY_ID, Domain, sign, verify
from uaw.shared.schema import validate_contract
from uaw.workspace.contracts import RunnerCommand, RunnerReceipt
from uaw.workspace.ports import CurrentKeyDirectory


def signature_key_id(signature: str) -> str | None:
    parts = signature.split(":")
    if len(parts) != 3 or parts[0] != "uaw-ed25519-v1" or not KEY_ID.fullmatch(parts[1]):
        return None
    return parts[1]


class Ed25519SignatureAdapter:
    def __init__(self, directory: CurrentKeyDirectory) -> None:
        self.directory = directory

    def verify_document(self, document: JsonObject, *, device_id: str, domain: Domain) -> bool:
        signature = document.get("signature")
        if not isinstance(signature, str):
            return False
        key_id = signature_key_id(signature)
        if key_id is None:
            return False
        try:
            key = self.directory.lookup(key_id, device_id=device_id)
        except DomainError:
            return False
        if key.key_id != key_id or key.device_id != device_id:
            return False
        return verify(document, signature, key, domain)

    def verify_command(self, command: RunnerCommand, *, device_id: str) -> bool:
        validated = RunnerCommand.model_validate_json(json.dumps(command.wire()))
        return self.verify_document(validated.wire(), device_id=device_id, domain="command")

    def verify_receipt(self, receipt: JsonObject, *, device_id: str) -> bool:
        RunnerReceipt.model_validate_json(json.dumps(receipt))
        return self.verify_document(receipt, device_id=device_id, domain="receipt")


class ProtectedSigner:
    def __init__(
        self,
        directory: CurrentKeyDirectory,
        credentials: CredentialStorePort | None,
    ) -> None:
        self.directory = directory
        # Production injection uses the explicit OS CredentialStore; never a JSON/file DB.
        self.credentials = credentials

    async def provision_private(self, *, credential_handle: str) -> bytes:
        """Trusted provisioning only. Returns PUBLIC bytes, not the private key/credential."""
        if self.credentials is None:
            raise CapabilityUnavailable("runner.protected_credentials")
        try:
            await self.credentials.resolve(credential_handle)
        except DomainError as exc:
            if exc.status_code != 404:
                raise
        else:
            raise reject("revision_conflict", "Protected credential handle already exists", 409)
        # Trusted single-owner provisioning; the OS port lacks create-only CAS.
        private = Ed25519PrivateKey.generate()
        secret = SecretStr(base64.b64encode(private.private_bytes_raw()).decode("ascii"))
        await self.credentials.put(credential_handle, secret)
        return private.public_key().public_bytes_raw()

    async def sign_document(
        self,
        document: JsonObject,
        *,
        device_id: str,
        key_id: str,
        domain: Domain,
        credential_handle: str,
    ) -> str:
        if self.credentials is None:
            raise CapabilityUnavailable("runner.protected_credentials")
        # Snapshot the caller's document before credential IO; never sign mutable claims.
        document = json.loads(json.dumps(document, ensure_ascii=False, allow_nan=False))
        key = await asyncio.to_thread(self.directory.lookup, key_id, device_id=device_id)
        required_role = "control" if domain == "command" else "device"
        if key.revoked or key.role != required_role:
            raise reject(
                "permission_denied", "Signing key role/revocation rejected", 403, "permission"
            )
        if domain in ("command", "receipt"):
            validate_contract("RunnerCommand" if domain == "command" else "RunnerReceipt", document)
        secret = await self.credentials.resolve(credential_handle)
        try:
            private_bytes = base64.b64decode(secret.get_secret_value(), validate=True)
            private = Ed25519PrivateKey.from_private_bytes(private_bytes)
            if private.public_key().public_bytes_raw() != key.public_bytes:
                raise ValueError("Key mismatch")
            signature = sign(document, private_bytes, device_id, key_id, domain)
        except ValueError, TypeError:
            raise reject(
                "permission_denied", "Protected key is invalid", 403, "permission"
            ) from None
        # Do not sign with a key revoked while awaiting the credential store.
        if await asyncio.to_thread(self.directory.lookup, key_id, device_id=device_id) != key:
            raise reject("permission_denied", "Signing key changed", 403, "permission")
        return signature
