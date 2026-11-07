from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.user import User
from app.repositories import project_repository

ROLE_RANK = {"viewer": 1, "member": 2, "owner": 3}


async def require_project_role(
    session: AsyncSession, user: User, project_id: int, minimum_role: str = "viewer"
) -> tuple[Project, str]:
    project = await project_repository.get(session, project_id)
    if project is None:
        raise NotFoundError("Project not found", details={"project_id": project_id})
    if user.role == "admin":
        return project, "owner"
    membership = await project_repository.get_membership(session, project_id, user.id)
    if membership is None:
        raise ForbiddenError("You are not a member of this project")
    if ROLE_RANK[membership.role] < ROLE_RANK[minimum_role]:
        raise ForbiddenError(f"Project role {minimum_role} or above is required")
    return project, membership.role
