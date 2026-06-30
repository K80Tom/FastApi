from app.repositories import memory_db


def list_users() -> list[dict]:
    return list(memory_db.users.values())


def get_user_by_id(user_id: int) -> dict | None:
    return memory_db.users.get(user_id)
