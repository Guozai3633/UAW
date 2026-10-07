"""Loopback development authentication. Roles are deployment configuration, never request fields."""

import hashlib
import hmac

from fastapi import Request

from uaw.shared.contracts import Principal
from uaw.shared.errors import reject
from uaw.shared.settings import Settings


def authenticate(request: Request, settings: Settings, *, admin: bool = False) -> Principal:
    if request.headers.get("origin"):
        # No browser-origin API access before the authenticated web gateway is implemented.
        raise reject(
            "origin_denied",
            "Browser origin is not enabled for the development API",
            403,
            "permission",
        )
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer" or not value or len(value) > 4096:
        raise reject(
            "authentication_required", "A development bearer token is required", 401, "permission"
        )
    for token, principal_id, kind in (
        (settings.development_admin_token, settings.development_admin_id, "admin"),
        (settings.development_user_token, settings.development_principal_id, "user"),
    ):
        if token and hmac.compare_digest(value.encode(), token.get_secret_value().encode()):
            if admin and kind != "admin":
                raise reject(
                    "admin_required", "Administrator authentication is required", 403, "permission"
                )
            session = "session-" + hashlib.sha256(value.encode()).hexdigest()[:24]
            return Principal(id=principal_id, kind=kind, auth_session_id=session)  # type: ignore[arg-type]
    raise reject("authentication_failed", "Development authentication failed", 401, "permission")
