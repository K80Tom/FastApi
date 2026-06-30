from fastapi import APIRouter

from app.api.v1.endpoints import health, projects, tasks, users


# prefix="/api/v1" 表示这个路由器下面的所有接口都会自动加上 /api/v1。
api_router = APIRouter(prefix="/api/v1")

# health.router 里已经写了 /health，所以这里不再额外加 prefix。
api_router.include_router(health.router)

# 这里统一给不同业务模块加路径前缀和 Swagger 分组标签。
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
