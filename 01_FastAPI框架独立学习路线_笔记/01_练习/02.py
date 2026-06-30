from datetime import datetime, timezone

from fastapi import Body, FastAPI, HTTPException, Response, status as http_status


app = FastAPI(title="TaskHub API")


ALLOWED_STATUS = {"todo", "doing", "done", "archived"}
ALLOWED_PRIORITY = {"low", "medium", "high"}

tasks = {}
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


def reject_unknown_fields(payload: dict, allowed_fields: set[str]) -> None:
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        fields = ", ".join(sorted(unknown_fields))
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown fields: {fields}",
        )


def validate_title(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="title is required and must be a non-empty string",
        )
    return value.strip()


def validate_description(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="description must be a string",
        )
    return value.strip()


def validate_choice(field_name: str, value, allowed_values: set[str]) -> str:
    if not isinstance(value, str) or value not in allowed_values:
        allowed_text = ", ".join(sorted(allowed_values))
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be one of: {allowed_text}",
        )
    return value


def build_task(task_id: int, payload: dict, created_at: str | None = None) -> dict:
    reject_unknown_fields(
        payload,
        {"title", "description", "status", "priority"},
    )

    now = utc_now()
    return {
        "id": task_id,
        "title": validate_title(payload.get("title")),
        "description": validate_description(payload.get("description", "")),
        "status": validate_choice("status", payload.get("status", "todo"), ALLOWED_STATUS),
        "priority": validate_choice("priority", payload.get("priority", "medium"), ALLOWED_PRIORITY),
        "created_at": created_at or now,
        "updated_at": now,
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(page: int = 1, page_size: int = 20, status: str | None = None):
    if page < 1:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="page must be greater than or equal to 1",
        )
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="page_size must be between 1 and 100",
        )
    if status is not None and status not in ALLOWED_STATUS:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="status must be one of: archived, doing, done, todo",
        )

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


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    return get_existing_task(task_id)


@app.post("/tasks", status_code=http_status.HTTP_201_CREATED)
def create_task(task_data: dict = Body(...)):
    global next_task_id

    task = build_task(next_task_id, task_data)
    tasks[next_task_id] = task
    next_task_id += 1

    return task


@app.put("/tasks/{task_id}")
def replace_task(task_id: int, task_data: dict = Body(...)):
    old_task = get_existing_task(task_id)

    task = build_task(
        task_id=task_id,
        payload=task_data,
        created_at=old_task["created_at"],
    )
    tasks[task_id] = task

    return task


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, task_data: dict = Body(...)):
    task = get_existing_task(task_id)
    reject_unknown_fields(
        task_data,
        {"title", "description", "status", "priority"},
    )

    if not task_data:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required",
        )

    if "title" in task_data:
        task["title"] = validate_title(task_data["title"])
    if "description" in task_data:
        task["description"] = validate_description(task_data["description"])
    if "status" in task_data:
        task["status"] = validate_choice("status", task_data["status"], ALLOWED_STATUS)
    if "priority" in task_data:
        task["priority"] = validate_choice("priority", task_data["priority"], ALLOWED_PRIORITY)

    task["updated_at"] = utc_now()

    return task


@app.delete("/tasks/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    get_existing_task(task_id)
    del tasks[task_id]

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)