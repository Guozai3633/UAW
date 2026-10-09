"""Internal administrator acceptance of an actual persisted model protocol probe."""

from uaw.infrastructure.db.transactions import RecordTransaction, reference
from uaw.model.contracts import Payload
from uaw.shared.configuration import ConfigurationService
from uaw.shared.contracts import Principal, Ref, RequestMeta
from uaw.shared.errors import reject
from uaw.shared.schema import validate_contract
from uaw.shared.stores import StoreConflict


class ModelConnectionAcceptance:
    """A successful owned invocation is evidence; caller JSON is never evidence.

    This is an internal assembly operation, not an installed public endpoint.
    Connecting advances both binding/config revisions. Existing Runs keep their
    original pins; the administrator must publish a new catalogue/snapshot.
    """

    def __init__(self, configuration: ConfigurationService) -> None:
        self.configuration = configuration

    async def accept(
        self,
        actor: Principal,
        provider_ref: Ref,
        probe_owner: Principal,
        attempt_id: str,
        meta: RequestMeta,
    ) -> Payload:
        config = self.configuration
        config._admin(actor)
        validate_contract("Principal", probe_owner.wire())
        validate_contract("ID", attempt_id)
        if provider_ref.wire() != reference("provider", provider_ref.id, int(provider_ref.version)):
            raise reject("connection_provider_pin_invalid", "Exact provider revision required")
        if meta.expected_revision != int(provider_ref.version):
            raise StoreConflict()

        async def write(tx: RecordTransaction) -> Payload:
            row = await tx.load("providers", provider_ref.id)
            configured = await tx.load("provider.configs", provider_ref.id)
            if (
                row.revision != meta.expected_revision
                or configured.revision != row.revision
                or row.schema_name != "ProviderBinding"
                or row.payload["kind"] != "model"
                or row.payload["state"] != "disconnected"
            ):
                raise reject(
                    "connection_provider_stale", "Configured disconnected provider required", 412
                )
            config._profile(configured.payload)
            # Read the isolated evidence owner within the same SQL transaction.
            evidence = RecordTransaction(tx.session, probe_owner.id)
            invocation = await evidence.load("model.invocations", attempt_id)
            output = await evidence.load("model.outputs", attempt_id)
            validate_contract("ModelInvocation", invocation.payload)
            validate_contract("ModelOutput", output.payload)
            result = invocation.payload.get("result", {})
            actual = output.payload["actual_config"]
            if (
                invocation.schema_name != "ModelInvocation"
                or output.schema_name != "ModelOutput"
                or invocation.payload["state"] != "finished"
                or result.get("kind") != "ok"
                or result.get("payload") != output.payload
                or result.get("output_refs") != [reference("content", attempt_id)]
                or invocation.payload["request"]["model_config"]["provider_ref"]
                != provider_ref.wire()
                or actual["provider_ref"] != provider_ref.wire()
                or output.payload["attempt_id"] != attempt_id
                or output.payload["finish_reason"] != "stop"
                or not output.payload["text_complete"]
                or actual.get("provider_model_name") != configured.payload["settings"]["model_name"]
                or actual.get("response_model_name")
                not in [
                    configured.payload["settings"]["model_name"],
                    *configured.payload["settings"].get("allowed_response_models", []),
                ]
            ):
                raise reject(
                    "connection_probe_invalid", "Successful matching persisted probe required", 412
                )
            revision = row.revision + 1
            await tx.write(
                "provider.configs",
                provider_ref.id,
                "ProviderDraft",
                configured.payload,
                configured.revision,
            )
            value = {
                **row.payload,
                "state": "active",
                "revision": revision,
                "config_ref": reference("configuration", provider_ref.id, revision),
            }
            await tx.write("providers", provider_ref.id, "ProviderBinding", value, row.revision)
            return value

        return await config.transactions.execute(
            config.platform,
            "configuration",
            meta,
            {
                "action": "provider.accept_model_probe",
                "actor": actor.wire(),
                "provider_ref": provider_ref.wire(),
                "probe_owner": probe_owner.wire(),
                "attempt_id": attempt_id,
            },
            write,
        )
