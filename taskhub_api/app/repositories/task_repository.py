from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.comment import Comment
from app.models.project import ProjectMembership
from app.models.task import Task


def task_options():
    return (selectinload(Task.tags), joinedload(Task.owner), joinedload(Task.project))


async def get(session: AsyncSession, task_id: int) -> Task | None:
    result = await session.execute(select(Task).options(*task_options()).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def list_visible(
    session: AsyncSession,
    user_id: int | None,
    *,
    page: int,
    page_size: int,
    status: str | None,
    priority: str | None,
    project_id: int | None,
    keyword: str | None,
) -> tuple[list[Task], int]:
    conditions = []
    if user_id is not None:
        visible_projects = select(ProjectMembership.project_id).where(ProjectMembership.user_id == user_id)
        conditions.append(Task.project_id.in_(visible_projects))
    if status:
        conditions.append(Task.status == status)
    if priority:
        conditions.append(Task.priority == priority)
    if project_id:
        conditions.append(Task.project_id == project_id)
    if keyword:
        pattern = f"%{keyword}%"
        conditions.append(Task.title.ilike(pattern) | Task.description.ilike(pattern))
    total = await session.scalar(select(func.count(Task.id)).where(*conditions)) or 0
    statement = (
        select(Task)
        .options(*task_options())
        .where(*conditions)
        .order_by(Task.created_at.desc(), Task.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(statement)
    return list(result.scalars().unique()), total


async def create(session: AsyncSession, **values) -> Task:
    task = Task(**values)
    session.add(task)
    await session.flush()
    return task


async def delete(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.flush()


async def create_comment(session: AsyncSession, task_id: int, author_id: int, content: str) -> Comment:
    comment = Comment(task_id=task_id, author_id=author_id, content=content)
    session.add(comment)
    await session.flush()
    return comment


async def list_comments(session: AsyncSession, task_id: int) -> list[Comment]:
    result = await session.execute(
        select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at, Comment.id)
    )
    return list(result.scalars())
