# 第 05 讲：APIRouter、项目结构与分层入门

学习路线位置：第 3 周  
学习主题：APIRouter、API 版本、项目目录结构、schema / service / repository 分层  
今日目标：把第 04 讲的单文件 TaskHub API 拆成更接近真实项目的多文件结构，但暂时仍然使用内存字典保存数据。

---

## 1. 下一步应该学什么

你现在已经学完了：

```text
第 01 讲：HTTP API 基础
第 02 讲：请求体和内存版 CRUD
第 03 讲：Pydantic 请求模型和响应模型
第 04 讲：Pydantic 模型拆分、嵌套模型、规范响应结构
```

你已经能在一个文件里写出比较完整的 TaskHub API：

```text
GET    /health
GET    /users
GET    /projects
GET    /tasks
GET    /tasks/{task_id}
POST   /tasks
PUT    /tasks/{task_id}
PATCH  /tasks/{task_id}
DELETE /tasks/{task_id}
```

下一步就不应该继续往一个文件里塞东西了。

现在最应该学的是：

```text
APIRouter、项目结构与分层
```

原因是：

```text
单文件适合入门。
多文件结构适合真实项目。
```

如果所有东西都写在一个文件里，短期很方便，但项目一变大就会出现几个问题：

```text
1. 路由函数越来越多，一个文件很难找代码。
2. Pydantic 模型和接口函数混在一起，边界不清楚。
3. 业务逻辑堆在接口函数里，后面很难测试。
4. 数据访问逻辑和业务逻辑混在一起，后面接数据库会很痛苦。
5. 用户、项目、任务、评论、标签越来越多时，文件会变成一锅粥。
```

所以第 05 讲要做一件很重要的事：

```text
把第 04 讲的单文件代码，拆成真实项目常见的目录结构。
```

---

## 2. 今天要掌握什么

本讲要掌握 8 件事：

```text
1. APIRouter 是什么
2. 为什么接口要加 /api/v1 前缀
3. main.py 应该负责什么
4. endpoints 目录放什么
5. schemas 目录放什么
6. services 目录放什么
7. repositories 目录放什么
8. 为什么本讲先分层，但还不接数据库
```

学完后，你应该能看懂这个结构：

```text
05_taskhub_api/
  app/
    main.py
    api/
      v1/
        router.py
        endpoints/
          health.py
          users.py
          projects.py
          tasks.py
    schemas/
      common.py
      user.py
      project.py
      task.py
    services/
      task_service.py
    repositories/
      memory_db.py
      user_repository.py
      project_repository.py
      task_repository.py
```

先记住一句话：

```text
router 处理 HTTP，schema 定义数据形状，service 处理业务逻辑，repository 处理数据访问。
```

---

## 3. 为什么要学 APIRouter

前面几讲，你一直这样写路由：

```python
@app.get("/tasks")
def list_tasks():
    ...
```

这里的 `app` 是整个 FastAPI 应用对象。

当接口少的时候，这样没有问题。  
但如果接口越来越多，就会变成：

```python
@app.get("/users")
@app.post("/users")
@app.get("/projects")
@app.post("/projects")
@app.get("/tasks")
@app.post("/tasks")
@app.patch("/tasks/{task_id}")
@app.delete("/tasks/{task_id}")
```

所有接口都直接挂在 `app` 上，文件会越来越长。

`APIRouter` 可以先把一组接口放进一个“小路由器”里，再统一注册到 `app`。

例如任务接口可以放在：

```text
app/api/v1/endpoints/tasks.py
```

里面这样写：

```python
from fastapi import APIRouter


router = APIRouter()


@router.get("/tasks")
def list_tasks():
    ...
```

然后在主应用里统一注册：

```python
app.include_router(api_router)
```

这样就变成：

```text
main.py 负责组装应用
tasks.py 负责写任务接口
users.py 负责写用户接口
projects.py 负责写项目接口
```

这就是 APIRouter 的核心价值：

```text
把接口按模块拆开，再统一挂到 FastAPI 应用上。
```

---

## 4. 为什么要加 /api/v1

第 04 讲的接口是：

```text
GET /tasks
POST /tasks
```

第 05 讲会改成：

```text
GET /api/v1/tasks
POST /api/v1/tasks
```

多出来的：

```text
/api/v1
```

表示：

```text
这是 API 接口。
这是第 1 个版本。
```

真实项目里，接口可能会升级。  
比如一开始任务列表返回：

```json
{
  "data": []
}
```

后面你想改成：

```json
{
  "items": [],
  "pagination": {}
}
```

如果直接改老接口，已经接入你接口的前端可能会坏。

所以很多项目会提前设计版本：

```text
/api/v1/tasks
/api/v2/tasks
```

这样将来升级时，可以让老客户端继续用 `v1`，新客户端用 `v2`。

本讲先不做 `v2`，但先养成习惯：

```text
所有业务 API 统一放在 /api/v1 下。
```

---

## 5. 本讲项目目录

这次不再只新增一个 `05.py` 文件，而是新增一个项目目录：

```text
D:\开发\Agent\AI应用开发学习\01_FastAPI框架独立学习路线_笔记\01_练习\05_taskhub_api
```

目录结构：

```text
05_taskhub_api/
  app/
    __init__.py
    main.py
    api/
      __init__.py
      v1/
        __init__.py
        router.py
        endpoints/
          __init__.py
          health.py
          users.py
          projects.py
          tasks.py
    schemas/
      __init__.py
      common.py
      user.py
      project.py
      task.py
    services/
      __init__.py
      task_service.py
    repositories/
      __init__.py
      memory_db.py
      user_repository.py
      project_repository.py
      task_repository.py
```

启动命令也会变化。  
进入项目目录：

```powershell
cd D:\开发\Agent\AI应用开发学习\01_FastAPI框架独立学习路线_笔记\01_练习\05_taskhub_api
```

启动：

```powershell
uvicorn app.main:app --reload
```

访问：

```text
http://127.0.0.1:8000/docs
```

注意：

```text
app.main:app
```

可以拆开理解：

```text
app.main -> app 目录下的 main.py
:app     -> main.py 里面名叫 app 的 FastAPI 应用对象
```

---

## 6. 每一层分别负责什么

### main.py

`main.py` 是应用入口。

它应该主要负责：

```text
1. 创建 FastAPI app
2. 注册 API router
3. 放少量应用级配置
```

它不应该塞很多业务逻辑。

你希望它看起来很薄：

```python
from fastapi import FastAPI

from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="TaskHub API")
    app.include_router(api_router)
    return app


app = create_app()
```

### endpoints

`endpoints` 放接口函数。

比如：

```text
app/api/v1/endpoints/tasks.py
```

这里负责：

```text
1. 定义 URL
2. 接收路径参数、查询参数、请求体
3. 指定 response_model
4. 调用 service 完成业务
5. 返回结果
```

它不应该直接操作内存字典，也不应该堆很多业务规则。

### schemas

`schemas` 放 Pydantic 模型。

比如：

```text
app/schemas/task.py
```

这里负责定义：

```text
TaskCreate
TaskUpdate
TaskListItem
TaskDetail
TaskListResponse
TaskDetailResponse
```

一句话：

```text
schemas 负责接口数据长什么样。
```

### services

`services` 放业务逻辑。

比如：

```text
app/services/task_service.py
```

这里负责：

```text
1. 创建任务时检查 owner_id 是否存在
2. 创建任务时检查 project_id 是否存在
3. 更新任务时处理 PATCH 的 changes
4. 查询任务列表时做筛选和分页
5. 把内部任务结构转换成响应结构
```

一句话：

```text
services 负责业务怎么做。
```

### repositories

`repositories` 放数据访问。

现在我们还没有数据库，所以 repository 先访问内存字典：

```text
memory_db.py
```

后面第 6 周接数据库时，这一层会从：

```text
访问内存 dict
```

升级成：

```text
访问 SQLAlchemy / PostgreSQL
```

但是 router 和 service 尽量不用大改。

这就是提前分层的意义：

```text
现在先把数据访问隔离起来，后面换数据库时不至于到处改。
```

---

## 7. 请求流向

第 05 讲最重要的是看懂请求经过哪些文件。

以创建任务为例：

```text
客户端 POST /api/v1/tasks
-> app/main.py 注册过 api_router
-> app/api/v1/router.py 把 /tasks 分发给 tasks.router
-> app/api/v1/endpoints/tasks.py 的 create_task()
-> app/services/task_service.py 的 create_task()
-> app/repositories/user_repository.py 检查用户
-> app/repositories/project_repository.py 检查项目
-> app/repositories/task_repository.py 保存任务
-> service 组装响应结构
-> endpoint 返回响应
-> FastAPI 根据 response_model 输出 JSON
```

你可以把它画成：

```text
HTTP
  -> endpoint
    -> service
      -> repository
        -> memory_db
```

反过来响应时：

```text
memory_db
  -> repository
    -> service
      -> endpoint
        -> response_model
          -> JSON
```

---

## 8. 配套练习代码

本讲代码已经生成在：

```text
01_练习/05_taskhub_api
```

启动：

```powershell
cd D:\开发\Agent\AI应用开发学习\01_FastAPI框架独立学习路线_笔记\01_练习\05_taskhub_api
uvicorn app.main:app --reload
```

如果当前 Python 环境还没有安装 FastAPI 和 Uvicorn，可以在这个目录下安装依赖：

```powershell
pip install -r requirements.txt
```

打开：

```text
http://127.0.0.1:8000/docs
```

这次接口路径变成：

```text
GET    /api/v1/health
GET    /api/v1/users
GET    /api/v1/projects
GET    /api/v1/tasks
GET    /api/v1/tasks/{task_id}
POST   /api/v1/tasks
PUT    /api/v1/tasks/{task_id}
PATCH  /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}
```

---

## 9. 重点文件讲解

### 1. `app/main.py`

```python
from fastapi import FastAPI

from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="TaskHub API")
    app.include_router(api_router)
    return app


app = create_app()
```

这份文件很短，这是好事。

重点是：

```python
app.include_router(api_router)
```

意思是：

```text
把 api_router 里面收集到的所有接口，注册到 FastAPI 应用里。
```

如果没有这一行，你写在 `endpoints/tasks.py` 里的接口不会出现在 `/docs` 中。

### 2. `app/api/v1/router.py`

```python
from fastapi import APIRouter

from app.api.v1.endpoints import health, projects, tasks, users


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
```

这里有两个重点：

```python
APIRouter(prefix="/api/v1")
```

表示这个路由器下面的接口都会自动加上 `/api/v1`。

```python
include_router(tasks.router, prefix="/tasks")
```

表示任务接口都会自动加上 `/tasks`。

所以如果 `tasks.py` 里写：

```python
@router.get("")
```

最终路径就是：

```text
/api/v1/tasks
```

如果 `tasks.py` 里写：

```python
@router.get("/{task_id}")
```

最终路径就是：

```text
/api/v1/tasks/{task_id}
```

### 3. `app/api/v1/endpoints/tasks.py`

这个文件只处理 HTTP 层。

例如：

```python
@router.post(
    "",
    response_model=TaskDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_task(task_data: TaskCreate):
    return task_service.create_task(task_data)
```

这里没有自己创建任务，而是调用：

```python
task_service.create_task(task_data)
```

这就是分层后的变化：

```text
endpoint 不直接做业务。
endpoint 把事情交给 service。
```

### 4. `app/schemas/task.py`

第 04 讲里所有任务相关 Pydantic 模型，现在移动到了：

```text
app/schemas/task.py
```

比如：

```python
class TaskCreate(TaskBase):
    owner_id: int = Field(..., ge=1)
    project_id: int = Field(..., ge=1)
```

以后你要找“任务请求体和响应体长什么样”，就来这里。

### 5. `app/services/task_service.py`

这个文件是本讲最重要的业务层。

例如创建任务：

```python
def create_task(task_data: TaskCreate) -> dict:
    record_data = build_task_record(task_data)
    task = task_repository.create_task(record_data)
    return build_detail_response("task created", task)
```

可以这样理解：

```text
TaskCreate 是已经校验过的请求数据。
build_task_record() 把请求模型变成内部保存的数据。
task_repository.create_task() 真正保存任务。
build_detail_response() 把内部任务变成统一响应结构。
```

### 6. `app/repositories/memory_db.py`

这里暂时模拟数据库：

```python
users = {...}
projects = {...}
tasks = {}
next_task_id = 1
```

为什么不直接在 service 里写这些字典？

因为后面接数据库时，你希望改的是 repository：

```text
memory_db -> SQLAlchemy
```

而不是让每个接口函数都跟着大改。

---

## 10. 语法重点解释

### 1. `from app.xxx import yyy`

你会看到很多这样的导入：

```python
from app.services import task_service
```

意思是：

```text
从 app/services 这个包里，导入 task_service.py 这个模块。
```

注意启动命令要在 `05_taskhub_api` 目录下执行：

```powershell
uvicorn app.main:app --reload
```

如果你在别的目录执行，Python 可能找不到 `app`，就会出现：

```text
ModuleNotFoundError: No module named 'app'
```

### 2. `__init__.py` 是什么

你会看到很多：

```text
__init__.py
```

它可以先理解成：

```text
告诉 Python：这个目录可以被当成一个包来导入。
```

比如有了：

```text
app/
  __init__.py
  services/
    __init__.py
    task_service.py
```

你就可以写：

```python
from app.services import task_service
```

### 3. `router = APIRouter()`

```python
router = APIRouter()
```

这表示创建一个小路由器。

之后你就可以写：

```python
@router.get("")
def list_tasks():
    ...
```

它和前面写的：

```python
@app.get("/tasks")
```

很像。区别是：

```text
app 是整个应用。
router 是某一组接口的路由器。
```

### 4. `include_router`

```python
api_router.include_router(tasks.router, prefix="/tasks")
```

意思是：

```text
把 tasks.router 里的接口挂到 api_router 下面。
并且统一加上 /tasks 前缀。
```

### 5. 为什么 `@router.get("")` 里是空字符串

在 `tasks.py` 里，列表接口这样写：

```python
@router.get("")
def list_tasks():
    ...
```

因为 `/tasks` 前缀已经在 `router.py` 里统一加过了：

```python
api_router.include_router(tasks.router, prefix="/tasks")
```

所以这里写空字符串，最终就是：

```text
/api/v1/tasks
```

如果你在 `tasks.py` 里再写：

```python
@router.get("/tasks")
```

最终会变成：

```text
/api/v1/tasks/tasks
```

这就是初学 APIRouter 时很常见的错误。

### 6. 为什么 service 返回 dict

本讲里 `task_service.py` 的函数大多返回普通 `dict`。

例如：

```python
return {
    "code": "OK",
    "message": message,
    "data": enrich_task(task),
}
```

然后 endpoint 上有：

```python
response_model=TaskDetailResponse
```

FastAPI 会用 `TaskDetailResponse` 处理最终输出。

也就是说：

```text
service 可以返回 Python dict。
endpoint 用 response_model 约束最终响应。
```

### 7. 为什么 repository 不抛 HTTPException

本讲让 repository 只负责读写数据：

```python
def get_task_by_id(task_id: int) -> dict | None:
    return memory_db.tasks.get(task_id)
```

如果找不到，它返回 `None`。

然后 service 决定：

```python
if task is None:
    raise HTTPException(status_code=404, detail="Task not found")
```

这样做的好处是：

```text
repository 更像数据层。
service 更像业务层。
HTTP 错误由业务层决定。
```

以后如果 repository 换成数据库查询，这个边界也更清楚。

---

## 11. 在 Swagger UI 里测试

启动项目：

```powershell
cd D:\开发\Agent\AI应用开发学习\01_FastAPI框架独立学习路线_笔记\01_练习\05_taskhub_api
uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

### 1. 健康检查

```text
GET /api/v1/health
```

期望：

```json
{
  "status": "ok"
}
```

### 2. 查看用户

```text
GET /api/v1/users
```

记住可用用户：

```text
owner_id = 1
owner_id = 2
```

### 3. 查看项目

```text
GET /api/v1/projects
```

记住可用项目：

```text
project_id = 1
project_id = 2
```

### 4. 创建任务

```text
POST /api/v1/tasks
```

请求体：

```json
{
  "title": "完成第 05 讲练习",
  "description": "把单文件 FastAPI 拆成多文件项目结构",
  "status": "todo",
  "priority": "medium",
  "owner_id": 1,
  "project_id": 1,
  "tags": [
    {
      "name": "router",
      "color": "#2563eb"
    },
    {
      "name": "layer",
      "color": "#16a34a"
    }
  ]
}
```

期望：

```text
201 Created
```

### 5. 查询任务列表

```text
GET /api/v1/tasks?page=1&page_size=20
```

观察：

```text
data 是任务列表
meta 是分页信息
```

### 6. 查询任务详情

```text
GET /api/v1/tasks/1
```

观察：

```text
详情比列表多 description、tags、created_at。
```

### 7. 按条件筛选

```text
GET /api/v1/tasks?status=todo
GET /api/v1/tasks?owner_id=1
GET /api/v1/tasks?project_id=1
GET /api/v1/tasks?keyword=FastAPI
```

### 8. 局部更新

```text
PATCH /api/v1/tasks/1
```

请求体：

```json
{
  "status": "doing",
  "priority": "high"
}
```

### 9. 整体替换

```text
PUT /api/v1/tasks/1
```

请求体：

```json
{
  "title": "整体替换后的第 05 讲任务",
  "description": "PUT 会整体替换任务内容",
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

### 10. 删除任务

```text
DELETE /api/v1/tasks/1
```

期望：

```text
204 No Content
```

---

## 12. 常见错误

### 1. 启动目录不对

如果你在这个目录运行：

```text
D:\开发\Agent\AI应用开发学习
```

然后执行：

```powershell
uvicorn app.main:app --reload
```

可能会报：

```text
ModuleNotFoundError: No module named 'app'
```

正确做法是先进入：

```text
01_练习/05_taskhub_api
```

再运行：

```powershell
uvicorn app.main:app --reload
```

### 2. URL 少了 /api/v1

第 05 讲的接口不是：

```text
/tasks
```

而是：

```text
/api/v1/tasks
```

如果访问 `/tasks` 得到 404，不是接口没写，而是路径变了。

### 3. 在 tasks.py 里重复写 /tasks

如果在 `tasks.py` 里写：

```python
@router.get("/tasks")
```

同时又在 `router.py` 里写：

```python
include_router(tasks.router, prefix="/tasks")
```

最终路径会变成：

```text
/api/v1/tasks/tasks
```

所以本讲 `tasks.py` 里列表接口写的是：

```python
@router.get("")
```

### 4. 循环导入

循环导入指的是：

```text
A 导入 B
B 又导入 A
```

比如：

```text
task_service.py 导入 tasks.py
tasks.py 又导入 task_service.py
```

这会导致 Python 很难正常加载模块。

本讲的方向是：

```text
endpoint -> service -> repository
```

不要让 repository 反过来导入 service，也不要让 service 反过来导入 endpoint。

---

## 13. 第 04 讲和第 05 讲的关系

第 04 讲关注：

```text
数据结构怎么设计
```

第 05 讲关注：

```text
代码应该放在哪里
```

同样是 TaskHub API：

```text
第 04 讲：
所有代码写在 04.py

第 05 讲：
main.py
router.py
endpoints/tasks.py
schemas/task.py
services/task_service.py
repositories/task_repository.py
```

本讲没有引入新业务，也没有引入数据库。  
这样做是为了让你把注意力集中在：

```text
项目结构和代码边界
```

---

## 14. 今日重点理解

今天最重要的是这几句话：

```text
1. APIRouter 用来把接口按模块拆开。
2. /api/v1 是 API 版本前缀。
3. main.py 只负责创建 app 和注册 router。
4. endpoint 负责 HTTP 层，不应该堆业务逻辑。
5. schema 负责请求和响应的数据结构。
6. service 负责业务规则。
7. repository 负责数据访问。
8. 现在 repository 访问内存字典，后面可以换成数据库。
```

你真正要形成的思维是：

```text
一个请求进来，不是所有代码都写在一个函数里。
它会经过 HTTP 层、业务层、数据层。
```

---

## 15. 今日练习

请按顺序完成：

1. 打开 `01_练习/05_taskhub_api`。
2. 先看 `app/main.py`。
3. 再看 `app/api/v1/router.py`。
4. 再看 `app/api/v1/endpoints/tasks.py`。
5. 再看 `app/schemas/task.py`。
6. 再看 `app/services/task_service.py`。
7. 最后看 `app/repositories/task_repository.py`。
8. 启动项目。
9. 打开 `/docs`。
10. 测试 `GET /api/v1/health`。
11. 测试 `GET /api/v1/users` 和 `GET /api/v1/projects`。
12. 创建一个任务。
13. 查询任务列表和详情。
14. 修改任务状态。
15. 删除任务。
16. 故意访问 `/tasks`，观察 404，理解路径前缀变化。

---

## 16. 自测问题

学完本讲后，尝试回答：

1. APIRouter 是什么？
2. 为什么本讲接口变成了 `/api/v1/tasks`？
3. `main.py` 主要负责什么？
4. `app.include_router(api_router)` 的作用是什么？
5. `api_router.include_router(tasks.router, prefix="/tasks")` 的作用是什么？
6. 为什么 `tasks.py` 里列表接口写 `@router.get("")`？
7. `schemas` 目录放什么？
8. `services` 目录放什么？
9. `repositories` 目录放什么？
10. 为什么 repository 暂时访问内存字典？
11. 为什么不要让 endpoint 直接操作 `tasks = {}`？
12. 创建任务请求从 endpoint 到 repository 的调用链路是什么？

---

## 17. 今日验收标准

完成后，你应该能做到：

- 能启动 `05_taskhub_api` 项目。
- 能打开 `/docs` 并看到 `/api/v1/...` 接口。
- 能解释 APIRouter 的作用。
- 能说清楚 `main.py`、`router.py`、`endpoints` 的关系。
- 能说清楚 schema、service、repository 的职责。
- 能看懂任务创建接口从 endpoint 到 service 再到 repository 的调用链路。
- 能理解为什么本讲先分层，还不接数据库。

---

## 18. 学完本讲后的下一步

学完本讲后，你就从“单文件 FastAPI”进入了“项目结构 FastAPI”。

下一讲建议继续：

```text
第 06 讲：分层后的错误处理、业务异常与更清晰的 service 返回
```

下一讲会继续在当前多文件项目上推进：

```text
1. 统一业务错误码
2. 自定义异常类
3. 全局异常处理器
4. 让 service 不直接依赖 HTTPException
5. 为第 4 周 Depends、配置、异常处理中间件做准备
```

也就是说：

```text
第 05 讲：先把文件放对位置。
第 06 讲：再让错误处理更像真实项目。
```
