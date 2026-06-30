from datetime import datetime, timezone

from fastapi import HTTPException, status as http_status

from app.repositories import project_repository, task_repository, user_repository
from app.schemas.common import PageMeta
from app.schemas.task import TaskCreate, TaskPriority, TaskStatus, TaskUpdate


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_existing_task(task_id: int) -> dict:
    task = task_repository.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


def get_existing_user(user_id: int) -> dict:
    user = user_repository.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_existing_project(project_id: int) -> dict:
    project = project_repository.get_project_by_id(project_id)
    if project is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def build_task_record(
    task_data: TaskCreate,
    created_at: str | None = None,
) -> dict:
    """把请求模型转换成内部保存的数据结构。"""
    get_existing_user(task_data.owner_id)
    get_existing_project(task_data.project_id)

    now = utc_now()
    return {
        **task_data.model_dump(),
        "created_at": created_at or now,
        "updated_at": now,
        "internal_note": "Only stored on the server side",
    }


def enrich_task(task: dict) -> dict:
    """把内部任务结构转换成响应结构。"""
    return {
        **task,
        "owner": get_existing_user(task["owner_id"]),
        "project": get_existing_project(task["project_id"]),
        "tag_count": len(task["tags"]),
    }


def build_page_meta(page: int, page_size: int, total: int) -> PageMeta:
    if total == 0:
        total_pages = 0
    else:
        total_pages = (total + page_size - 1) // page_size

    return PageMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


def build_detail_response(message: str, task: dict) -> dict:
    return {
        "code": "OK",
        "message": message,
        "data": enrich_task(task),
    }


def list_tasks(
    page: int,
    page_size: int,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    owner_id: int | None = None,
    project_id: int | None = None,
    keyword: str | None = None,
) -> dict:
    items = task_repository.list_tasks()

    if status is not None:
        items = [task for task in items if task["status"] == status]
    if priority is not None:
        items = [task for task in items if task["priority"] == priority]
    if owner_id is not None:
        items = [task for task in items if task["owner_id"] == owner_id]
    if project_id is not None:
        items = [task for task in items if task["project_id"] == project_id]
    if keyword is not None:
        keyword_lower = keyword.lower()
        items = [
            task
            for task in items
            if keyword_lower in task["title"].lower()
            or keyword_lower in task["description"].lower()
        ]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = [enrich_task(task) for task in items[start:end]]

    return {
        "code": "OK",
        "message": "success",
        "data": page_items,
        "meta": build_page_meta(page, page_size, total),
    }


def get_task(task_id: int) -> dict:
    task = get_existing_task(task_id)
    return build_detail_response("success", task)


def create_task(task_data: TaskCreate) -> dict:
    record_data = build_task_record(task_data)
    task = task_repository.create_task(record_data)
    return build_detail_response("task created", task)


def replace_task(task_id: int, task_data: TaskCreate) -> dict:
    old_task = get_existing_task(task_id)
    record_data = build_task_record(
        task_data,
        created_at=old_task["created_at"],
    )
    task = task_repository.replace_task(task_id, record_data)
    return build_detail_response("task replaced", task)


def update_task(task_id: int, task_data: TaskUpdate) -> dict:
    get_existing_task(task_id)
    changes = task_data.model_dump(exclude_unset=True)

    if "owner_id" in changes:
        get_existing_user(changes["owner_id"])
    if "project_id" in changes:
        get_existing_project(changes["project_id"])

    changes["updated_at"] = utc_now()
    task = task_repository.update_task(task_id, changes)
    return build_detail_response("task updated", task)


def delete_task(task_id: int) -> None:
    get_existing_task(task_id)
    task_repository.delete_task(task_id)
