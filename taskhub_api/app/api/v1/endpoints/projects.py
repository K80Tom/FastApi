from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbDep
from app.schemas.common import DataResponse
from app.schemas.project import MemberAdd, MembershipRead, ProjectCreate, ProjectRead
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=DataResponse[list[ProjectRead]])
async def list_projects(current_user: CurrentUser, db: DbDep):
    projects = await project_service.list_projects(db, current_user)
    return {"data": [ProjectRead.model_validate(item) for item in projects]}


@router.post("", response_model=DataResponse[ProjectRead], status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, current_user: CurrentUser, db: DbDep):
    project = await project_service.create_project(db, current_user, payload)
    return {"data": ProjectRead.model_validate(project), "message": "project created"}


@router.post("/{project_id}/members", response_model=DataResponse[MembershipRead], status_code=status.HTTP_201_CREATED)
async def add_member(project_id: int, payload: MemberAdd, current_user: CurrentUser, db: DbDep):
    membership = await project_service.add_member(db, current_user, project_id, payload.user_id, payload.role)
    return {"data": MembershipRead.model_validate(membership), "message": "member added"}
