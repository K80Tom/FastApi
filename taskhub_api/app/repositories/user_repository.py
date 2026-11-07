from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def find_by_login(session: AsyncSession, login: str) -> User | None:
    result = await session.execute(select(User).where(or_(User.email == login, User.username == login)))
    return result.scalar_one_or_none()


async def find_duplicate(session: AsyncSession, email: str, username: str) -> User | None:
    result = await session.execute(select(User).where(or_(User.email == email, User.username == username)))
    return result.scalars().first()


async def create(session: AsyncSession, **values) -> User:
    user = User(**values)
    session.add(user)
    await session.flush()
    return user
