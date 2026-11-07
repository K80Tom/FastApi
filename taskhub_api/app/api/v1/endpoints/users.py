from fastapi import APIRouter

from app.core.dependencies import CurrentUser
from app.schemas.common import DataResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=DataResponse[UserRead])
async def read_me(current_user: CurrentUser):
    return {"data": UserRead.model_validate(current_user)}
