from fastapi import APIRouter

from app.repositories import user_repository
from app.schemas.user import UserSummary


router = APIRouter()


@router.get("", response_model=list[UserSummary])
def list_users():
    # 本讲用户接口很简单，先直接读 repository。
    # 后面用户业务变复杂时，也可以新增 user_service.py。
    return user_repository.list_users()
