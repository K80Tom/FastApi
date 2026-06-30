# 第 04 讲：Pydantic 模型拆分、嵌套模型与规范响应结构

学习路线位置：第 2 周  
学习主题：Pydantic 模型拆分、嵌套模型、分页响应、统一响应结构  
今日目标：在第 03 讲 Pydantic 请求/响应模型的基础上，把 TaskHub API 的数据结构写得更像真实项目，为后面的 APIRouter 和项目分层做准备。

---

## 1. 下一步应该学什么

你现在已经学过：

```text
第 01 讲：HTTP API 基础、路径参数、查询参数、JSON 响应
第 02 讲：请求体、POST / PUT / PATCH / DELETE、内存版 CRUD
第 03 讲：Pydantic 请求模型、响应模型、Field、Enum、response_model
```

你已经能写出一个 Pydantic 版任务 CRUD：

```text
GET    /health
GET    /tasks
GET    /tasks/{task_id}
POST   /tasks
PUT    /tasks/{task_id}
PATCH  /tasks/{task_id}
DELETE /tasks/{task_id}
```

下一步先不要急着进入数据库，也不要马上拆成很多文件。  
现在最适合继续学的是：

```text
Pydantic 模型拆分、嵌套模型与更规范的响应结构
```

原因是：

```text
第 03 讲只是把 dict 手动校验升级成了 Pydantic 自动校验。
第 04 讲要继续学习真实项目里更常见的数据结构写法。
```

真实项目里的响应往往不是一个简单任务对象，而会包含：

```text
任务本身
任务所属项目
任务负责人
任务标签
分页信息
统一响应 code / message / data
```

这就需要你理解：

```text
一个 Pydantic 模型里面，还可以嵌套另一个 Pydantic 模型。
```

这件事后面非常重要，因为 AI 应用里也会大量出现嵌套结构，例如：

```text
conversation
  message
    tool_call
    attachment
    usage
```

所以第 04 讲其实是在打一个很关键的基础：

```text
如何用 Pydantic 表达更复杂、更接近真实业务的数据结构。
```

---

## 2. 今天要掌握什么

本讲要掌握 7 件事：

```text
1. 为什么模型还要继续拆分
2. 什么是嵌套模型
3. 请求体里为什么常用 id，响应体里为什么常用完整对象
4. list[模型] 是什么意思
5. Field(default_factory=list) 为什么比 tags=[] 更稳
6. 分页响应 meta 应该包含哪些信息
7. 统一响应结构 code / message / data / meta 有什么好处
```

学完后，你会把第 03 讲的模型继续升级成：

```text
UserSummary       -> 用户摘要响应模型
ProjectSummary    -> 项目摘要响应模型
TaskTagInput      -> 请求里的任务标签模型
TaskTagRead       -> 响应里的任务标签模型
TaskBase          -> 创建和整体替换共用的基础字段
TaskCreate        -> 创建任务请求模型
TaskUpdate        -> 局部更新任务请求模型
TaskListItem      -> 任务列表项响应模型
TaskDetail        -> 任务详情响应模型
PageMeta          -> 分页信息模型
TaskListResponse  -> 任务列表统一响应模型
TaskDetailResponse -> 任务详情统一响应模型
```

你会发现模型数量变多了。  
这不是为了炫技，而是为了让每个模型只负责一件事。

可以先记住一句话：

```text
模型变多，不一定是复杂；职责混在一起，才是真的复杂。
```

---

## 3. 第 03 讲有什么不够真实

第 03 讲里，任务大概长这样：

```json
{
  "id": 1,
  "title": "学习 Pydantic",
  "description": "理解请求模型和响应模型",
  "status": "todo",
  "priority": "medium",
  "created_at": "...",
  "updated_at": "..."
}
```

这个结构适合入门，但真实任务系统通常还会有：

```text
任务属于哪个项目
任务负责人是谁
任务有哪些标签
列表接口有没有分页信息
接口是否统一返回 code / message
```

比如更真实的任务详情可能是：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": 1,
    "title": "整理接口文档",
    "description": "把任务接口说明补完整",
    "status": "todo",
    "priority": "medium",
    "owner": {
      "id": 1,
      "username": "alice",
      "display_name": "Alice"
    },
    "project": {
      "id": 1,
      "name": "FastAPI 学习项目"
    },
    "tags": [
      {
        "name": "api",
        "color": "#2563eb"
      }
    ],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

这里有一个关键变化：

```text
owner 不是简单字符串，而是一个对象。
project 也不是简单字符串，而是一个对象。
tags 是一个列表，列表里面每一项也是对象。
```

这就是嵌套模型要解决的问题。

---

## 4. 什么是嵌套模型

嵌套模型可以理解为：

```text
一个 Pydantic 模型的字段，类型也是另一个 Pydantic 模型。
```

比如：

```python
from pydantic import BaseModel


class UserSummary(BaseModel):
    id: int
    username: str
    display_name: str


class TaskDetail(BaseModel):
    id: int
    title: str
    owner: UserSummary
```

这里的：

```python
owner: UserSummary
```

意思是：

```text
TaskDetail 里面有一个 owner 字段。
owner 字段不是普通字符串，也不是普通数字。
owner 字段应该长得像 UserSummary。
```

所以响应可以是：

```json
{
  "id": 1,
  "title": "学习嵌套模型",
  "owner": {
    "id": 1,
    "username": "alice",
    "display_name": "Alice"
  }
}
```

注意这里的层级：

```text
TaskDetail
  owner
    id
    username
    display_name
```

这就是嵌套。

---

## 5. 请求体里用 id，响应体里用对象

本讲会引入两个新的概念：

```text
owner_id
project_id
```

创建任务时，客户端提交的是：

```json
{
  "title": "写第 04 讲练习",
  "owner_id": 1,
  "project_id": 1
}
```

为什么请求体里只提交 id？

因为客户端创建任务时，只需要告诉服务端：

```text
这个任务属于哪个项目
这个任务分配给哪个用户
```

项目名称、用户名称这些信息应该由服务端根据 id 查出来，而不是让客户端乱传。

但是响应时，服务端可以返回更友好的对象：

```json
{
  "owner": {
    "id": 1,
    "username": "alice",
    "display_name": "Alice"
  },
  "project": {
    "id": 1,
    "name": "FastAPI 学习项目"
  }
}
```

这背后的思想是：

```text
请求模型：尽量让客户端提交必要信息。
响应模型：尽量让客户端拿到好用的信息。
```

所以本讲会出现这种区别：

```text
TaskCreate 里面有 owner_id / project_id。
TaskDetail 里面有 owner / project。
```

这就是请求模型和响应模型继续拆分的原因。

---

## 6. list[模型] 是什么意思

任务可以有多个标签，例如：

```json
[
  {"name": "api", "color": "#2563eb"},
  {"name": "pydantic", "color": "#16a34a"}
]
```

如果用 Pydantic 表达，可以这样写：

```python
class TaskTagInput(BaseModel):
    name: str
    color: str


class TaskCreate(BaseModel):
    tags: list[TaskTagInput]
```

这里的：

```python
list[TaskTagInput]
```

意思是：

```text
tags 是一个列表。
列表里的每一项，都必须符合 TaskTagInput 的结构。
```

也就是说，每个标签都应该有：

```text
name
color
```

如果客户端传：

```json
{
  "tags": [
    {"name": "api", "color": "#2563eb"}
  ]
}
```

可以通过校验。

如果客户端传：

```json
{
  "tags": [
    {"name": "api", "color": "blue"}
  ]
}
```

本讲代码会返回 422，因为 `color` 要求是十六进制颜色，例如：

```text
#2563eb
#16a34a
#64748b
```

---

## 7. 为什么用 Field(default_factory=list)

你可能会想，默认空标签列表能不能这样写：

```python
tags: list[TaskTagInput] = []
```

入门练习里有时看起来能跑，但不建议这样写。  
更推荐：

```python
tags: list[TaskTagInput] = Field(default_factory=list)
```

你可以先这样理解：

```text
default_factory=list 表示每次创建新模型时，都生成一个新的空列表。
```

为什么这件事重要？

因为列表是可变对象。  
如果多个任务不小心共用同一个默认列表，就可能出现一个任务改标签，另一个任务也受影响的奇怪问题。

现在先不需要深挖 Python 可变默认值的所有细节。  
你先记住这个实践规则：

```text
字段默认值如果是 list / dict / set，优先用 default_factory。
```

常见写法：

```python
tags: list[TaskTagInput] = Field(default_factory=list)
metadata: dict[str, str] = Field(default_factory=dict)
```

---

## 8. 什么是规范分页响应

第 03 讲的列表响应是：

```json
{
  "page": 1,
  "page_size": 20,
  "total": 2,
  "items": [...]
}
```

这个已经比直接返回列表更好。  
第 04 讲会继续把它整理成更规范的结构：

```json
{
  "code": "OK",
  "message": "success",
  "data": [...],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 2,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

这里分成两个区域：

```text
data -> 真正的数据列表
meta -> 和列表相关的附加信息
```

这样客户端拿到响应后会更好处理：

```text
data 用来渲染任务列表
meta 用来渲染分页按钮
```

`total_pages` 的计算规则是：

```python
total_pages = (total + page_size - 1) // page_size
```

如果你暂时看不懂这个公式，可以先记结果：

```text
total=0, page_size=20  -> total_pages=0
total=1, page_size=20  -> total_pages=1
total=20, page_size=20 -> total_pages=1
total=21, page_size=20 -> total_pages=2
total=40, page_size=20 -> total_pages=2
total=41, page_size=20 -> total_pages=3
```

它的作用就是：

```text
只要最后一页还有 1 条数据，也要算作一页。
```

---

## 9. 本讲项目目录

继续放在你的 FastAPI 学习笔记练习目录：

```text
D:\开发\Agent\AI应用开发学习\01_FastAPI框架独立学习路线_笔记\01_练习
```

本讲文件：

```text
04.py
```

启动命令：

```powershell
uvicorn 04:app --reload
```

访问地址：

```text
http://127.0.0.1:8000/docs
```

---

## 10. 完整项目示例：更规范的 Pydantic 版 TaskHub API

这一版仍然是单文件内存版。  
现在先不拆文件，是为了让你集中理解 Pydantic 模型结构。

```python
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


class UserSummary(BaseModel):
    id: int
    username: str
    display_name: str


class ProjectSummary(BaseModel):
    id: int
    name: str


class TaskTagInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=20)
    color: str = Field(default="#64748b", pattern=r"^#[0-9a-fA-F]{6}$")


class TaskTagRead(BaseModel):
    name: str
    color: str


class TaskBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    tags: list[TaskTagInput] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_unique_tag_names(self):
        tag_names = [tag.name.lower() for tag in self.tags]
        if len(tag_names) != len(set(tag_names)):
            raise ValueError("tag names must be unique")
        return self


class TaskCreate(TaskBase):
    owner_id: int = Field(..., ge=1)
    project_id: int = Field(..., ge=1)


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
        if not self.model_fields_set:
            raise ValueError("At least one field is required")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        if "tags" in self.model_fields_set and self.tags is not None:
            tag_names = [tag.name.lower() for tag in self.tags]
            if len(tag_names) != len(set(tag_names)):
                raise ValueError("tag names must be unique")

        return self


class TaskListItem(BaseModel):
    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    owner: UserSummary
    project: ProjectSummary
    tag_count: int
    updated_at: str


class TaskDetail(TaskListItem):
    description: str
    tags: list[TaskTagRead]
    created_at: str


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


def get_existing_user(user_id: int) -> dict:
    user = users.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_existing_project(project_id: int) -> dict:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def build_task(task_id: int, task_data: TaskCreate, created_at: str | None = None) -> dict:
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
```

---

## 11. 配套练习代码位置

我已经把本讲代码整理成：

```text
01_练习/04.py
```

你可以直接进入练习目录启动：

```powershell
cd D:\开发\Agent\AI应用开发学习\01_FastAPI框架独立学习路线_笔记\01_练习
uvicorn 04:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

---

## 12. 代码详细注释

下面重点解释你容易卡住的语法。

### 1. `class UserSummary(BaseModel)`

```python
class UserSummary(BaseModel):
    id: int
    username: str
    display_name: str
```

这表示定义一个用户摘要模型。

```text
UserSummary 是响应模型。
它只放前端需要看的用户信息。
```

为什么叫 Summary？

因为它不是完整用户模型。真实项目里的用户可能还有：

```text
password_hash
email
created_at
is_active
role
```

但任务响应里不一定需要这些，所以只返回摘要。

---

### 2. `owner: UserSummary`

```python
class TaskListItem(BaseModel):
    owner: UserSummary
```

这就是嵌套模型。

意思是：

```text
任务列表项里有 owner。
owner 必须符合 UserSummary 的结构。
```

对应 JSON：

```json
{
  "owner": {
    "id": 1,
    "username": "alice",
    "display_name": "Alice"
  }
}
```

---

### 3. `tags: list[TaskTagInput]`

```python
tags: list[TaskTagInput] = Field(default_factory=list, max_length=5)
```

这行语法可以拆开：

```text
tags                  -> 字段名叫 tags
list[...]             -> tags 是列表
TaskTagInput          -> 列表里的每个元素都必须符合 TaskTagInput
Field(...)            -> 给字段加校验规则
default_factory=list  -> 不传 tags 时，默认生成一个新的空列表
max_length=5          -> 最多 5 个标签
```

合法请求：

```json
{
  "tags": [
    {"name": "api", "color": "#2563eb"},
    {"name": "pydantic", "color": "#16a34a"}
  ]
}
```

非法请求：

```json
{
  "tags": [
    {"name": "api", "color": "blue"}
  ]
}
```

因为 `blue` 不符合本讲要求的颜色格式。

---

### 4. `pattern=r"^#[0-9a-fA-F]{6}$"`

```python
color: str = Field(default="#64748b", pattern=r"^#[0-9a-fA-F]{6}$")
```

这个语法用于限制字符串格式。

你现在不用完全掌握正则表达式，先理解这个规则：

```text
颜色必须是 # 开头，后面跟 6 个十六进制字符。
```

可以通过：

```text
#2563eb
#16a34a
#64748b
```

不能通过：

```text
blue
2563eb
#123
#zzzzzz
```

---

### 5. `class TaskCreate(TaskBase)`

```python
class TaskCreate(TaskBase):
    owner_id: int = Field(..., ge=1)
    project_id: int = Field(..., ge=1)
```

这里用了 Python 的继承。

你可以先这样理解：

```text
TaskCreate 会自动拥有 TaskBase 里面的字段。
然后 TaskCreate 自己再额外增加 owner_id 和 project_id。
```

`TaskBase` 里有：

```text
title
description
status
priority
tags
```

所以 `TaskCreate` 实际上拥有：

```text
title
description
status
priority
tags
owner_id
project_id
```

为什么这样写？

因为创建任务和整体替换任务都需要这几个基础字段。  
把公共字段放进 `TaskBase`，可以减少重复代码。

---

### 6. `Field(..., ge=1)`

```python
owner_id: int = Field(..., ge=1)
```

这行可以拆成：

```text
owner_id: int -> owner_id 必须是整数
Field(...)    -> owner_id 必填
ge=1          -> greater than or equal，必须大于等于 1
```

所以：

```json
{"owner_id": 1}
```

可以。

```json
{"owner_id": 0}
```

会返回 422。

---

### 7. `self.model_fields_set`

```python
if not self.model_fields_set:
    raise ValueError("At least one field is required")
```

这个主要用于 PATCH。

PATCH 是局部更新，所以字段可以都写成可选：

```python
title: str | None = None
status: TaskStatus | None = None
```

但是如果客户端提交空对象：

```json
{}
```

那就没有任何更新意义。

`self.model_fields_set` 可以告诉我们：

```text
客户端这次到底传了哪些字段。
```

如果它是空的，说明客户端什么都没传，于是返回 422。

---

### 8. `model_dump(exclude_unset=True)`

```python
changes = task_data.model_dump(exclude_unset=True)
```

这行也是 PATCH 的核心。

假设客户端只传：

```json
{
  "status": "done"
}
```

那么：

```python
changes
```

大概就是：

```python
{"status": TaskStatus.done}
```

不会包含没传的字段。

如果不用 `exclude_unset=True`，没传的字段可能会以 `None` 的形式出现，容易把原来的值覆盖掉。

所以 PATCH 里要记住：

```text
只修改客户端真正传来的字段。
```

---

### 9. `enrich_task(task)`

```python
def enrich_task(task: dict) -> dict:
    return {
        **task,
        "owner": get_existing_user(task["owner_id"]),
        "project": get_existing_project(task["project_id"]),
        "tag_count": len(task["tags"]),
    }
```

这个函数的作用是：

```text
把内存里保存的任务 dict，转换成适合响应给客户端的结构。
```

内存里保存的是：

```json
{
  "id": 1,
  "owner_id": 1,
  "project_id": 1
}
```

响应时补成：

```json
{
  "id": 1,
  "owner": {"id": 1, "username": "alice", "display_name": "Alice"},
  "project": {"id": 1, "name": "FastAPI 学习项目"},
  "tag_count": 2
}
```

这里体现一个重要思想：

```text
内部存储结构，不一定等于外部响应结构。
```

---

### 10. `**task`

```python
return {
    **task,
    "owner": get_existing_user(task["owner_id"]),
    "project": get_existing_project(task["project_id"]),
}
```

`**task` 的意思是把字典里的键值对展开。

比如：

```python
task = {"id": 1, "title": "学习 FastAPI"}
```

那么：

```python
{
    **task,
    "tag_count": 0,
}
```

等价于：

```python
{
    "id": 1,
    "title": "学习 FastAPI",
    "tag_count": 0,
}
```

你可以把它理解成：

```text
先复制 task 里的所有字段，再补充新的字段。
```

---

### 11. `response_model=TaskDetailResponse`

```python
@app.get("/tasks/{task_id}", response_model=TaskDetailResponse)
```

这表示：

```text
这个接口最终返回给客户端的数据，必须整理成 TaskDetailResponse 的结构。
```

`TaskDetailResponse` 是：

```python
class TaskDetailResponse(BaseModel):
    code: str
    message: str
    data: TaskDetail
```

所以响应结构就是：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": 1,
    "title": "...",
    "owner": {...},
    "project": {...}
  }
}
```

这比直接返回任务对象更统一。

---

### 12. `meta: PageMeta`

```python
class TaskListResponse(BaseModel):
    code: str
    message: str
    data: list[TaskListItem]
    meta: PageMeta
```

列表接口通常需要额外返回分页信息。  
所以这里除了 `data`，还有 `meta`。

可以这样记：

```text
data -> 当前页的数据
meta -> 描述当前页状态的信息
```

`meta` 里有：

```text
page        -> 当前第几页
page_size   -> 每页多少条
total       -> 一共有多少条
total_pages -> 一共有多少页
has_next    -> 是否有下一页
has_prev    -> 是否有上一页
```

---

## 13. 在 Swagger UI 里测试

启动：

```powershell
uvicorn 04:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

### 1. 健康检查

```text
GET /health
```

期望：

```json
{
  "status": "ok"
}
```

### 2. 查看用户列表

```text
GET /users
```

你会看到内置的用户：

```json
[
  {"id": 1, "username": "alice", "display_name": "Alice"},
  {"id": 2, "username": "bob", "display_name": "Bob"}
]
```

创建任务时要用这里的 `id` 作为 `owner_id`。

### 3. 查看项目列表

```text
GET /projects
```

你会看到内置的项目：

```json
[
  {"id": 1, "name": "FastAPI 学习项目"},
  {"id": 2, "name": "TaskHub API"}
]
```

创建任务时要用这里的 `id` 作为 `project_id`。

### 4. 创建任务

```text
POST /tasks
```

请求体：

```json
{
  "title": "完成第 04 讲练习",
  "description": "理解嵌套模型和规范响应结构",
  "status": "todo",
  "priority": "medium",
  "owner_id": 1,
  "project_id": 1,
  "tags": [
    {
      "name": "api",
      "color": "#2563eb"
    },
    {
      "name": "pydantic",
      "color": "#16a34a"
    }
  ]
}
```

期望状态码：

```text
201 Created
```

期望响应结构：

```json
{
  "code": "OK",
  "message": "task created",
  "data": {
    "id": 1,
    "title": "完成第 04 讲练习",
    "description": "理解嵌套模型和规范响应结构",
    "status": "todo",
    "priority": "medium",
    "owner": {
      "id": 1,
      "username": "alice",
      "display_name": "Alice"
    },
    "project": {
      "id": 1,
      "name": "FastAPI 学习项目"
    },
    "tags": [
      {
        "name": "api",
        "color": "#2563eb"
      }
    ],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

注意：响应里不会返回：

```text
owner_id
project_id
internal_note
```

因为 `response_model=TaskDetailResponse` 控制了最终返回结构。

### 5. 创建只带必要字段的任务

请求体：

```json
{
  "title": "最小任务",
  "owner_id": 2,
  "project_id": 2
}
```

期望自动补默认值：

```text
description -> ""
status      -> "todo"
priority    -> "medium"
tags        -> []
```

### 6. 测试标签颜色错误

请求体：

```json
{
  "title": "颜色格式错误",
  "owner_id": 1,
  "project_id": 1,
  "tags": [
    {
      "name": "api",
      "color": "blue"
    }
  ]
}
```

期望：

```text
422 Validation Error
```

因为颜色不是 `#` 加 6 位十六进制字符。

### 7. 测试重复标签

请求体：

```json
{
  "title": "重复标签测试",
  "owner_id": 1,
  "project_id": 1,
  "tags": [
    {
      "name": "api",
      "color": "#2563eb"
    },
    {
      "name": "API",
      "color": "#16a34a"
    }
  ]
}
```

期望：

```text
422 Validation Error
```

因为代码里把标签名转成小写后检查重复，`api` 和 `API` 会被认为是同一个标签。

### 8. 查询任务列表

```text
GET /tasks?page=1&page_size=20
```

期望响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": [
    {
      "id": 1,
      "title": "完成第 04 讲练习",
      "status": "todo",
      "priority": "medium",
      "owner": {...},
      "project": {...},
      "tag_count": 2,
      "updated_at": "..."
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

列表项比详情少一些字段。  
这是正常的，因为列表一般用于快速展示，不一定要返回所有详情。

### 9. 按条件筛选列表

可以测试：

```text
GET /tasks?status=todo
GET /tasks?priority=high
GET /tasks?owner_id=1
GET /tasks?project_id=1
GET /tasks?keyword=练习
```

也可以组合：

```text
GET /tasks?status=todo&owner_id=1&page=1&page_size=10
```

### 10. 查询任务详情

```text
GET /tasks/1
```

详情里会比列表多：

```text
description
tags
created_at
```

### 11. 局部更新任务

```text
PATCH /tasks/1
```

请求体：

```json
{
  "status": "doing",
  "priority": "high"
}
```

期望只修改这两个字段。

再试一次修改负责人：

```json
{
  "owner_id": 2
}
```

响应里的 `owner` 应该从 Alice 变成 Bob。

### 12. 整体替换任务

```text
PUT /tasks/1
```

PUT 使用 `TaskCreate` 作为请求模型，所以需要提交完整任务：

```json
{
  "title": "整体替换后的任务",
  "description": "PUT 会用新内容整体替换任务",
  "status": "done",
  "priority": "high",
  "owner_id": 2,
  "project_id": 2,
  "tags": [
    {
      "name": "review",
      "color": "#f59e0b"
    }
  ]
}
```

### 13. 删除任务

```text
DELETE /tasks/1
```

期望：

```text
204 No Content
```

删除后再查询：

```text
GET /tasks/1
```

期望：

```text
404 Not Found
```

---

## 14. 常见错误和怎么看

### 1. owner_id 不存在

请求体：

```json
{
  "title": "不存在用户测试",
  "owner_id": 999,
  "project_id": 1
}
```

期望：

```text
404 User not found
```

原因：

```text
owner_id 格式是对的，但是业务上找不到这个用户。
```

这和 422 不同。  
422 是请求格式不对，404 是引用的资源不存在。

### 2. owner_id 是 0

请求体：

```json
{
  "title": "owner_id 错误",
  "owner_id": 0,
  "project_id": 1
}
```

期望：

```text
422 Validation Error
```

原因：

```python
owner_id: int = Field(..., ge=1)
```

这里要求 `owner_id >= 1`。

### 3. tags 超过 5 个

请求体里如果传 6 个标签，会返回 422。

原因：

```python
tags: list[TaskTagInput] = Field(default_factory=list, max_length=5)
```

这里限制最多 5 个标签。

### 4. PATCH 空对象

请求体：

```json
{}
```

期望：

```text
422 Validation Error
```

原因：

```text
PATCH 至少应该传一个要修改的字段。
```

### 5. 多余字段

请求体：

```json
{
  "title": "多余字段测试",
  "owner_id": 1,
  "project_id": 1,
  "unknown": "xxx"
}
```

期望：

```text
422 Validation Error
```

原因：

```python
model_config = ConfigDict(extra="forbid")
```

它表示不允许提交模型没有定义的字段。

---

## 15. 第 03 讲和第 04 讲的关系

第 03 讲重点是：

```text
用 Pydantic 替代手动校验。
```

第 04 讲重点是：

```text
用 Pydantic 表达更真实的数据结构。
```

对比一下：

```text
第 03 讲：
TaskCreate
TaskUpdate
TaskRead
TaskListItem
TaskListResponse

第 04 讲：
UserSummary
ProjectSummary
TaskTagInput
TaskTagRead
TaskBase
TaskCreate
TaskUpdate
TaskListItem
TaskDetail
PageMeta
TaskListResponse
TaskDetailResponse
```

看起来模型变多了，但每个模型的职责更清楚。

你要形成这个感觉：

```text
模型不是越少越好。
模型应该刚好表达接口边界。
```

---

## 16. 本讲重点理解

今天最重要的是这 5 句话：

```text
1. 请求模型和响应模型要继续拆分，不能一个模型用到底。
2. 嵌套模型可以表达对象里面还有对象。
3. 请求体里常传 owner_id / project_id，响应体里常返回 owner / project 对象。
4. 列表响应最好把 data 和 meta 分开。
5. response_model 能把内部字段过滤成对外结构。
```

如果你能理解下面这个转换，就说明第 04 讲抓住了：

```text
客户端提交：
owner_id=1, project_id=1

服务端内部保存：
owner_id, project_id, internal_note

服务端响应：
owner 对象, project 对象, 不返回 internal_note
```

这就是后端接口经常在做的事情：

```text
接收简单输入 -> 校验 -> 业务处理 -> 转换成友好的输出
```

---

## 17. 今日练习

请按顺序完成：

1. 打开 `01_练习/04.py`。
2. 启动服务。
3. 打开 `/docs`。
4. 调用 `GET /users`，记住可用的用户 id。
5. 调用 `GET /projects`，记住可用的项目 id。
6. 用完整字段创建一个任务。
7. 用最小字段创建一个任务。
8. 测试错误颜色格式，观察 422。
9. 测试重复标签，观察 422。
10. 查询任务列表，观察 `data` 和 `meta`。
11. 用 `status`、`owner_id`、`keyword` 筛选任务。
12. 查询任务详情，观察详情比列表多哪些字段。
13. 用 PATCH 只修改任务状态。
14. 用 PATCH 修改 owner_id，观察响应里的 owner 改变。
15. 用 PUT 整体替换任务。
16. 删除任务并验证 404。

---

## 18. 自测问题

学完本讲后，尝试回答：

1. 什么是嵌套模型？
2. `owner: UserSummary` 表示什么？
3. `tags: list[TaskTagInput]` 表示什么？
4. 为什么默认空列表推荐用 `Field(default_factory=list)`？
5. 为什么创建任务时传 `owner_id`，响应时返回 `owner` 对象？
6. `TaskBase` 的作用是什么？
7. `TaskCreate(TaskBase)` 是什么意思？
8. `TaskListItem` 和 `TaskDetail` 为什么要分开？
9. `data` 和 `meta` 分别适合放什么？
10. `response_model` 为什么能过滤掉 `internal_note`？
11. 422 和 404 在本讲里分别代表什么？
12. PATCH 为什么要使用 `model_dump(exclude_unset=True)`？

---

## 19. 今日验收标准

完成后，你应该能做到：

- 能写出一个嵌套 Pydantic 模型。
- 能理解 `list[SomeModel]`。
- 能用 `Field(default_factory=list)` 设置列表默认值。
- 能区分请求里的 id 和响应里的嵌套对象。
- 能写出带 `data` 和 `meta` 的列表响应。
- 能解释 `TaskListItem` 和 `TaskDetail` 的区别。
- 能看懂本讲 `04.py` 的主要语法。
- 能在 Swagger UI 里完整测试一遍第 04 讲接口。

---

## 20. 学完本讲后的下一步

学完本讲后，第 2 周的 Pydantic 基础就比较扎实了。

下一步建议进入：

```text
第 05 讲：APIRouter、项目结构与分层入门
```

下一讲会把现在的单文件代码拆成更真实的项目结构：

```text
app/
  main.py
  api/
    v1/
      endpoints/
        tasks.py
  schemas/
    task.py
  services/
    task_service.py
  repositories/
    task_repository.py
```

也就是说：

```text
第 04 讲：先把模型结构想清楚。
第 05 讲：再把代码放到正确的文件里。
```

这样学会更稳。
