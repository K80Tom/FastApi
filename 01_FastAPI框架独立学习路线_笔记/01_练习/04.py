from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status as http_status
from pydantic import BaseModel, ConfigDict, Field, model_validator


app = FastAPI(title="TaskHub API")


# Enum 用来限制字段只能取固定值。
# 这里继承 str，是为了让响应 JSON 里直接显示 "todo" 这种字符串。
class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    done = "done"
    archived = "archived"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# 用户摘要模型：只返回任务里需要展示的用户信息。
# 真实项目里用户可能还有密码哈希、邮箱、角色等字段，但不应该都塞进任务响应。
class UserSummary(BaseModel):
    id: int
    username: str
    display_name: str


# 项目摘要模型：任务详情里只需要知道项目 id 和项目名。
class ProjectSummary(BaseModel):
    id: int
    name: str


# 请求里的标签模型。
# extra="forbid" 表示不允许客户端提交 name/color 之外的字段。
# str_strip_whitespace=True 表示自动去掉字符串前后的空格。
class TaskTagInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=20)
    color: str = Field(default="#64748b", pattern=r"^#[0-9a-fA-F]{6}$")


# 响应里的标签模型。
# 这里和 TaskTagInput 暂时一样，但仍然单独写出来，是为了养成请求模型和响应模型分开的习惯。
class TaskTagRead(BaseModel):
    name: str
    color: str


# TaskBase 放创建任务和整体替换任务都会用到的公共字段。
# 后面 TaskCreate 会继承它，这样不用重复写 title/description/status/priority/tags。
class TaskBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    tags: list[TaskTagInput] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_unique_tag_names(self):
        # self.tags 是一个列表，里面每一项都是 TaskTagInput 对象。
        # tag.name 可以取出每个标签的名字。
        tag_names = [tag.name.lower() for tag in self.tags]
        if len(tag_names) != len(set(tag_names)):
            raise ValueError("tag names must be unique")
        return self


# 创建任务时，客户端提交 owner_id 和 project_id。
# 响应时再由服务端把它们转换成 owner/project 嵌套对象。
class TaskCreate(TaskBase):
    owner_id: int = Field(..., ge=1)
    project_id: int = Field(..., ge=1)


# PATCH 局部更新模型。
# 所有字段都是可选的，因为 PATCH 可以只改一个字段。
class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    owner_id: int | None = Field(default=None, ge=1)
    project_id: int | None = Field(default=None, ge=1)
    tags: list[TaskTagInput] | None = Field(default=None, max_length=5)

    @model_validator(mode="after")
    def validate_update_payload(self):
        # PATCH 不允许提交空对象 {}，因为那样没有任何字段需要更新。
        if not self.model_fields_set:
            raise ValueError("At least one field is required")

        # 本讲为了减少歧义，规定 PATCH 传了某个字段，就不能把它传成 null。
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        # 如果这次 PATCH 修改了 tags，就继续检查标签名是否重复。
        if "tags" in self.model_fields_set and self.tags is not None:
            tag_names = [tag.name.lower() for tag in self.tags]
            if len(tag_names) != len(set(tag_names)):
                raise ValueError("tag names must be unique")

        return self


# 列表项响应模型。
# 列表页通常只返回摘要信息，不一定返回完整 description 和 tags。
class TaskListItem(BaseModel):
    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    owner: UserSummary
    project: ProjectSummary
    tag_count: int
    updated_at: str


# 详情响应模型。
# 它继承 TaskListItem，所以会拥有列表项的字段，再额外增加详情字段。
class TaskDetail(TaskListItem):
    description: str
    tags: list[TaskTagRead]
    created_at: str


# 分页信息模型。
# meta 里放分页相关信息，data 里放真正的数据。
class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class TaskListResponse(BaseModel):
    code: str
    message: str
    data: list[TaskListItem]
    meta: PageMeta


class TaskDetailResponse(BaseModel):
    code: str
    message: str
    data: TaskDetail


# 这里用内存字典模拟用户表。
# key 是用户 id，value 是用户信息。
users: dict[int, dict] = {
    1: {"id": 1, "username": "alice", "display_name": "Alice"},
    2: {"id": 2, "username": "bob", "display_name": "Bob"},
}


# 这里用内存字典模拟项目表。
projects: dict[int, dict] = {
    1: {"id": 1, "name": "FastAPI 学习项目"},
    2: {"id": 2, "name": "TaskHub API"},
}


# 这里用内存字典模拟任务表。
tasks: dict[int, dict] = {}
next_task_id = 1


def utc_now() -> str:
    """返回 UTC 时间字符串。"""
    return datetime.now(timezone.utc).isoformat()


def get_existing_task(task_id: int) -> dict:
    """根据任务 id 获取任务；如果不存在，就返回 404。"""
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


def get_existing_user(user_id: int) -> dict:
    """根据用户 id 获取用户；如果不存在，就返回 404。"""
    user = users.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_existing_project(project_id: int) -> dict:
    """根据项目 id 获取项目；如果不存在，就返回 404。"""
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def build_task(task_id: int, task_data: TaskCreate, created_at: str | None = None) -> dict:
    """把 TaskCreate 请求模型转换成内部保存的任务 dict。"""
    get_existing_user(task_data.owner_id)
    get_existing_project(task_data.project_id)

    now = utc_now()
    return {
        "id": task_id,
        **task_data.model_dump(),
        "created_at": created_at or now,
        "updated_at": now,
        "internal_note": "Only stored on the server side",
    }


def enrich_task(task: dict) -> dict:
    """把内部任务结构转换成适合返回给客户端的结构。"""
    return {
        **task,
        "owner": get_existing_user(task["owner_id"]),
        "project": get_existing_project(task["project_id"]),
        "tag_count": len(task["tags"]),
    }


def build_page_meta(page: int, page_size: int, total: int) -> PageMeta:
    """根据分页参数和总数生成 meta 信息。"""
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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/users", response_model=list[UserSummary])
def list_users():
    return list(users.values())


@app.get("/projects", response_model=list[ProjectSummary])
def list_projects():
    return list(projects.values())


@app.get("/tasks", response_model=TaskListResponse)
def list_tasks(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    owner_id: Annotated[int | None, Query(ge=1)] = None,
    project_id: Annotated[int | None, Query(ge=1)] = None,
    keyword: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
):
    items = list(tasks.values())

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


@app.get("/tasks/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: int):
    task = get_existing_task(task_id)
    return {
        "code": "OK",
        "message": "success",
        "data": enrich_task(task),
    }


@app.post(
    "/tasks",
    response_model=TaskDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_task(task_data: TaskCreate):
    global next_task_id

    task = build_task(next_task_id, task_data)
    tasks[next_task_id] = task
    next_task_id += 1

    return {
        "code": "OK",
        "message": "task created",
        "data": enrich_task(task),
    }


@app.put("/tasks/{task_id}", response_model=TaskDetailResponse)
def replace_task(task_id: int, task_data: TaskCreate):
    old_task = get_existing_task(task_id)
    task = build_task(task_id, task_data, created_at=old_task["created_at"])
    tasks[task_id] = task

    return {
        "code": "OK",
        "message": "task replaced",
        "data": enrich_task(task),
    }


@app.patch("/tasks/{task_id}", response_model=TaskDetailResponse)
def update_task(task_id: int, task_data: TaskUpdate):
    task = get_existing_task(task_id)
    changes = task_data.model_dump(exclude_unset=True)

    if "owner_id" in changes:
        get_existing_user(changes["owner_id"])
    if "project_id" in changes:
        get_existing_project(changes["project_id"])

    for field_name, value in changes.items():
        task[field_name] = value

    task["updated_at"] = utc_now()

    return {
        "code": "OK",
        "message": "task updated",
        "data": enrich_task(task),
    }


@app.delete("/tasks/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    get_existing_task(task_id)
    del tasks[task_id]

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
