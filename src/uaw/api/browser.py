"""Local user sessions. Tickets are consumed once; no raw credential is persisted."""

import hashlib
import hmac
import ipaddress
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from fastapi import Request

from uaw.api.authentication import authenticate
from uaw.infrastructure.db.records import PostgresRecordStore
from uaw.infrastructure.db.transactions import RecordTransaction, TransactionalStore, identifier
from uaw.shared.contracts import Principal, RequestMeta
from uaw.shared.errors import CapabilityUnavailable, reject
from uaw.shared.settings import Settings
from uaw.shared.stores import StoreMissing

if TYPE_CHECKING:
    from uaw.composition import Container

COOKIE = "uaw_web_session"
CSRF_HEADER = "X-UAW-CSRF"
TICKETS = "web.launch_tickets"
SESSIONS = "web.sessions"
Payload = dict[str, Any]


def clock() -> datetime:
    return datetime.now(UTC)


class BrowserSessions:
    def __init__(self, records: PostgresRecordStore, settings: Settings) -> None:
        self.records, self.settings = records, settings
        self.owner = Principal(id=settings.platform_id, kind="service", auth_session_id="web-auth")
        self.transactions = TransactionalStore(records.database)

    def ready(self) -> None:
        if not self.settings.browser_origin or not self.settings.browser_session_signing_key:
            raise CapabilityUnavailable("web.browser_session")

    def guard(self, request: Request, *, origin_required: bool = True) -> None:
        self.ready()
        host = self.settings.host
        authority = f"[{host}]" if ":" in host else host
        expected_host = f"{authority}:{self.settings.port}"
        try:
            local = (
                request.client is not None and ipaddress.ip_address(request.client.host).is_loopback
            )
        except ValueError:
            local = False
        if (
            not local
            or request.url.scheme != "http"
            or request.headers.getlist("host") != [expected_host]
        ):
            raise reject(
                "web_host_denied", "Configured loopback API host required", 403, "permission"
            )
        origins = request.headers.getlist("origin")
        if origins == [self.settings.browser_origin]:
            return
        # Same-origin browser GETs can omit Origin. A precise Referer supplies the
        # original Web origin, including port; forwarded headers never supply it.
        if not origins and not origin_required and request.method == "GET":
            try:
                referer = urlsplit(request.headers.get("referer", ""))
            except ValueError:
                raise reject(
                    "origin_denied", "Invalid browser Referer", 403, "permission"
                ) from None
            if (
                f"{referer.scheme}://{referer.netloc}" == self.settings.browser_origin
                and referer.username is None
                and referer.password is None
            ):
                return
        raise reject("origin_denied", "Exact configured browser Origin required", 403, "permission")

    def mac(self, purpose: str, resource_id: str) -> str:
        self.ready()
        assert self.settings.browser_session_signing_key is not None
        key = self.settings.browser_session_signing_key.get_secret_value().encode()
        return hmac.new(key, f"{purpose}:{resource_id}".encode(), hashlib.sha256).hexdigest()

    def token(self, purpose: str, resource_id: str) -> str:
        return resource_id + "." + self.mac(purpose, resource_id)

    def decode(self, purpose: str, value: str) -> str:
        resource_id, separator, signature = value.rpartition(".")
        if (
            not separator
            or not 1 <= len(resource_id) <= 128
            or not resource_id.startswith("web-" + purpose + "-")
            or len(signature) != 64
            or not hmac.compare_digest(signature.encode(), self.mac(purpose, resource_id).encode())
        ):
            raise reject(
                "authentication_failed", "Browser credential is invalid", 401, "permission"
            )
        return resource_id

    def epoch(self) -> str:
        assert self.settings.development_user_token is not None
        # Key/origin changes invalidate records too; restarting with the same
        # persisted settings keeps current sessions, never reopens consumed codes.
        return hashlib.sha256(
            (
                self.settings.development_principal_id
                + "\0"
                + self.settings.development_user_token.get_secret_value()
                + "\0"
                + str(self.settings.browser_origin)
            ).encode()
        ).hexdigest()

    def current_record(self, value: Payload, *, ticket: bool = False) -> None:
        if (
            value["credential_epoch"] != self.epoch()
            or value["origin"] != self.settings.browser_origin
            or value["principal"]["id"] != self.settings.development_principal_id
            or value["principal"]["kind"] != "user"
        ):
            raise reject("authentication_failed", "User credential changed", 401, "permission")
        if datetime.fromisoformat(value["expires_at"]) <= clock():
            raise reject(
                "web_ticket_expired" if ticket else "web_session_expired",
                "Browser credential expired",
                401,
                "permission",
            )

    async def launch(self, actor: Principal, meta: RequestMeta) -> Payload:
        self.ready()
        if actor.kind != "user" or actor.id != self.settings.development_principal_id:
            raise reject(
                "user_required", "User authentication required for Web launch", 403, "permission"
            )

        async def issue(tx: RecordTransaction) -> Payload:
            ticket_id = identifier("web-launch")
            value = {
                "id": ticket_id,
                "principal": actor.wire(),
                "origin": self.settings.browser_origin,
                "credential_epoch": self.epoch(),
                "expires_at": (clock() + timedelta(seconds=120)).isoformat(),
                "state": "issued",
                "revision": 1,
            }
            await tx.write(TICKETS, ticket_id, "WebLaunchTicket", value)
            return {"id": ticket_id}

        result = await self.transactions.execute(
            self.owner,
            f"web.launch:{actor.id}",
            meta,
            {"principal": actor.wire(), "epoch": self.epoch()},
            issue,
        )
        value = (await self.records.get(self.owner, TICKETS, result["id"])).payload
        self.current_record(value, ticket=True)
        if value["state"] != "issued":
            raise reject("web_ticket_used", "Launch code already consumed", 409, "permission")
        assert self.settings.browser_origin is not None
        return {
            "launch_url": self.settings.browser_origin
            + "/#uaw_launch="
            + self.token("launch", value["id"]),
            "expires_at": value["expires_at"],
        }

    async def exchange(self, code: str) -> tuple[Payload, str]:
        ticket_id = self.decode("launch", code)

        async def consume(tx: RecordTransaction) -> Payload:
            try:
                ticket = await tx.load(TICKETS, ticket_id)
            except StoreMissing:
                raise reject(
                    "web_ticket_invalid", "Launch ticket unavailable", 401, "permission"
                ) from None
            value = ticket.payload
            self.current_record(value, ticket=True)
            if value["state"] != "issued":
                raise reject("web_ticket_used", "Launch code already consumed", 409, "permission")
            session_id = identifier("web-session")
            session = {
                "id": session_id,
                "principal": Principal(
                    id=value["principal"]["id"], kind="user", auth_session_id=session_id
                ).wire(),
                "origin": value["origin"],
                "credential_epoch": value["credential_epoch"],
                "expires_at": (
                    clock() + timedelta(seconds=self.settings.browser_session_seconds)
                ).isoformat(),
                "state": "active",
                "revision": 1,
            }
            await tx.write(SESSIONS, session_id, "WebSessionRecord", session)
            await tx.write(
                TICKETS,
                ticket_id,
                "WebLaunchTicket",
                {**value, "state": "consumed", "revision": ticket.revision + 1},
                ticket.revision,
            )
            return session

        # inspect serializes the one-use exchange; even the same client request
        # cannot replay a consumed code to obtain a browser credential.
        value = await self.transactions.inspect(self.owner, f"web.ticket:{ticket_id}", consume)
        return self.public(value), self.token("session", value["id"])

    def public(self, value: Payload) -> Payload:
        return {
            "principal": value["principal"],
            "expires_at": value["expires_at"],
            "csrf_token": self.mac("csrf", value["id"]),
        }

    async def principal(self, actor: Principal) -> Payload:
        self.ready()
        try:
            row = await self.records.get(self.owner, SESSIONS, actor.auth_session_id)
        except StoreMissing:
            raise reject(
                "authentication_required", "Browser session unavailable", 401, "permission"
            ) from None
        self.current_record(row.payload)
        if row.schema_name != "WebSessionRecord" or row.payload["principal"] != actor.wire():
            raise reject("authentication_failed", "Browser identity changed", 401, "permission")
        if row.payload["state"] != "active":
            raise reject("web_session_revoked", "Browser session revoked", 401, "permission")
        return row.payload

    async def authenticate(self, request: Request) -> Payload:
        self.guard(request, origin_required=request.method != "GET")
        if request.headers.get("authorization"):
            raise reject(
                "web_bearer_denied", "Browser bearer authentication is disabled", 403, "permission"
            )
        # Ambiguous duplicate cookies/headers cannot choose a different session.
        values = [
            v
            for v in ";".join(request.headers.getlist("cookie")).split(";")
            if v.strip().startswith(COOKIE + "=")
        ]
        if len(values) != 1:
            raise reject(
                "authentication_required", "One browser session cookie required", 401, "permission"
            )
        session_id = self.decode("session", request.cookies.get(COOKIE, ""))
        actor = Principal(
            id=self.settings.development_principal_id, kind="user", auth_session_id=session_id
        )
        value = await self.principal(actor)
        if request.method != "GET" and (
            len(request.headers.getlist(CSRF_HEADER)) != 1
            or not hmac.compare_digest(
                request.headers[CSRF_HEADER].encode(), self.mac("csrf", session_id).encode()
            )
        ):
            raise reject("csrf_denied", "Current browser CSRF token required", 403, "permission")
        return value

    async def logout(self, actor: Principal, meta: RequestMeta) -> Payload:
        async def revoke(tx: RecordTransaction) -> Payload:
            row = await tx.load(SESSIONS, actor.auth_session_id)
            self.current_record(row.payload)
            if row.payload["principal"] != actor.wire():
                raise reject("authentication_failed", "Browser identity differs", 401, "permission")
            if row.payload["state"] == "active":
                await tx.write(
                    SESSIONS,
                    row.resource_id,
                    "WebSessionRecord",
                    {**row.payload, "state": "revoked", "revision": row.revision + 1},
                    row.revision,
                )
            return {"operation_id": meta.request_id, "status": "completed"}

        return await self.transactions.inspect(
            self.owner, f"web.session:{actor.auth_session_id}", revoke
        )


async def authenticated(
    request: Request, container: Container, *, admin: bool = False
) -> Principal:
    if request.headers.get("origin") or COOKIE in request.cookies:
        if container.browser_sessions is None:
            # Preserve the original CLI Origin rejection when Web is disabled.
            return authenticate(request, container.settings, admin=admin)
        value = await container.browser_sessions.authenticate(request)
        if admin:
            raise reject(
                "admin_required", "Browser sessions have no admin authority", 403, "permission"
            )
        return Principal.model_validate(value["principal"])
    return authenticate(request, container.settings, admin=admin)
