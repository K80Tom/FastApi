# 第 03 讲：Pydantic 请求模型与响应模型

> 来源：ima知识库 - 练后吃菠萝🍍的知识库 / FastAPI框架学习-Tom

学习路线位置：第 2 周
学习主题：Pydantic、请求模型、响应模型、字段校验、response_model
今日目标：把第 02 讲里的手动校验升级成 Pydantic 模型校验，让 TaskHub API 更接近真实项目写法。

## 1. 下一步应该学什么

你现在已经学过：

```
HTTP 请求 -> FastAPI 路由匹配 -> Python 函数执行 -> JSON 响应
```

也已经写过：

```
GET    /health
GET    /tasks
GET    /tasks/{task_id}
POST   /tasks
PUT    /tasks/{task_id}
PATCH  /tasks/{task_id}
DELETE /tasks/{task_id}
```

第 02 讲用的是这种方式接收请求体：

```python
def create_task(task_data: dict = Body(...)):
```

然后自己写函数校验：

```python
validate_title(...)
validate_choice(...)
reject_unknown_fields(...)
```

下一步最应该学的是：**Pydantic 请求模型与响应模型**

因为真实 FastAPI 项目里，很少一直用裸 dict 接收请求体。更常见的写法是：

```python
def create_task(task_data: TaskCreate):
```

这里的 TaskCreate 就是 Pydantic 模型。它能帮你完成：

1. 读取 JSON 请求体
2. 校验字段类型
3. 校验必填字段
4. 校验字符串长度
5. 限制枚举值
6. 自动生成 Swagger 文档
7. 把错误统一变成 422 Validation Error

这也是 FastAPI 很重要的一点：**类型注解不是摆设，而是接口契约。**

## 2. 今天要掌握什么

本讲要掌握 6 件事：

1. Pydantic BaseModel 是什么
2. 请求模型和响应模型为什么要分开
3. Field 如何限制字段
4. Enum 如何限制状态值
5. response_model 如何控制返回内容
6. 422 Validation Error 应该怎么看

学完后，你会把第 02 讲的手动校验版接口升级成：

- TaskCreate -> 创建任务请求体
- TaskUpdate -> 更新任务请求体
- TaskRead -> 任务详情响应体
- TaskListItem -> 任务列表中的单个任务
- TaskListResponse -> 任务列表响应体

## 3. Pydantic 是什么

Pydantic 可以先简单理解成：用 Python 类型注解定义数据结构，并自动完成数据校验的工具。

比如你定义一个模型：

```python
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: str = ""
```

意思是：创建任务时，请求体里应该有 title，它必须是字符串。description 也是字符串，但可以不传，不传时默认是空字符串。

当客户端发送：

```json
{
  "title": "学习 Pydantic"
}
```

FastAPI 会把 JSON 请求体交给 Pydantic，Pydantic 校验通过后，接口函数拿到的是一个 TaskCreate 对象。

当客户端发送：

```json
{
  "title": 123
}
```

或者缺少必填字段时，Pydantic 会校验失败，FastAPI 自动返回：**422 Validation Error**

你不用再自己写一堆 if 判断。

## 4. 请求模型和响应模型为什么要分开

很多初学者会写一个模型到处用：`Task`，创建任务用它，更新任务用它，返回任务也用它。这样短期看省事，后面会很乱。

真实接口里，创建、更新、返回通常不是同一种数据结构。

### 创建任务：TaskCreate

创建任务时，客户端只需要提交：title, description, status, priority

客户端不应该提交：id, created_at, updated_at，因为这些应该由服务端生成。

### 更新任务：TaskUpdate

PATCH 局部更新时，所有字段都应该是可选的：

```json
{
  "status": "done"
}
```

它不需要把 title、description、priority 全部传一遍。

### 返回任务：TaskRead

服务端返回任务时，应该包含：id, title, description, status, priority, created_at, updated_at

但是不应该返回内部字段，比如：internal_note, secret, debug_info

所以模型拆分的核心思想是：

- 请求模型描述客户端能提交什么。
- 响应模型描述服务端愿意返回什么。

## 5. 本讲项目目录

继续放在你的 FastAPI 学习笔记练习目录下。

本讲建议文件：`03.py`

启动命令：

```bash
uvicorn 03:app --reload
```

访问：http://127.0.0.1:8000/docs

## 6. 完整项目示例：Pydantic 版 TaskHub API

先看完整代码。你会发现接口数量和第 02 讲基本一样，但校验逻辑更集中、更清楚。

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
```

## 7. 代码拆解

### BaseModel

```python
class TaskCreate(BaseModel):
```

BaseModel 是 Pydantic 模型的基础类。继承它以后，TaskCreate 就不只是一个普通 Python 类，而是一个可以做数据校验、类型转换和文档生成的数据模型。

当接口这样写：

```python
def create_task(task_data: TaskCreate):
```

FastAPI 会理解为：

- 这个接口需要一个 JSON 请求体。
- 请求体结构应该符合 TaskCreate。
- 校验通过后，把它变成 TaskCreate 对象传给 task_data。

### Enum

```python
class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    done = "done"
    archived = "archived"
```

Enum 用来限制字段只能取固定值。

```python
status: TaskStatus = TaskStatus.todo
```

表示 status 只能是：todo, doing, done, archived

如果客户端提交 `{"status": "started"}`，就会返回 422。

这比第 02 讲手写 `ALLOWED_STATUS = {"todo", "doing", "done", "archived"}` 更规范，也更容易被 Swagger UI 展示成可选项。

### Field

```python
title: str = Field(..., min_length=1, max_length=100)
```

这里可以拆成三层看：

- `title: str` -> title 必须是字符串
- `Field(...)` -> title 是必填字段
- `min_length=1` -> 不能为空字符串
- `max_length=100` -> 最多 100 个字符

description 的写法：

```python
description: str = Field(default="", max_length=500)
```

含义是：description 可以不传，不传时默认是空字符串，最多 500 个字符。

### ConfigDict

```python
model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
```

这里配置了两个规则：

- `extra="forbid"` -> 不允许客户端提交模型里没有定义的字段
- `str_strip_whitespace=True` -> 自动去掉字符串前后的空格

例如客户端提交：

```json
{
  "title": "学习 Pydantic",
  "owner": "me"
}
```

owner 不在 TaskCreate 里，所以会返回 422。

### TaskUpdate

```python
class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
```

PATCH 是局部更新，所以这些字段都可以不传。例如：

```json
{"status": "done"}
```

只修改状态。但完全空对象不应该被接受：`{}`

所以本讲用了：

```python
@model_validator(mode="after")
def validate_update_payload(self):
```

它负责检查：1. PATCH 至少要传一个字段 2. 传入的字段不能是 null

### response_model

```python
@app.get("/tasks/{task_id}", response_model=TaskRead)
```

response_model 的意思是：这个接口返回给客户端的数据，应该整理成 TaskRead 的形状。

本讲代码里，服务端内存任务包含一个内部字段：

```python
"internal_note": "Only stored on the server side"
```

但 TaskRead 没有这个字段，所以响应中不会返回 internal_note。

这就是 response_model 很重要的能力：**内部数据可以多，返回给客户端的数据要受控。**

### model_dump()

```python
task_data.model_dump()
```

model_dump() 会把 Pydantic 模型对象转换成普通 Python 字典。

创建任务时：`{**task_data.model_dump()}` 可以把客户端提交的字段展开到任务字典里。

局部更新时：`changes = task_data.model_dump(exclude_unset=True)`

exclude_unset=True 的意思是：只取客户端真正传了的字段。

比如客户端只传 `{"status": "done"}`，那么 changes 就是 `{"status": TaskStatus.done}`，不会把没传的 title、description、priority 拿出来覆盖原数据。

## 8. 第 02 讲和第 03 讲的区别

第 02 讲的核心写法：

```python
def create_task(task_data: dict = Body(...)):
```

特点是：

- 请求体是普通 dict。
- 字段是否合法，要在函数里手动判断。
- 错误很多时候由你自己决定返回 400。
- Swagger 只能知道这是一个 object，但不知道字段细节。

第 03 讲的核心写法：

```python
def create_task(task_data: TaskCreate):
```

特点是：

- 请求体结构由 TaskCreate 定义。
- 字段类型、长度、枚举值由 Pydantic 自动校验。
- 校验失败自动返回 422。
- Swagger 能展示完整请求体结构。
- 接口函数更干净，业务逻辑更突出。

可以把升级关系理解成：

- 第 02 讲：先理解 HTTP 和 CRUD 数据流
- 第 03 讲：把数据流里的手动校验升级成模型校验

## 9. 在 Swagger UI 里测试

启动服务：

```bash
uvicorn 03:app --reload
```

打开：http://127.0.0.1:8000/docs

### 1. 健康检查

```
GET /health
```

期望结果：`{"status": "ok"}`

### 2. 创建任务

```
POST /tasks
```

请求体：

```json
{
  "title": "完成第 03 讲练习",
  "description": "把手动校验升级成 Pydantic 模型",
  "status": "todo",
  "priority": "medium"
}
```

期望状态码：**201 Created**

注意响应里不会出现 `internal_note`，因为 response_model=TaskRead 已经把它过滤掉了。

### 3. 测试默认值

只提交：

```json
{
  "title": "只提交标题"
}
```

期望服务端自动补默认值：description="", status="todo", priority="medium"

### 4. 测试字段长度

提交空标题：

```json
{"title": ""}
```

期望：**422 Validation Error**，因为 title 设置了 `min_length=1`

### 5. 测试枚举值

提交错误状态：

```json
{"title": "错误状态测试", "status": "started"}
```

期望：**422 Validation Error**，因为 status 只能是 todo/doing/done/archived

### 6. 测试多余字段

提交：

```json
{"title": "多余字段测试", "owner": "me"}
```

期望：**422 Validation Error**，因为模型配置了 `extra="forbid"`

### 7. 查询任务列表

```
GET /tasks?page=1&page_size=20
```

也可以筛选状态：`GET /tasks?status=todo`

如果提交 `GET /tasks?page=0`，会返回 422，因为 `page: Annotated[int, Query(ge=1)] = 1` 限制了 page 必须大于等于 1。

### 8. 局部更新任务

```
PATCH /tasks/1
```

请求体：`{"status": "done"}`

期望只修改状态，其他字段保持不变。

如果提交空对象 `{}`，会返回 422，因为 PATCH 至少要传一个字段。

### 9. 删除任务

```
DELETE /tasks/1
```

期望状态码：**204 No Content**

删除后再查询：`GET /tasks/1` 期望 **404 Not Found**

## 10. 422 Validation Error 应该怎么看

422 不是服务崩了，而是：请求数据没有通过 FastAPI / Pydantic 的校验。

常见原因：

1. 必填字段没传
2. 字段类型不对
3. 字符串太短或太长
4. 枚举值不在允许范围内
5. 多传了不允许的字段
6. 查询参数不符合范围限制

看到 422 时，重点看响应里的：`loc`, `msg`, `type`

比如：

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "type": "string_too_short"
    }
  ]
}
```

意思是：请求体里的 title 字段太短。

## 11. 本讲重点理解

今天最重要的不是背 Pydantic 所有语法，而是理解这个升级：

```
第 02 讲：
客户端 JSON -> dict -> 手动校验 -> 手动组装响应

第 03 讲：
客户端 JSON -> Pydantic 模型 -> 自动校验 -> response_model 控制响应
```

再换成更工程化的话：

- 请求模型负责入口校验。
- 响应模型负责出口约束。
- 业务函数负责真正的业务逻辑。

这会直接影响后面第 3 周的项目分层：

- schemas/task.py 里放 TaskCreate、TaskUpdate、TaskRead
- api/endpoints/tasks.py 里放接口函数
- services/task_service.py 里放业务逻辑
- repositories/task_repository.py 里放数据访问

## 12. 今日练习

请自己完成下面任务：

1. 打开 01_练习/03.py。
2. 启动服务并打开 /docs。
3. 创建一个完整任务。
4. 创建一个只包含 title 的任务，观察默认值。
5. 故意提交空 title，观察 422。
6. 故意提交错误 status，观察 422。
7. 故意提交多余字段 owner，观察 422。
8. 用 GET /tasks?page=0 测试查询参数校验。
9. 用 PATCH /tasks/{task_id} 只修改任务状态。
10. 用 DELETE /tasks/{task_id} 删除任务。

## 13. 自测问题

学完本讲后，尝试回答：

1. BaseModel 是什么？
2. TaskCreate 和 TaskRead 为什么不应该合并成一个模型？
3. Field(..., min_length=1) 里的 ... 表示什么？
4. Enum 解决了什么问题？
5. extra="forbid" 的作用是什么？
6. response_model=TaskRead 的作用是什么？
7. 为什么响应里没有返回 internal_note？
8. model_dump() 的作用是什么？
9. exclude_unset=True 为什么适合 PATCH？
10. 422 错误应该重点看哪些字段？

## 14. 今日验收标准

完成后，你应该能做到：

- 能写出一个 Pydantic BaseModel。
- 能用 Field 限制字段必填、长度和默认值。
- 能用 Enum 限制任务状态和优先级。
- 能解释请求模型和响应模型的区别。
- 能用 response_model 控制接口返回字段。
- 能读懂基础 422 错误。
- 能把第 02 讲的手动校验 CRUD 改成 Pydantic 模型校验 CRUD。

## 15. 学完本讲后的下一步

学完本讲后，第 2 周已经开始。下一步建议继续深化 Pydantic：

**第 04 讲：Pydantic 模型拆分、嵌套模型与更规范的响应结构**

下一讲重点会从"能用模型校验字段"继续推进到：

1. TaskCreate / TaskUpdate / TaskRead / TaskDetail 的边界更清晰
2. 列表响应、详情响应、分页响应更规范
3. 嵌套模型如何表达复杂对象
4. 为什么这些 schema 后面要单独放到 schemas/task.py

也就是说，第 03 讲先把 Pydantic 用起来；第 04 讲会把 Pydantic 用得更像真实项目。
