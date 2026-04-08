"""Authentication and identity utilities."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationException, ConfigurationException


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthContext:
    """Represents authenticated user identity."""

    clerk_user_id: str
    token: str | None = None
    email: str | None = None


def _extract_email(claims: dict[str, object], request: Request) -> str | None:
    for key in ("email", "email_address", "primary_email_address"):
        value = claims.get(key)
        if isinstance(value, str) and value:
            return value

    header_value = request.headers.get("x-user-email")
    return header_value or None


def _build_auth_context(claims: dict[str, object], *, token: str, request: Request) -> AuthContext:
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AuthenticationException("Token does not contain a valid subject")

    return AuthContext(
        clerk_user_id=subject,
        token=token,
        email=_extract_email(claims, request),
    )


def _decode_clerk_jwt(token: str, settings: Settings) -> dict[str, object]:
    try:
        from jose import JWTError, jwt  # type: ignore
    except ModuleNotFoundError as exc:
        raise ConfigurationException(
            "python-jose is required when auth is enabled"
        ) from exc

    if not settings.clerk_jwt_public_key:
        raise ConfigurationException(
            "CLERK_JWT_PUBLIC_KEY must be configured when auth is enabled"
        )

    decode_kwargs: dict[str, object] = {
        "key": settings.clerk_jwt_public_key,
        "algorithms": ["RS256"],
    }

    options = {"verify_signature": True, "verify_exp": True, "verify_aud": bool(settings.clerk_audience)}
    decode_kwargs["options"] = options

    if settings.clerk_audience:
        decode_kwargs["audience"] = settings.clerk_audience
    if settings.clerk_issuer:
        decode_kwargs["issuer"] = settings.clerk_issuer

    return jwt.decode(token, **decode_kwargs)


async def get_auth_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    """Resolve authenticated user from Clerk bearer token."""
    cached = getattr(request.state, "auth_context", None)
    if isinstance(cached, AuthContext):
        return cached

    if settings.auth_disabled:
        user_id = request.headers.get("x-dev-user-id", settings.dev_user_id)
        context = AuthContext(
            clerk_user_id=user_id,
            token=None,
            email=request.headers.get("x-user-email") or None,
        )
        request.state.auth_context = context
        return context

    if credentials is None or not credentials.credentials:
        raise AuthenticationException("Missing bearer token")

    token = credentials.credentials
    try:
        claims = _decode_clerk_jwt(token, settings)
    except Exception as exc:
        if isinstance(exc, ConfigurationException):
            raise
        raise AuthenticationException("Invalid or expired token", details={"reason": str(exc)}) from exc

    context = _build_auth_context(claims, token=token, request=request)
    request.state.auth_context = context
    return context


async def get_optional_auth_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthContext | None:
    """Best-effort auth context for routes that can work anonymously."""
    cached = getattr(request.state, "auth_context", None)
    if isinstance(cached, AuthContext):
        return cached

    if settings.auth_disabled:
        context = AuthContext(
            clerk_user_id=request.headers.get("x-dev-user-id", settings.dev_user_id),
            token=None,
            email=request.headers.get("x-user-email") or None,
        )
        request.state.auth_context = context
        return context

    if credentials is None or not credentials.credentials:
        return None

    try:
        claims = _decode_clerk_jwt(credentials.credentials, settings)
    except Exception:
        return None

    context = _build_auth_context(claims, token=credentials.credentials, request=request)
    request.state.auth_context = context
    return context
