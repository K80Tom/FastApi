from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """提交当前事务；任何异常都回滚，兼容依赖查询触发的 autobegin。"""
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
