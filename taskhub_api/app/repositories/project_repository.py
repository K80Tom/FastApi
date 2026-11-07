from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMembership


async def get(session: AsyncSession, project_id: int) -> Project | None:
    return await session.get(Project, project_id)


async def get_membership(session: AsyncSession, project_id: int, user_id: int) -> ProjectMembership | None:
    return await session.get(ProjectMembership, (project_id, user_id))


async def list_for_user(session: AsyncSession, user_id: int) -> list[Project]:
    statement = (
        select(Project)
        .join(ProjectMembership)
        .where(ProjectMembership.user_id == user_id)
        .order_by(Project.created_at.desc(), Project.id.desc())
    )
    result = await session.execute(statement)
    return list(result.scalars())


async def create(session: AsyncSession, *, name: str, description: str, owner_id: int) -> Project:
    project = Project(name=name, description=description, owner_id=owner_id)
    session.add(project)
    await session.flush()
    session.add(ProjectMembership(project_id=project.id, user_id=owner_id, role="owner"))
    await session.flush()
    return project


async def add_member(session: AsyncSession, project_id: int, user_id: int, role: str) -> ProjectMembership:
    membership = ProjectMembership(project_id=project_id, user_id=user_id, role=role)
    session.add(membership)
    await session.flush()
    return membership
