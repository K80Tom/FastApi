from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.db.transaction import transaction
from app.models.project import Project, ProjectMembership
from app.models.user import User
from app.repositories import project_repository, user_repository
from app.schemas.project import ProjectCreate
from app.services.permission_service import require_project_role


async def create_project(session: AsyncSession, user: User, payload: ProjectCreate) -> Project:
    try:
        async with transaction(session):
            return await project_repository.create(
                session,
                name=payload.name,
                description=payload.description,
                owner_id=user.id,
            )
    except IntegrityError as exc:
        raise ConflictError("You already have a project with this name") from exc


async def list_projects(session: AsyncSession, user: User) -> list[Project]:
    if user.role == "admin":
        from sqlalchemy import select

        result = await session.execute(select(Project).order_by(Project.created_at.desc(), Project.id.desc()))
        return list(result.scalars())
    return await project_repository.list_for_user(session, user.id)


async def add_member(
    session: AsyncSession, current_user: User, project_id: int, user_id: int, role: str
) -> ProjectMembership:
    await require_project_role(session, current_user, project_id, "owner")
    target = await user_repository.get_by_id(session, user_id)
    if target is None or not target.is_active:
        raise NotFoundError("Active user not found", details={"user_id": user_id})
    if await project_repository.get_membership(session, project_id, user_id):
        raise ConflictError("User is already a project member")
    async with transaction(session):
        return await project_repository.add_member(session, project_id, user_id, role)
