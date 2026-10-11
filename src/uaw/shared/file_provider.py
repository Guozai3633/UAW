"""Explicit closed file-provider acceptance; no flag or Run is changed here."""

from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.shared.configuration import FILE_PROFILE, ConfigurationService
from uaw.shared.contracts import JsonObject, Principal, Ref, RequestMeta
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.stores import StoreConflict


class FileProviderConnectionAcceptance:
    def __init__(self, configuration: ConfigurationService) -> None:
        self.configuration = configuration

    async def accept(self, actor: Principal, provider: Ref, meta: RequestMeta) -> JsonObject:
        config = self.configuration
        config._admin(actor)
        if (
            not provider.version.isascii()
            or not provider.version.isdigit()
            or provider.wire() != reference("provider", provider.id, int(provider.version))
            or meta.expected_revision != int(provider.version)
        ):
            raise StoreConflict()
        availability = config.file_availability
        if availability is None:
            raise CapabilityUnavailable("file.current_installed_availability")

        async def write(tx: RecordTransaction) -> JsonObject:
            row = await tx.load("providers", provider.id)
            draft = await tx.load("provider.configs", provider.id)
            config._profile(draft.payload)
            if (
                row.revision != meta.expected_revision
                or draft.revision != row.revision
                or row.payload["revision"] != row.revision
                or row.payload["id"] != provider.id
                or draft.payload["id"] != provider.id
                or row.payload["kind"] != "local"
                or row.payload["state"] != "disconnected"
                or draft.payload["profile_ref"] != FILE_PROFILE
            ):
                raise reject(
                    "file_provider_stale", "Original disconnected file profile required", 412
                )
            # No UI/tool/model work under this short configuration transaction.
            await availability.require({})
            revision = row.revision + 1
            await tx.write(
                "provider.configs", provider.id, "ProviderDraft", draft.payload, row.revision
            )
            value = {
                **row.payload,
                "revision": revision,
                "state": "active",
                "config_ref": reference("configuration", provider.id, revision),
            }
            await tx.write("providers", provider.id, "ProviderBinding", value, row.revision)
            return value

        return await config.transactions.execute(
            config.platform,
            "configuration",
            meta,
            {"action": "file.accept", "actor": actor.wire(), "provider": provider.wire()},
            write,
        )
