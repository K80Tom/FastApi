from fastapi import APIRouter
from sqlalchemy import text

from app.core.dependencies import DbDep

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live():
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: DbDep):
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
