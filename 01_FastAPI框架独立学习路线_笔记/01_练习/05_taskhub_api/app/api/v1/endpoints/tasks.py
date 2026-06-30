from typing import Annotated

from fastapi import APIRouter, Query, Response, status as http_status

from app.schemas.task import (
    TaskCreate,
    TaskDetailResponse,
    TaskListResponse,
    TaskPriority,
    TaskStatus,
    TaskUpdate,
)
from app.services import task_service


router = APIRouter()


@router.get("", response_model=TaskListResponse)
def list_tasks(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    owner_id: Annotated[int | None, Query(ge=1)] = None,
    project_id: Annotated[int | None, Query(ge=1)] = None,
    keyword: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
):
    # endpoint 只接收 HTTP 参数，然后把业务交给 service。
    return task_service.list_tasks(
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        owner_id=owner_id,
        project_id=project_id,
        keyword=keyword,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: int):
    return task_service.get_task(task_id)


@router.post(
    "",
    response_model=TaskDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_task(task_data: TaskCreate):
    return task_service.create_task(task_data)


@router.put("/{task_id}", response_model=TaskDetailResponse)
def replace_task(task_id: int, task_data: TaskCreate):
    return task_service.replace_task(task_id, task_data)


@router.patch("/{task_id}", response_model=TaskDetailResponse)
def update_task(task_id: int, task_data: TaskUpdate):
    return task_service.update_task(task_id, task_data)


@router.delete("/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    task_service.delete_task(task_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
