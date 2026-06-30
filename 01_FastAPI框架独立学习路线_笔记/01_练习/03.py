from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status as http_status
from pydantic import BaseModel, ConfigDict, Field, model_validator


app = FastAPI(title="TaskHub API")


class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    done = "done"
    archived = "archived"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None

    @model_validator(mode="after")
    def validate_update_payload(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        return self


class TaskListItem(BaseModel):
    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    updated_at: str


class TaskRead(TaskListItem):
    description: str
    created_at: str


class TaskListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[TaskListItem]


tasks: dict[int, dict] = {}
next_task_id = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_existing_task(task_id: int) -> dict:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


def build_task(task_id: int, task_data: TaskCreate, created_at: str | None = None) -> dict:
    now = utc_now()
    return {
        "id": task_id,
        **task_data.model_dump(),
        "created_at": created_at or now,
        "updated_at": now,
        "internal_note": "Only stored on the server side",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks", response_model=TaskListResponse)
def list_tasks(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: TaskStatus | None = None,
):
    items = list(tasks.values())
    if status is not None:
        items = [task for task in items if task["status"] == status]

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "page": page,
        "page_size": page_size,
        "total": len(items),
        "items": items[start:end],
    }


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int):
    return get_existing_task(task_id)


@app.post(
    "/tasks",
    response_model=TaskRead,
    status_code=http_status.HTTP_201_CREATED,
)
def create_task(task_data: TaskCreate):
    global next_task_id

    task = build_task(next_task_id, task_data)
    tasks[next_task_id] = task
    next_task_id += 1

    return task


@app.put("/tasks/{task_id}", response_model=TaskRead)
def replace_task(task_id: int, task_data: TaskCreate):
    old_task = get_existing_task(task_id)
    task = build_task(task_id, task_data, created_at=old_task["created_at"])
    tasks[task_id] = task

    return task


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task_data: TaskUpdate):
    task = get_existing_task(task_id)
    changes = task_data.model_dump(exclude_unset=True)

    for field_name, value in changes.items():
        task[field_name] = value

    task["updated_at"] = utc_now()
    return task


@app.delete("/tasks/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    get_existing_task(task_id)
    del tasks[task_id]

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
