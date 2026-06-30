from app.repositories import memory_db


def list_tasks() -> list[dict]:
    return list(memory_db.tasks.values())


def get_task_by_id(task_id: int) -> dict | None:
    return memory_db.tasks.get(task_id)


def create_task(record_data: dict) -> dict:
    task_id = memory_db.next_task_id
    task = {
        "id": task_id,
        **record_data,
    }

    memory_db.tasks[task_id] = task
    memory_db.next_task_id += 1
    return task


def replace_task(task_id: int, record_data: dict) -> dict:
    task = {
        "id": task_id,
        **record_data,
    }
    memory_db.tasks[task_id] = task
    return task


def update_task(task_id: int, changes: dict) -> dict:
    task = memory_db.tasks[task_id]
    for field_name, value in changes.items():
        task[field_name] = value
    return task


def delete_task(task_id: int) -> None:
    del memory_db.tasks[task_id]
