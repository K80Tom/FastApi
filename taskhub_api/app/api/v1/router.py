from fastapi import APIRouter

from app.api.v1.endpoints import auth, events, external, files, projects, service, tasks, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(files.router)
api_router.include_router(events.router)
api_router.include_router(external.router)
api_router.include_router(service.router)
