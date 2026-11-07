from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import DbDep, SettingsDep
from app.schemas.common import DataResponse
from app.schemas.user import TokenResponse, UserCreate, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=DataResponse[UserRead], status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbDep):
    user = await auth_service.register(db, payload)
    return {"data": UserRead.model_validate(user), "message": "user registered"}


@router.post("/token", response_model=TokenResponse)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbDep, settings: SettingsDep):
    token, expires_in = await auth_service.authenticate(db, settings, form.username, form.password)
    return TokenResponse(access_token=token, expires_in=expires_in)
