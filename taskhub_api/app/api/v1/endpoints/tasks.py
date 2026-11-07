from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, Response, status

from app.core.dependencies import CurrentUser, DbDep
from app.schemas.common import DataResponse, PageResponse, page_meta
from app.schemas.task import CommentCreate, CommentRead, TaskCreate, TaskPriority, TaskRead, TaskStatus, TaskUpdate
from app.services import notification_service, task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=PageResponse[TaskRead])
async def list_tasks(
    current_user: CurrentUser,
    db: DbDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: TaskPriority | None = None,
    project_id: Annotated[int | None, Query(ge=1)] = None,
    keyword: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
):
    items, total = await task_service.list_tasks(
        db,
        current_user,
        page=page,
        page_size=page_size,
        status=task_status.value if task_status else None,
        priority=priority.value if priority else None,
        project_id=project_id,
        keyword=keyword,
    )
    return {
        "data": [TaskRead.model_validate(item) for item in items],
        "meta": page_meta(page, page_size, total),
    }


@router.get("/{task_id}", response_model=DataResponse[TaskRead])
async def get_task(task_id: int, current_user: CurrentUser, db: DbDep):
    task = await task_service.get_task(db, current_user, task_id)
    return {"data": TaskRead.model_validate(task)}


@router.post("", response_model=DataResponse[TaskRead], status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, current_user: CurrentUser, db: DbDep, background_tasks: BackgroundTasks):
    task = await task_service.create_task(db, current_user, payload)
    background_tasks.add_task(notification_service.log_task_created, task.id)
    return {"data": TaskRead.model_validate(task), "message": "task created"}


@router.patch("/{task_id}", response_model=DataResponse[TaskRead])
async def update_task(task_id: int, payload: TaskUpdate, current_user: CurrentUser, db: DbDep):
    task = await task_service.update_task(db, current_user, task_id, payload)
    return {"data": TaskRead.model_validate(task), "message": "task updated"}


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, current_user: CurrentUser, db: DbDep):
    await task_service.delete_task(db, current_user, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{task_id}/comments", response_model=DataResponse[list[CommentRead]])
async def list_comments(task_id: int, current_user: CurrentUser, db: DbDep):
    comments = await task_service.list_comments(db, current_user, task_id)
    return {"data": [CommentRead.model_validate(item) for item in comments]}


@router.post("/{task_id}/comments", response_model=DataResponse[CommentRead], status_code=status.HTTP_201_CREATED)
async def add_comment(task_id: int, payload: CommentCreate, current_user: CurrentUser, db: DbDep):
    comment = await task_service.add_comment(db, current_user, task_id, payload.content)
    return {"data": CommentRead.model_validate(comment), "message": "comment created"}
