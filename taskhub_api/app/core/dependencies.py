import secrets
from typing import Annotated

import httpx
from fastapi import Depends, Request
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import NotFoundError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


async def get_db(request: Request):
    async with request.app.state.session_factory() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


HttpClientDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: DbDep,
    settings: SettingsDep,
) -> User:
    if not token:
        raise UnauthorizedError(
            "Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token, settings)
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise UnauthorizedError(
            "Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError(
            "User is inactive or no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_api_key(
    settings: SettingsDep,
    supplied_key: Annotated[str | None, Depends(api_key_header)],
) -> str:
    if not settings.api_key_enabled:
        raise NotFoundError("Service endpoint is disabled")
    if settings.api_key is None or not supplied_key:
        raise UnauthorizedError("Valid API key required", headers={"WWW-Authenticate": "APIKey"})
    expected = settings.api_key.get_secret_value()
    if not secrets.compare_digest(supplied_key, expected):
        raise UnauthorizedError("Valid API key required", headers={"WWW-Authenticate": "APIKey"})
    return "api-key-client"
