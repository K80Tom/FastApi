# 本讲还没有接数据库，所以先用内存字典模拟数据表。
# 后面接 SQLAlchemy 时，可以把 repository 改成查询真实数据库。

users: dict[int, dict] = {
    1: {"id": 1, "username": "alice", "display_name": "Alice"},
    2: {"id": 2, "username": "bob", "display_name": "Bob"},
}

projects: dict[int, dict] = {
    1: {"id": 1, "name": "FastAPI 学习项目"},
    2: {"id": 2, "name": "TaskHub API"},
}

tasks: dict[int, dict] = {}
next_task_id = 1
