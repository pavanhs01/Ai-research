"""
Verifies Clerk-issued session JWTs on every protected request.

The frontend sends `Authorization: Bearer <clerk_session_token>` on each
request (attached automatically by the Next.js proxy route / API client).
This module fetches Clerk's JWKS, verifies the token signature, issuer,
and expiry, and exposes the authenticated user's Clerk ID + claims to
route handlers via the `get_current_user` dependency.
"""

from dataclasses import dataclass
from functools import lru_cache

import httpx
import jwt
from fastapi import Depends, Request
from jwt import PyJWKClient

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


@dataclass(frozen=True)
class AuthenticatedUser:
    clerk_id: str
    email: str | None
    claims: dict


@lru_cache
def get_jwks_client() -> PyJWKClient:
    """Cached JWKS client — avoids refetching Clerk's public keys on every request."""
    return PyJWKClient(settings.CLERK_JWKS_URL)


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedException("Missing or malformed Authorization header")
    return auth_header.removeprefix("Bearer ").strip()


def verify_clerk_token(token: str) -> dict:
    """Verify signature, issuer, and expiry of a Clerk session token. Raises UnauthorizedException on failure."""
    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER,
            options={"verify_aud": False},
        )
        return claims
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException("Session token has expired") from exc
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid Clerk token: %s", exc)
        raise UnauthorizedException("Invalid session token") from exc
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch Clerk JWKS: %s", exc)
        raise UnauthorizedException("Could not verify session token") from exc


async def get_current_user(request: Request) -> AuthenticatedUser:
    """FastAPI dependency — injects the authenticated user into any route handler."""
    token = _extract_bearer_token(request)
    claims = verify_clerk_token(token)

    clerk_id = claims.get("sub")
    if not clerk_id:
        raise UnauthorizedException("Token missing subject claim")

    email = claims.get("email") or (claims.get("email_addresses") or [{}])[0].get("email_address")
    return AuthenticatedUser(clerk_id=clerk_id, email=email, claims=claims)


CurrentUser = Depends(get_current_user)
