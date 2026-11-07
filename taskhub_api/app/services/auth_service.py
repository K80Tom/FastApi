from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.transaction import transaction
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate

DUMMY_HASH = hash_password("not-a-real-user-password")


async def register(session: AsyncSession, payload: UserCreate) -> User:
    duplicate = await user_repository.find_duplicate(session, payload.email, payload.username)
    if duplicate:
        raise ConflictError("Email or username is already registered")
    try:
        async with transaction(session):
            return await user_repository.create(
                session,
                email=str(payload.email).lower(),
                username=payload.username,
                display_name=payload.display_name,
                password_hash=hash_password(payload.password),
                role="user",
                is_active=True,
            )
    except IntegrityError as exc:
        raise ConflictError("Email or username is already registered") from exc


async def authenticate(session: AsyncSession, settings: Settings, login: str, password: str) -> tuple[str, int]:
    user = await user_repository.find_by_login(session, login)
    if user is None:
        verify_password(password, DUMMY_HASH)
        raise UnauthorizedError(
            "Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise UnauthorizedError(
            "Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_access_token(user.id, settings)
