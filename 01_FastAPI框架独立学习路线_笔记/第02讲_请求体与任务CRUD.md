# 第 02 讲：请求体、HTTP 方法与内存版任务 CRUD

学习路线位置：第 1 周  
学习主题：请求体、POST、PUT、PATCH、DELETE 与内存版任务 CRUD  
今日目标：在第 01 讲 GET 接口的基础上，完成一个可以创建、查询、更新、删除任务的内存版 TaskHub API。

---

## 1. 下一步应该学什么

你已经理解了：

```text
HTTP 请求 -> FastAPI 路由匹配 -> Python 函数执行 -> JSON 响应
```

下一步不要急着进入数据库、登录、复杂项目结构。现在最应该补齐的是：

```text
请求体 + 常见 HTTP 方法 + 内存版 CRUD
```

因为真实后端接口不只是查询，还要处理客户端提交的数据。比如：

```text
创建任务 -> 客户端提交任务标题、描述、状态
更新任务 -> 客户端提交要修改的新内容
删除任务 -> 客户端告诉服务端要删除哪个资源
```

本讲先用内存字典保存任务数据。这样可以把注意力放在 FastAPI 接口设计上，暂时不被数据库、ORM、项目分层打断。

---

## 2. 今天要掌握什么

本讲要掌握 4 件事：

```text
1. 什么是请求体
2. POST / PUT / PATCH / DELETE 分别适合做什么
3. 如何用内存字典保存临时数据
4. 找不到资源或请求数据不合法时如何返回合适的状态码
```

今天完成后，你的接口会从第 01 讲的只读查询：

```text
GET /health
GET /tasks
GET /tasks/{task_id}
```

扩展成完整内存版 CRUD：

```text
GET    /health
GET    /tasks
GET    /tasks/{task_id}
POST   /tasks
PUT    /tasks/{task_id}
PATCH  /tasks/{task_id}
DELETE /tasks/{task_id}
```

---

## 3. 请求体是什么

请求体是 HTTP 请求里专门用来提交复杂数据的部分。

第 01 讲学过的路径参数和查询参数主要放在 URL 里：

```text
GET /tasks/1
GET /tasks?page=1&page_size=20
```

但创建任务时，数据通常比较多，不适合全部塞到 URL 里：

```json
{
  "title": "完成第 02 讲练习",
  "description": "实现 TaskHub 内存版 CRUD",
  "status": "todo",
  "priority": "medium"
}
```

这类 JSON 数据就应该放在请求体里。

简单判断：

```text
标识某个资源 -> 路径参数，例如 /tasks/1
筛选、分页、排序 -> 查询参数，例如 ?page=1&page_size=20
创建或更新的复杂数据 -> 请求体，例如 JSON 对象
```

---

## 4. POST、PUT、PATCH、DELETE 的区别

### POST：创建资源

```text
POST /tasks
```

含义：

```text
请服务端创建一个新任务。
```

客户端通常不指定最终 id，由服务端生成 id。创建成功后，常用状态码是：

```text
201 Created
```

### PUT：整体更新资源

```text
PUT /tasks/1
```

含义：

```text
把 id 为 1 的任务整体替换成请求体里的新内容。
```

PUT 更像是“完整覆盖”。如果任务有 `title`、`description`、`status`、`priority`，那请求体最好把这些字段都传完整。

### PATCH：局部更新资源

```text
PATCH /tasks/1
```

含义：

```text
只修改 id 为 1 的任务中的部分字段。
```

比如只把状态改成 done：

```json
{
  "status": "done"
}
```

### DELETE：删除资源

```text
DELETE /tasks/1
```

含义：

```text
删除 id 为 1 的任务。
```

删除成功后，如果不需要返回内容，常用状态码是：

```text
204 No Content
```

---

## 5. 本讲项目目录

建议继续放在第 1 周练习目录下：

```text
D:\开发\Agent\AI应用开发学习\code\fastapi-framework-lab\week01_basic_api
```

如果你想保留第 01 讲代码，可以新建文件：

```text
week01_task_crud.py
```

启动命令：

```powershell
uvicorn week01_task_crud:app --reload
```

如果你更想沿用 `main.py`，也可以把下面代码写入 `main.py`，启动命令就改成：

```powershell
uvicorn main:app --reload
```

---

## 6. 完整项目示例：内存版 TaskHub API

先直接看完整代码，后面再拆开理解。

```python
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
```

---

## 7. 代码拆解

### 内存字典

```python
tasks = {}
next_task_id = 1
```

这里暂时不用数据库，而是用 Python 字典保存任务。

```text
key   -> 任务 id
value -> 任务详情 dict
```

比如创建两个任务后，内存里的结构大概是：

```python
{
    1: {"id": 1, "title": "任务 1", "status": "todo"},
    2: {"id": 2, "title": "任务 2", "status": "doing"},
}
```

注意：内存数据只适合练习。服务重启后，数据会丢失。

### Body(...)

```python
def create_task(task_data: dict = Body(...)):
```

这里的 `task_data` 来自请求体。

`Body(...)` 的意思是：

```text
这个参数从请求体中读取，并且是必填的。
```

客户端发送：

```json
{
  "title": "完成第 02 讲练习",
  "description": "实现内存版任务 CRUD"
}
```

FastAPI 会把 JSON 对象转换成 Python 字典：

```python
{
    "title": "完成第 02 讲练习",
    "description": "实现内存版任务 CRUD",
}
```

本讲先用 `dict` 接收请求体，并手动校验字段。第 2 周会把这些手动校验改成 Pydantic 模型。

### HTTPException

```python
raise HTTPException(
    status_code=http_status.HTTP_404_NOT_FOUND,
    detail="Task not found",
)
```

当任务不存在时，不应该随便返回空字典，也不应该返回正常的 `200 OK`。  
更合理的是返回：

```text
404 Not Found
```

FastAPI 会把 `HTTPException` 转成标准错误响应。

### status

```python
http_status.HTTP_201_CREATED
http_status.HTTP_204_NO_CONTENT
http_status.HTTP_404_NOT_FOUND
```

这些是 FastAPI 提供的状态码常量。  
它们本质上还是数字，比如：

```text
201
204
404
```

用常量的好处是代码更容易读。

---

## 8. 在 Swagger UI 里测试

启动服务：

```powershell
uvicorn week01_task_crud:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

按下面顺序测试。

### 1. 健康检查

```text
GET /health
```

期望结果：

```json
{
  "status": "ok"
}
```

### 2. 创建任务

```text
POST /tasks
```

请求体：

```json
{
  "title": "完成第 02 讲练习",
  "description": "实现 TaskHub 内存版 CRUD",
  "status": "todo",
  "priority": "medium"
}
```

期望状态码：

```text
201 Created
```

### 3. 查看任务列表

```text
GET /tasks
```

也可以带分页参数：

```text
GET /tasks?page=1&page_size=20
```

如果只看某个状态，可以使用：

```text
GET /tasks?status=todo
```

### 4. 查看任务详情

```text
GET /tasks/1
```

如果任务存在，返回任务详情。  
如果任务不存在，返回：

```text
404 Not Found
```

### 5. 整体更新任务

```text
PUT /tasks/1
```

请求体：

```json
{
  "title": "完成第 02 讲代码和笔记",
  "description": "整体替换任务内容",
  "status": "doing",
  "priority": "high"
}
```

PUT 要理解成整体替换，所以请求体尽量传完整字段。

### 6. 局部更新任务

```text
PATCH /tasks/1
```

请求体：

```json
{
  "status": "done"
}
```

PATCH 只修改传入字段，其他字段保持不变。

### 7. 删除任务

```text
DELETE /tasks/1
```

期望状态码：

```text
204 No Content
```

删除成功后，再访问：

```text
GET /tasks/1
```

应该得到：

```text
404 Not Found
```

---

## 9. 常见错误

### 422 Validation Error

如果访问：

```text
GET /tasks/abc
```

而接口要求：

```python
task_id: int
```

FastAPI 会返回 422，因为 `abc` 不能转换成整数。

如果 `POST /tasks` 时请求体不是 JSON 对象，也可能返回 422。

### 400 Bad Request

本讲代码里，业务规则不满足时返回 400。比如：

```json
{
  "title": ""
}
```

标题为空，不符合创建任务的业务规则，所以返回 400。

再比如：

```json
{
  "title": "错误状态",
  "status": "started"
}
```

`status` 只能是：

```text
todo
doing
done
archived
```

所以也返回 400。

### 404 Not Found

当任务 id 不存在时返回 404：

```text
GET /tasks/999
PUT /tasks/999
PATCH /tasks/999
DELETE /tasks/999
```

---

## 10. 本讲重点理解

今天最重要的不是背代码，而是形成这个后端接口思维：

```text
GET    /tasks           -> 查询任务列表
GET    /tasks/{id}      -> 查询一个任务
POST   /tasks           -> 创建一个任务
PUT    /tasks/{id}      -> 整体替换一个任务
PATCH  /tasks/{id}      -> 局部修改一个任务
DELETE /tasks/{id}      -> 删除一个任务
```

以及这个数据流：

```text
客户端 JSON 请求体
-> FastAPI 读取 Body
-> Python dict
-> 手动校验字段
-> 写入内存字典
-> 返回 JSON 响应
```

---

## 11. 今日练习

请自己动手完成下面任务：

1. 新建 `week01_task_crud.py`。
2. 写入本讲完整示例代码。
3. 启动服务并打开 `/docs`。
4. 创建 2 个任务。
5. 查询任务列表。
6. 查询某个任务详情。
7. 用 `PATCH` 把一个任务状态改成 `done`。
8. 用 `PUT` 整体替换另一个任务。
9. 删除一个任务。
10. 故意查询不存在的任务，观察 404。

---

## 12. 自测问题

学完本讲后，尝试回答：

1. 请求体和查询参数有什么区别？
2. 为什么创建任务通常用 `POST /tasks`？
3. 为什么更新某个任务时路径里要有 `/tasks/{task_id}`？
4. PUT 和 PATCH 的区别是什么？
5. DELETE 成功后为什么可以返回 `204 No Content`？
6. 为什么任务不存在时应该返回 404，而不是 200？
7. 内存字典保存数据有什么缺点？
8. `Body(...)` 表示什么？
9. `HTTPException` 的作用是什么？
10. 本讲为什么先手动校验，而不是一开始就上 Pydantic？

---

## 13. 今日验收标准

完成后，你应该能做到：

- 能解释什么是请求体。
- 能写出 `POST /tasks` 创建任务。
- 能写出 `PUT /tasks/{task_id}` 整体更新任务。
- 能写出 `PATCH /tasks/{task_id}` 局部更新任务。
- 能写出 `DELETE /tasks/{task_id}` 删除任务。
- 能使用内存字典临时保存任务。
- 能在任务不存在时返回 404。
- 能在删除成功时返回 204。
- 能在 `/docs` 中完整测试一遍任务 CRUD。

---

## 14. 学完本讲后的下一步

完成本讲后，第 1 周的核心目标就基本完成了：

```text
单文件 FastAPI 任务 CRUD
```

下一步建议进入第 2 周：

```text
Pydantic 与请求响应模型
```

你会把本讲里的这些手动校验：

```python
validate_title(...)
validate_choice(...)
reject_unknown_fields(...)
```

升级成更规范的模型：

```text
TaskCreate
TaskUpdate
TaskRead
TaskListItem
TaskDetail
```

到那一步，你会明显感觉 FastAPI 写接口变得更干净、更像真实项目。
