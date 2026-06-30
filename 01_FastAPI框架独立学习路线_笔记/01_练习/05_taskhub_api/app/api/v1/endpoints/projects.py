from fastapi import APIRouter

from app.repositories import project_repository
from app.schemas.project import ProjectSummary


router = APIRouter()


@router.get("", response_model=list[ProjectSummary])
def list_projects():
    # 本讲项目接口只用于给创建任务提供 project_id。
    return project_repository.list_projects()
