# 第 07 讲：Depends 依赖注入入门

学习路线位置：第 4 周  
学习主题：Depends、依赖注入、子依赖、router 级依赖  
今日目标：在第 06 讲统一错误处理的基础上，把 endpoint 中"直接导入 service 模块"的方式升级成"通过 Depends 获取 service 实例"，为后续配置管理、数据库 session、当前用户注入打好基础。

---

## 1. 下一步应该学什么

你现在已经学完了：

```text
第 01 讲：HTTP API 基础与 FastAPI 入门
第 02 讲：请求体、HTTP 方法与内存版任务 CRUD
第 03 讲：Pydantic 请求模型与响应模型
第 04 讲：Pydantic 模型拆分、嵌套模型与规范响应结构
第 05 讲：APIRouter、项目结构与分层入门
第 06 讲：业务异常与统一错误处理入门
```

第 05 讲把代码拆成了分层结构。  
第 06 讲把错误处理统一了。

但是你看当前的 `tasks.py`：

```python
from app.services import task_service

@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: int):
    return task_service.get_task(task_id)
```

endpoint 直接导入了 `task_service` 模块，然后调用它的函数。

这个写法能跑，但有几个问题：

```text
1. endpoint 和 task_service 模块强绑定，测试时很难替换。
2. 后面 service 需要数据库 session、配置对象、当前用户，这些东西怎么传进去？
3. 如果多个 endpoint 都需要"先检查 API Key，再获取当前用户"，每个函数都写一遍？
```

所以第 07 讲要学的是：

```text
Depends 依赖注入
```

---

## 2. 本讲先记住一句话

```text
Depends 让你声明"这个 endpoint 需要什么东西"，FastAPI 自动帮你准备好。
```

完整链路：

```text
HTTP 请求
-> FastAPI 看到 endpoint 参数里有 Depends(...)
-> 先调用依赖函数，拿到结果
-> 把结果注入到 endpoint 参数里
-> endpoint 拿到已经准备好的对象，直接用
```

比如：

```text
endpoint 需要 task_service -> Depends 帮你创建
endpoint 需要当前用户 -> Depends 帮你解析 token
endpoint 需要数据库 session -> Depends 帮你打开连接
endpoint 需要配置对象 -> Depends 帮你加载
```

---

## 3. 今天要掌握什么

本讲要掌握 8 件事：

```text
1. 什么是依赖注入
2. 什么是 Depends
3. 怎么把 task_service 改成依赖
4. 什么是子依赖
5. 什么是 router 级依赖
6. Depends 和直接导入有什么区别
7. 后面 Depends 能做什么
8. 什么时候不需要 Depends
```

学完后，你应该能看懂这些词：

```text
Depends
dependency
sub-dependency
Annotated
router dependencies
dependency override
```

---

## 4. 什么是依赖注入

依赖注入是一个通用编程概念，不是 FastAPI 发明的。

核心思想：

```text
一个函数需要某个对象时，不自己去创建或导入，而是让外部传进来。
```

举个日常例子：

```text
不用依赖注入：
你想喝咖啡，自己去磨豆、煮水、冲泡。

用依赖注入：
你说"我需要一杯咖啡"，有人帮你准备好端过来。
```

在代码里：

```text
不用依赖注入：
def get_task(task_id: int):
    service = TaskService(db=get_db(), config=load_config())
    return service.get_task(task_id)

用依赖注入：
def get_task(task_id: int, service: TaskService = Depends(get_task_service)):
    return service.get_task(task_id)
```

好处：

```text
1. endpoint 不需要知道 service 怎么创建的。
2. 测试时可以替换成假的 service。
3. 多个 endpoint 可以复用同一个依赖。
4. 依赖之间可以组合（子依赖）。
```

---

## 5. FastAPI 的 Depends 是什么

`Depends` 是 FastAPI 提供的依赖注入工具。

基本用法：

```python
from fastapi import Depends

def get_task_service():
    return task_service

@router.get("/{task_id}")
def get_task(task_id: int, service = Depends(get_task_service)):
    return service.get_task(task_id)
```

FastAPI 看到 `Depends(get_task_service)` 时会：

```text
1. 调用 get_task_service() 函数
2. 拿到返回值
3. 把返回值赋给 service 参数
4. 然后才执行 endpoint 函数体
```

这意味着：

```text
endpoint 执行之前，依赖已经准备好了。
```

---

## 6. 推荐写法：Annotated + Depends

从 Python 3.9+ 和 FastAPI 0.95+ 开始，推荐用 `Annotated` 配合 `Depends`：

```python
from typing import Annotated
from fastapi import Depends


def get_task_service():
    return task_service


TaskServiceDep = Annotated[object, Depends(get_task_service)]


@router.get("/{task_id}")
def get_task(task_id: int, service: TaskServiceDep):
    return service.get_task(task_id)
```

好处：

```text
1. 类型更清晰。
2. 可以复用类型别名，多个 endpoint 不用重复写 Depends(...)。
3. 代码更干净。
```

`Annotated[object, Depends(get_task_service)]` 的意思是：

```text
这个参数的类型是 object（或更具体的类型）。
它的值通过 Depends(get_task_service) 获取。
```

---

## 7. 当前项目的问题

看当前 `app/api/v1/endpoints/tasks.py`：

```python
from app.services import task_service


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: int):
    return task_service.get_task(task_id)
```

问题 1：endpoint 硬绑定了 task_service 模块

```text
如果你想测试 get_task 这个 endpoint，
你必须让整个 task_service 模块跑起来。
不能轻松替换成一个假的 service。
```

问题 2：后面 service 需要更多东西

```text
现在 task_service 是无状态的模块级函数。
后面接数据库时，service 需要 db session。
接鉴权时，service 需要当前用户。
这些东西怎么传给 service？
```

问题 3：多个 endpoint 可能有公共前置逻辑

```text
比如所有任务接口都要先验证 API Key。
或者所有接口都要先获取当前用户。
用 Depends 可以统一声明，不用每个函数里都手动写。
```

---

## 8. 第 07 讲目标结构

本讲建议在第 06 讲项目基础上新增：

```text
05_taskhub_api/
  app/
    core/
      dependencies.py    <- 新增：存放公共依赖函数
```

并修改：

```text
app/api/v1/endpoints/tasks.py
```

目标是：

```text
1. app/core/dependencies.py 定义依赖函数
2. tasks.py 通过 Depends 获取 service，不再直接导入 task_service
3. 理解子依赖的概念
4. 理解 router 级依赖的概念
```

---

## 9. 最简单的 Depends 示例

先看一个最小的例子，帮你理解 Depends 的运行机制。

假设你有一个依赖函数：

```python
def get_greeting():
    return "Hello from dependency!"
```

在 endpoint 里使用：

```python
from fastapi import Depends

@router.get("/demo")
def demo(message: str = Depends(get_greeting)):
    return {"message": message}
```

访问 `GET /demo` 时：

```text
1. FastAPI 看到 message 参数有 Depends(get_greeting)
2. FastAPI 调用 get_greeting()
3. 返回值 "Hello from dependency!" 赋给 message
4. endpoint 函数体执行，返回 {"message": "Hello from dependency!"}
```

响应：

```json
{
  "message": "Hello from dependency!"
}
```

这就是 Depends 最基本的运行方式：

```text
声明依赖 -> FastAPI 自动调用 -> 结果注入参数
```

---

## 10. 把 task_service 改成依赖

### 第一步：创建依赖函数

新增文件：

```text
app/core/dependencies.py
```

代码：

```python
from app.services import task_service as _task_service_module


def get_task_service():
    """依赖函数：返回 task_service 模块。"""
    return _task_service_module
```

现阶段看起来很简单，好像多此一举。

但这一步的意义是：

```text
endpoint 不再直接写死导入 task_service。
而是通过一个函数"获取" task_service。
后面这个函数可以换成返回 TaskService 类的实例。
测试时可以 override 这个函数，注入假的 service。
```

### 第二步：修改 tasks.py

修改前：

```python
from app.services import task_service


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: int):
    return task_service.get_task(task_id)
```

修改后：

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status as http_status

from app.core.dependencies import get_task_service
from app.schemas.task import (
    TaskCreate,
    TaskDetailResponse,
    TaskListResponse,
    TaskPriority,
    TaskStatus,
    TaskUpdate,
)


router = APIRouter()

TaskServiceDep = Annotated[object, Depends(get_task_service)]


@router.get("", response_model=TaskListResponse)
def list_tasks(
    service: TaskServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    owner_id: Annotated[int | None, Query(ge=1)] = None,
    project_id: Annotated[int | None, Query(ge=1)] = None,
    keyword: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
):
    return service.list_tasks(
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        owner_id=owner_id,
        project_id=project_id,
        keyword=keyword,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: int, service: TaskServiceDep):
    return service.get_task(task_id)


@router.post(
    "",
    response_model=TaskDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_task(task_data: TaskCreate, service: TaskServiceDep):
    return service.create_task(task_data)


@router.put("/{task_id}", response_model=TaskDetailResponse)
def replace_task(task_id: int, task_data: TaskCreate, service: TaskServiceDep):
    return service.replace_task(task_id, task_data)


@router.patch("/{task_id}", response_model=TaskDetailResponse)
def update_task(task_id: int, task_data: TaskUpdate, service: TaskServiceDep):
    return service.update_task(task_id, task_data)


@router.delete("/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, service: TaskServiceDep):
    service.delete_task(task_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
```

关键变化：

```text
1. 不再 from app.services import task_service
2. 改成 from app.core.dependencies import get_task_service
3. 定义类型别名 TaskServiceDep = Annotated[object, Depends(get_task_service)]
4. 每个 endpoint 函数加一个参数 service: TaskServiceDep
5. 函数体里用 service.xxx() 代替 task_service.xxx()
```

从 endpoint 的角度：

```text
"我需要一个 task_service，FastAPI 帮我准备好就行。"
```

---

## 11. Depends 参数不会出现在 Swagger 里

你可能会担心：

```text
service: TaskServiceDep 会不会变成一个请求参数？
```

不会。

FastAPI 看到 `Depends(...)` 时，知道这个参数是内部依赖，不是客户端传的。

所以 Swagger UI 里不会出现 `service` 这个字段。

客户端请求和之前完全一样：

```text
GET /api/v1/tasks/1
```

不需要传 service。

---

## 12. 什么是子依赖

子依赖是指：一个依赖函数里面又使用了另一个依赖。

例如后面你会遇到这样的场景：

```python
def get_db():
    """获取数据库 session。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_task_repository(db=Depends(get_db)):
    """获取 task_repository，它依赖 db。"""
    return TaskRepository(db)


def get_task_service(repo=Depends(get_task_repository)):
    """获取 task_service，它依赖 repository。"""
    return TaskService(repo)
```

调用链：

```text
endpoint 需要 task_service
-> task_service 需要 task_repository
-> task_repository 需要 db session
-> FastAPI 从最底层开始创建，一层一层往上传
```

这就是子依赖。

FastAPI 会自动解析整个依赖树：

```text
get_db() -> get_task_repository(db) -> get_task_service(repo) -> endpoint(service)
```

本讲暂时不需要这么复杂，但你要知道 Depends 支持这种嵌套。

---

## 13. 什么是 yield 依赖

你可能注意到上面 `get_db` 用了 `yield` 而不是 `return`：

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

这是 FastAPI 的 yield dependency。

它的运行方式：

```text
1. yield 之前的代码：在 endpoint 执行之前运行（初始化资源）
2. yield 的值：注入到 endpoint 参数里
3. yield 之后的代码：在 endpoint 执行完之后运行（清理资源）
```

相当于：

```text
打开数据库连接
-> endpoint 使用连接
-> 无论成功还是失败，最后关闭连接
```

本讲暂时用不到 yield 依赖，因为还没接数据库。  
但先理解这个概念，后面第 6 周会用到。

---

## 14. 什么是 router 级依赖

前面的依赖是写在单个 endpoint 参数里的。

如果你希望某个 router 下的所有 endpoint 都自动执行某个依赖，可以用 router 级依赖。

例如：

```python
from fastapi import APIRouter, Depends


def verify_api_key(api_key: str = Header(...)):
    if api_key != "my-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")


router = APIRouter(dependencies=[Depends(verify_api_key)])
```

这样，这个 router 下面的所有接口都会先执行 `verify_api_key`。

```text
不需要每个 endpoint 都写一遍 Depends(verify_api_key)。
```

router 级依赖的特点：

```text
1. 写在 APIRouter(dependencies=[...]) 里。
2. 对这个 router 下所有 endpoint 生效。
3. 依赖函数的返回值不会注入到 endpoint 参数里。
4. 主要用于"前置检查"类逻辑，比如验证 API Key、检查权限。
```

如果你既想做前置检查，又想拿到返回值，那还是写在 endpoint 参数里：

```python
@router.get("/{task_id}")
def get_task(task_id: int, current_user=Depends(get_current_user)):
    ...
```

---

## 15. Depends 和直接导入有什么区别

对比表：

```text
                    直接导入                          Depends
----------------------------------------------------------------------
写法            from app.services import x       service = Depends(get_x)
绑定关系        编译时绑定，改不了                 运行时注入，可替换
测试            需要 mock 模块                    可以用 dependency_override
子依赖          不支持                            支持嵌套依赖链
生命周期管理     自己管                            yield 依赖自动管理
复用            每个文件自己导入                   类型别名统一复用
Swagger 影响    无                               依赖参数不会出现在文档里
```

什么时候用直接导入也没问题？

```text
工具函数、纯计算函数、常量。
比如 utc_now()、build_page_meta() 这些不需要外部资源的函数。
```

什么时候应该用 Depends？

```text
需要外部资源的对象：数据库 session、配置、当前用户、service 实例。
需要可替换性的对象：测试时想换成假的。
有生命周期的对象：打开/关闭连接。
有前置检查的逻辑：验证 token、检查权限。
```

---

## 16. dependency_override：测试时替换依赖

Depends 最实用的好处之一就是测试时可以替换。

FastAPI 提供了 `app.dependency_overrides`：

```python
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_task_service


# 创建一个假的 service
class FakeTaskService:
    def get_task(self, task_id: int):
        return {
            "code": "OK",
            "message": "success",
            "data": {"id": task_id, "title": "Fake task"},
        }


def get_fake_task_service():
    return FakeTaskService()


# 替换依赖
app.dependency_overrides[get_task_service] = get_fake_task_service

client = TestClient(app)
response = client.get("/api/v1/tasks/1")

# 还原
app.dependency_overrides.clear()
```

这样测试时：

```text
endpoint 调用 service.get_task(1)
但 service 已经被替换成 FakeTaskService
不会真的去访问内存数据库或真实数据库
```

如果你用直接导入 `from app.services import task_service`，要做同样的事就需要用 `unittest.mock.patch`，写起来更复杂。

本讲先知道有这个能力就够了，第 8 周学测试时会详细用到。

---

## 17. 依赖函数可以有参数吗

可以。

依赖函数的参数来源和 endpoint 一样：

```text
路径参数
查询参数
请求头
请求体
其他 Depends
```

例如一个从请求头获取 API Key 的依赖：

```python
from fastapi import Header, HTTPException


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "my-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key
```

FastAPI 会自动从请求头里提取 `x-api-key`，传给依赖函数。

如果请求头里没有这个字段，FastAPI 会返回 422。  
如果值不对，依赖函数自己抛异常。

---

## 18. 本讲完整代码变更清单

建议按这个顺序改：

```text
1. 新增 app/core/dependencies.py
2. 修改 app/api/v1/endpoints/tasks.py
3. 启动项目，在 /docs 测试所有接口
4. 确认功能和之前完全一样
```

### 新增 `app/core/dependencies.py` 完整代码

```python
"""公共依赖函数。

本讲先提供 get_task_service。
后续会逐步增加：get_settings、get_db、get_current_user 等。
"""

from app.services import task_service as _task_service_module


def get_task_service():
    """返回 task_service 模块，供 endpoint 通过 Depends 注入。"""
    return _task_service_module
```

### 修改 `app/api/v1/endpoints/tasks.py` 完整代码

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status as http_status

from app.core.dependencies import get_task_service
from app.schemas.task import (
    TaskCreate,
    TaskDetailResponse,
    TaskListResponse,
    TaskPriority,
    TaskStatus,
    TaskUpdate,
)


router = APIRouter()

# 类型别名：所有 endpoint 通过这个获取 task_service
TaskServiceDep = Annotated[object, Depends(get_task_service)]


@router.get("", response_model=TaskListResponse)
def list_tasks(
    service: TaskServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    owner_id: Annotated[int | None, Query(ge=1)] = None,
    project_id: Annotated[int | None, Query(ge=1)] = None,
    keyword: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
):
    # endpoint 只接收 HTTP 参数，通过注入的 service 处理业务。
    return service.list_tasks(
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        owner_id=owner_id,
        project_id=project_id,
        keyword=keyword,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: int, service: TaskServiceDep):
    return service.get_task(task_id)


@router.post(
    "",
    response_model=TaskDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_task(task_data: TaskCreate, service: TaskServiceDep):
    return service.create_task(task_data)


@router.put("/{task_id}", response_model=TaskDetailResponse)
def replace_task(task_id: int, task_data: TaskCreate, service: TaskServiceDep):
    return service.replace_task(task_id, task_data)


@router.patch("/{task_id}", response_model=TaskDetailResponse)
def update_task(task_id: int, task_data: TaskUpdate, service: TaskServiceDep):
    return service.update_task(task_id, task_data)


@router.delete("/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, service: TaskServiceDep):
    service.delete_task(task_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
```

---

## 19. Swagger UI 测试顺序

启动项目：

```powershell
cd D:\开发\Agent\AI应用开发学习\01_FastAPI框架独立学习路线_笔记\01_练习\05_taskhub_api
uvicorn app.main:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

### 1. 确认接口列表和之前一样

你应该看到：

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

Swagger 里不会出现 `service` 参数。

### 2. 创建任务

```text
POST /api/v1/tasks
```

请求体：

```json
{
  "title": "完成第 07 讲依赖注入练习",
  "description": "把 endpoint 从直接导入改成 Depends 注入",
  "status": "todo",
  "priority": "medium",
  "owner_id": 1,
  "project_id": 1,
  "tags": [
    {
      "name": "depends",
      "color": "#8b5cf6"
    }
  ]
}
```

期望：

```text
201 Created
```

### 3. 查询任务

```text
GET /api/v1/tasks/1
```

期望：正常返回任务详情。

### 4. 测试不存在的任务

```text
GET /api/v1/tasks/999
```

期望：

```text
404（如果已经做了第 06 讲的改动，会返回统一错误格式）
```

### 5. 测试分页

```text
GET /api/v1/tasks?page=1&page_size=10
```

期望：正常返回列表。

### 6. 确认所有操作和之前完全一样

```text
PUT    /api/v1/tasks/1  -> 整体替换
PATCH  /api/v1/tasks/1  -> 局部更新
DELETE /api/v1/tasks/1  -> 删除
```

本讲改的是内部实现方式，外部行为不应该有任何变化。

如果你发现有接口报错，说明改动过程中某个地方写错了，回去对照代码检查。

---

## 20. 后续 Depends 的实际用途预览

本讲只用 Depends 注入了 task_service。

后面几讲你会逐步增加更多依赖：

```text
第 08 讲（配置管理）：
  get_settings() -> 返回配置对象
  endpoint 通过 Depends(get_settings) 拿到配置

第 09 讲（中间件与 request_id）：
  get_request_id(request: Request) -> 返回当前请求的 request_id

第 10 讲（API Key 认证）：
  verify_api_key(x_api_key: str = Header(...)) -> 验证 API Key

第 6 周（数据库）：
  get_db() -> yield db session
  get_task_repository(db = Depends(get_db)) -> 返回 repository

第 7 周（鉴权）：
  get_current_user(token: str = Depends(oauth2_scheme)) -> 返回当前用户
  require_admin(user = Depends(get_current_user)) -> 检查管理员权限
```

依赖链越来越长：

```text
get_db -> get_repository -> get_service -> endpoint
                                        -> get_current_user -> endpoint
```

但不管链路多长，endpoint 本身始终只写：

```python
def get_task(task_id: int, service: TaskServiceDep, user: CurrentUserDep):
    ...
```

这就是 Depends 的价值：

```text
复杂的准备工作全部封装在依赖链里。
endpoint 只关心"我需要什么"，不关心"怎么来的"。
```

---

## 21. 常见错误

### 1. 忘记在参数里加 Depends

错误写法：

```python
@router.get("/{task_id}")
def get_task(task_id: int):
    service = get_task_service()  # 手动调用，不是依赖注入
    return service.get_task(task_id)
```

这样虽然能跑，但你失去了：

```text
FastAPI 自动管理生命周期
dependency_override 替换能力
子依赖自动解析
```

正确写法：

```python
@router.get("/{task_id}")
def get_task(task_id: int, service: TaskServiceDep):
    return service.get_task(task_id)
```

### 2. 把 Depends 写在函数体里

错误：

```python
@router.get("/{task_id}")
def get_task(task_id: int):
    service = Depends(get_task_service)  # 错！Depends 不能这样用
    return service.get_task(task_id)
```

`Depends` 只能写在函数参数的默认值里，或者放在 `Annotated` 里。

### 3. 依赖函数忘记 return

错误：

```python
def get_task_service():
    _task_service_module  # 忘记 return 了
```

这样注入到 endpoint 的值是 `None`，调用 `service.get_task()` 会报：

```text
AttributeError: 'NoneType' object has no attribute 'get_task'
```

### 4. 循环依赖

错误：

```text
dependencies.py 导入 task_service
task_service.py 导入 dependencies
```

这会导致循环导入。

本讲的方向：

```text
dependencies.py 可以导入 services
services 不应该导入 dependencies
```

### 5. 在 router 级依赖里想拿返回值

错误理解：

```python
router = APIRouter(dependencies=[Depends(get_task_service)])

@router.get("/{task_id}")
def get_task(task_id: int):
    # 这里拿不到 service！router 级依赖不注入到参数里
    ...
```

router 级依赖只做"前置检查"，不注入返回值。

如果你需要拿到返回值，就写在 endpoint 参数里：

```python
@router.get("/{task_id}")
def get_task(task_id: int, service: TaskServiceDep):
    return service.get_task(task_id)
```

### 6. 同一个请求里重复创建依赖

假设 service 和 另一个依赖都依赖 `get_db`：

```python
def get_task_service(db=Depends(get_db)):
    ...

def get_audit_logger(db=Depends(get_db)):
    ...

@router.post("")
def create_task(service=Depends(get_task_service), logger=Depends(get_audit_logger)):
    ...
```

FastAPI 默认行为：

```text
同一个请求里，同一个依赖函数只会调用一次。
service 和 logger 拿到的是同一个 db session。
```

这是 FastAPI 的缓存机制，大多数时候是你想要的行为。

如果你确实想每次都创建新的，可以用 `use_cache=False`：

```python
Depends(get_db, use_cache=False)
```

但通常不需要。

---

## 22. 今日练习

请按顺序完成：

1. 先确认第 05 讲（或第 06 讲）项目能正常启动。
2. 新增 `app/core/dependencies.py`。
3. 在里面定义 `get_task_service` 函数。
4. 修改 `app/api/v1/endpoints/tasks.py`：
   - 删除 `from app.services import task_service`。
   - 添加 `from app.core.dependencies import get_task_service`。
   - 定义 `TaskServiceDep = Annotated[object, Depends(get_task_service)]`。
   - 每个 endpoint 加一个 `service: TaskServiceDep` 参数。
   - 把 `task_service.xxx()` 改成 `service.xxx()`。
5. 启动项目。
6. 打开 `/docs`，确认 Swagger 里看不到 `service` 参数。
7. 创建一个任务。
8. 查询任务列表和详情。
9. 更新任务。
10. 删除任务。
11. 测试不存在的任务（确认错误处理没有被破坏）。
12. 确认所有功能和改动前完全一致。

---

## 23. 本讲和前几讲的关系

```text
第 05 讲：把代码拆成层（endpoint / service / repository）。
第 06 讲：把错误处理统一起来（AppError / exception handler）。
第 07 讲：用 Depends 管理层与层之间的依赖关系。
```

第 05 讲解决的是：

```text
代码放在哪里。
```

第 06 讲解决的是：

```text
错误在哪里产生，在哪里统一返回。
```

第 07 讲解决的是：

```text
endpoint 怎么拿到 service。
后面 service 怎么拿到 db、config、user。
```

合起来看项目演进：

```text
第 01-04 讲：单文件，什么都堆在一起
第 05 讲：多文件，按职责分层
第 06 讲：错误流程规范化
第 07 讲：对象获取方式规范化
```

---

## 24. Depends 解决了什么问题（总结）

```text
问题 1：endpoint 和 service 强绑定
解决：通过 Depends 注入，可替换。

问题 2：后面 service 需要 db、config、user
解决：子依赖链，一层一层自动注入。

问题 3：多个 endpoint 有公共前置逻辑
解决：router 级依赖，统一声明。

问题 4：测试时难以替换组件
解决：dependency_override。

问题 5：资源生命周期管理（打开/关闭连接）
解决：yield 依赖。
```

---

## 25. 今日重点理解

今天最重要的是这几句话：

```text
1. Depends 是 FastAPI 的依赖注入工具。
2. 依赖注入 = "我需要什么，框架帮我准备好"。
3. 依赖函数通过 Depends(...) 声明在 endpoint 参数里。
4. FastAPI 自动调用依赖函数，把返回值注入到参数。
5. Depends 参数不会出现在 Swagger 文档里。
6. 推荐用 Annotated + Depends 定义类型别名。
7. 子依赖：依赖函数里可以再用 Depends。
8. router 级依赖：对所有 endpoint 生效，但不注入返回值。
9. yield 依赖：可以管理资源的打开和关闭。
10. dependency_override：测试时替换依赖。
```

---

## 26. 自测问题

学完本讲后，尝试回答：

1. 什么是依赖注入？
2. `Depends` 是什么？
3. FastAPI 看到 `Depends(get_task_service)` 时会做什么？
4. 为什么推荐用 `Annotated[object, Depends(...)]`？
5. `TaskServiceDep` 这个类型别名有什么好处？
6. Depends 声明的参数会出现在 Swagger 里吗？
7. 什么是子依赖？
8. 什么是 yield 依赖？它解决什么问题？
9. 什么是 router 级依赖？它和 endpoint 级依赖有什么区别？
10. `dependency_overrides` 是什么？什么时候用？
11. 本讲改动后，API 的外部行为变了吗？
12. 后面 service 需要数据库 session 时，怎么通过 Depends 传进去？
13. 什么时候不需要用 Depends，直接导入就行？
14. 同一个请求里，同一个依赖函数会被调用几次？

---

## 27. 今日验收标准

完成后，你应该能做到：

- 能说清楚 `Depends` 解决了什么问题。
- 能定义一个依赖函数 `get_task_service`。
- 能用 `Annotated + Depends` 定义类型别名。
- 能把 endpoint 从直接导入改成 Depends 注入。
- 能确认改动后所有接口功能不变。
- 能解释 Swagger 里为什么看不到 `service` 参数。
- 能说出子依赖的概念。
- 能说出 router 级依赖的作用。
- 能说出 `dependency_overrides` 的作用。
- 能画出 `endpoint -> Depends -> service -> repository` 的调用链。

---

## 28. 学完本讲后的下一步

学完第 07 讲后，你已经掌握了 FastAPI 最核心的工程化能力之一：

```text
用 Depends 声明依赖，让 FastAPI 自动管理对象的创建和注入。
```

下一讲建议进入：

```text
第 08 讲：配置管理与 .env
```

下一讲要解决的问题是：

```text
现在项目里的配置（比如 API 标题、数据库地址、密钥）写死在代码里。
怎么把配置移到 .env 文件？
怎么用 Pydantic Settings 加载配置？
怎么通过 Depends 把配置注入到需要的地方？
```

也就是说：

```text
第 05 讲：把项目拆成层。
第 06 讲：把错误处理统一起来。
第 07 讲：用 Depends 管理对象和依赖关系。
第 08 讲：用 Pydantic Settings + Depends 管理配置。
```
