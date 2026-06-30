from app.repositories import memory_db


def list_projects() -> list[dict]:
    return list(memory_db.projects.values())


def get_project_by_id(project_id: int) -> dict | None:
    return memory_db.projects.get(project_id)
