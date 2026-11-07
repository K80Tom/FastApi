from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import require_api_key

router = APIRouter(prefix="/service", tags=["service"])


@router.get("/info")
async def service_info(request: Request, client: Annotated[str, Depends(require_api_key)]):
    return {
        "service": request.app.state.settings.app_name,
        "environment": request.app.state.settings.environment,
        "client": client,
    }
