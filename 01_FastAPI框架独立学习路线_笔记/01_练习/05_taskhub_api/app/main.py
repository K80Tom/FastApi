from fastapi import FastAPI

from app.api.v1.router import api_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用对象，并注册所有路由。"""
    app = FastAPI(title="TaskHub API")
    app.include_router(api_router)
    return app


# uvicorn app.main:app --reload 里的最后一个 app，指的就是这个变量。
app = create_app()
