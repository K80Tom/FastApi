# FastAPI 框架独立学习总路线

> 来源：ima知识库 - 练后吃菠萝🍍的知识库 / FastAPI框架学习-Tom

## 目标

先不混入 Agent、RAG、LLM 等 AI 应用内容，单独掌握 FastAPI 框架本体。

- **适用对象**：有 Python 基础、编程基础较好，希望后续用于 AI 应用开发
- **建议周期**：8-10 周
- **时间安排**：工作日每天 1 小时，周末 6-8 小时

学习笔记：
- FastAPI 学习进度
- 第 01 讲：HTTP API 基础与 FastAPI 入门
- 第 02 讲：请求体、HTTP 方法与内存版任务 CRUD
- 第 03 讲：Pydantic 请求模型与响应模型

## 1. 学完后你应该具备的能力

完成这条路线后，你应该能独立完成一个标准 FastAPI 后端项目：

- 设计 RESTful API。
- 使用 Pydantic 做请求和响应校验。
- 使用 APIRouter 拆分业务模块。
- 使用 Depends 管理依赖。
- 使用统一异常处理和统一响应格式。
- 接入 PostgreSQL 数据库。
- 使用 SQLAlchemy 和 Alembic。
- 实现用户注册、登录和鉴权。
- 编写接口测试。
- 使用 Docker / Docker Compose 启动项目。
- 形成一个可复用的 FastAPI 工程模板。

这条路线的最终项目是：**TaskHub API** — 一个标准任务管理后端，包含用户、项目、任务、评论、标签、鉴权、数据库、测试、Docker 部署。

## 2. 学习阶段总览

| 周次 | 主题 |
|------|------|
| 第 1 周 | HTTP API 基础与 FastAPI 入门 |
| 第 2 周 | Pydantic 与请求响应模型 |
| 第 3 周 | APIRouter、项目结构与分层 |
| 第 4 周 | Depends、配置、异常处理、中间件 |
| 第 5 周 | 异步编程、生命周期、后台任务、文件上传 |
| 第 6 周 | 数据库、SQLAlchemy、Alembic |
| 第 7 周 | 鉴权、安全、权限控制 |
| 第 8 周 | 测试、工程质量、Docker 部署 |
| 第 9-10 周 | 综合项目强化，可选 |

## 3. 每周学习节奏

### 工作日

每天 1 小时：

- 10 分钟：复盘昨天内容
- 20 分钟：学习官方文档或源码示例
- 25 分钟：写一个小功能
- 5 分钟：记录笔记和 commit

### 周末

建议每周 6-8 小时：

- 周六：集中写项目功能。
- 周日：补测试、重构、整理 README。

**每周结束都要有一个可运行版本。**

---

## 第 1 周：HTTP API 基础与 FastAPI 入门

### 学习目标

理解 FastAPI 的基本运行方式，知道一个 Python 函数如何变成 HTTP 接口。

### 核心知识

- HTTP 请求和响应。
- REST API 基本设计。
- 常见 HTTP 方法：GET, POST, PUT, PATCH, DELETE
- 常见状态码：200, 201, 204, 400, 401, 403, 404, 409, 422, 500
- FastAPI 应用对象。
- 路径操作函数。
- 路径参数。
- 查询参数。
- 请求体。
- 自动文档 /docs。ReDoc /redoc。
- Uvicorn 启动方式。

### 小项目：TaskHub API，内存版

任务字段：id, title, description, status, priority, created_at, updated_at

状态字段：todo, doing, done, archived

### 必写代码

实现这些接口：

```
GET    /health
GET    /tasks
GET    /tasks/{task_id}
POST   /tasks
PUT    /tasks/{task_id}
PATCH  /tasks/{task_id}
DELETE /tasks/{task_id}
```

第一周可以先用内存字典保存数据。

### 验收标准

- 能启动 FastAPI 服务。
- 能打开 /docs 调接口。
- 能解释路径参数和查询参数的区别。
- 能解释 POST、PUT、PATCH 的区别。
- 能实现任务 CRUD。

---

## 第 2 周：Pydantic 与请求响应模型

### 学习目标

掌握 FastAPI 的数据校验系统。Pydantic 是 FastAPI 的核心之一，也是后续 AI 应用结构化输出的基础。

### 核心知识

- BaseModel
- 类型注解。
- Field
- 默认值。
- 可选字段。
- Enum。
- 嵌套模型。
- List / Dict。
- 请求模型。
- 响应模型。
- response_model
- 422 错误。
- 自定义 validator。
- model_dump()
- model_validate()

### 推荐模型拆分

- TaskCreate
- TaskUpdate
- TaskRead
- TaskListItem
- TaskDetail

不要一个模型从头用到尾。创建、更新、返回通常应该分开。

### 必写代码

给 TaskHub 增加：

- 创建任务校验。
- 更新任务校验。
- 响应模型过滤。
- 状态枚举。
- 优先级枚举。
- 分页参数。

接口示例：`GET /tasks?page=1&page_size=20&status=doing`

### 验收标准

- 能设计请求模型和响应模型。
- 能解释为什么返回模型不应该包含敏感字段。
- 能读懂 422 错误。
- 能使用 Enum 限制状态值。

---

## 第 3 周：APIRouter、项目结构与分层

### 学习目标

把单文件项目重构为真实项目结构。

### 核心知识

- Python package。
- APIRouter
- router 分组。
- API version。
- schema 层。
- service 层。
- repository 层。
- core 配置层。
- main.py 应用组装。

### 分层原则

- router：处理 HTTP 请求和响应
- schema：定义输入输出数据结构
- service：处理业务逻辑
- repository：处理数据访问
- model：定义数据库模型
- core：配置、安全、异常、通用能力

### 推荐目录结构

```
taskhub-api/
  app/
    main.py
    api/
      v1/
        router.py
        endpoints/
          tasks.py
          users.py
    core/
      config.py
      errors.py
      security.py
    schemas/
      task.py
      user.py
    services/
      task_service.py
      user_service.py
    repositories/
      task_repository.py
      user_repository.py
    models/
    db/
  tests/
```

### 必写代码

重构前两周的任务管理 API：

- main.py 只负责创建 app 和注册 router。
- tasks.py 只保留接口函数。
- 业务逻辑移动到 service。
- 内存数据访问移动到 repository。

### 验收标准

- main.py 简洁。
- 新增模块知道放在哪里。
- 不在 router 中堆业务逻辑。
- API 前缀统一为 /api/v1。

---

## 第 4 周：Depends、配置、异常处理与中间件

### 学习目标

掌握 FastAPI 的依赖注入，这是 FastAPI 工程化能力的核心。

### 核心知识

- Depends
- 子依赖。
- router 级依赖。
- 全局依赖。
- yield dependency。
- 配置管理。
- .env
- Pydantic Settings。
- 自定义异常。
- 全局异常处理器。
- 中间件。
- CORS。
- 请求耗时统计。
- Request ID。

### 必写功能

给 TaskHub 增加：

- 应用配置。
- 统一错误格式。
- 请求日志中间件。
- request_id。
- 简单 API Key 依赖。

错误返回格式：

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task not found",
    "request_id": "..."
  }
}
```

### 建议依赖设计

- get_settings
- get_current_request_id
- get_task_service
- verify_api_key

### 验收标准

- 能解释 Depends 解决了什么问题。
- 能把配置从代码中移到环境变量。
- 能返回统一错误格式。
- 能给每个请求生成 request_id。

---

## 第 5 周：异步编程、生命周期、后台任务与文件上传

### 学习目标

掌握 FastAPI 中异步代码的使用方式，以及一些常见高级接口能力。

### 核心知识

- async def
- await
- I/O bound。
- CPU bound。
- 阻塞调用。
- httpx.AsyncClient
- lifespan。
- startup / shutdown。
- BackgroundTasks
- UploadFile
- File
- Form
- StreamingResponse
- WebSocket 基础，可选。

### 重点理解

FastAPI 可以同时支持普通函数和异步函数。

经验规则：

- 调用 async 库 -> endpoint 用 async def
- 调用阻塞库 -> endpoint 可以用 def，或放到线程池/任务队列
- 不确定时 -> 先保证正确，再考虑并发优化

### 必写功能

给 TaskHub 增加：

- 上传任务附件。
- 后台记录操作日志。
- 应用启动时初始化资源。
- 应用关闭时释放资源。
- 一个简单流式接口：`GET /tasks/export/stream`

### 验收标准

- 能解释 async 和普通 def 的区别。
- 能上传文件。
- 能使用 BackgroundTasks 做轻量后台动作。
- 能理解 lifespan 的作用。

---

## 第 6 周：数据库、SQLAlchemy 与 Alembic

### 学习目标

把内存版 TaskHub 改成数据库持久化版本。

### 核心知识

- PostgreSQL 基础。
- SQLAlchemy 2.x。
- Engine。
- Session。
- ORM model。
- relationship。
- transaction。
- Alembic。
- migration。
- repository。
- 数据库连接池。

### 推荐数据库表

users, projects, tasks, comments, tags, task_tags, attachments

### 必写功能

实现数据库版：

- 用户表。
- 项目表。
- 任务表。
- 评论表。
- 标签表。
- 任务和标签多对多关系。
- Alembic migration。
- 数据库初始化文档。

### 任务 API 扩展

```
GET    /projects
POST   /projects
GET    /projects/{project_id}/tasks
POST   /projects/{project_id}/tasks
POST   /tasks/{task_id}/comments
POST   /tasks/{task_id}/tags
```

### 验收标准

- 能写 SQLAlchemy model。
- 能通过 Alembic 生成和执行 migration。
- 能处理一对多、多对多关系。
- 能解释事务的作用。

---

## 第 7 周：鉴权、安全与权限控制

### 学习目标

掌握 Web API 常见安全能力，能实现用户登录和受保护接口。

### 核心知识

- 密码哈希。
- JWT。
- Bearer Token。
- OAuth2 Password flow 基础。
- 当前用户依赖。
- 权限控制。
- CORS。
- API Key。
- 输入限制。
- 常见安全风险。

### 必写功能

给 TaskHub 增加：

```
POST /auth/register
POST /auth/login
GET  /users/me
```

任务接口改成需要登录：

```
GET    /tasks
POST   /tasks
PATCH  /tasks/{task_id}
DELETE /tasks/{task_id}
```

权限规则：

- 用户只能看到自己的项目。
- 项目成员才能看项目任务。
- 只有任务创建者或项目管理员能删除任务。

### 验收标准

- 能注册和登录。
- 能用 Bearer Token 访问受保护接口。
- 能通过 Depends 获取当前用户。
- 能实现基础权限判断。

---

## 第 8 周：测试、工程质量与 Docker 部署

### 学习目标

让项目不只是能跑，还能被测试、被部署、被别人运行。

### 核心知识

- Pytest。
- FastAPI TestClient。
- dependency override。
- 测试数据库。
- Mock。
- 测试鉴权。
- 测试异常。
- Ruff。
- Black。
- Dockerfile。
- Docker Compose。
- 健康检查。
- README。

### 必写测试

至少覆盖：

- health check。
- 注册登录。
- 创建任务。
- 查询任务。
- 更新任务。
- 删除任务。
- 无权限访问。
- 数据校验错误。
- 资源不存在。

### 高阶接口

```
GET  /tasks/search
GET  /tasks/export
GET  /events/stream
POST /tasks/{task_id}/assign
POST /projects/{project_id}/members
```

### Docker Compose 服务

- api
- postgres
- redis，可选

### 验收标准

- 能一键运行测试。
- 能用 Docker Compose 启动项目。
- README 中有清楚的启动步骤。
- /docs 能正常访问。
- 项目结构稳定。
- 核心功能有测试。
- 有基础日志和可观测性。
- 能作为你后续 AI 项目的后端模板。

---

## 第 9-10 周：综合项目强化，可选

如果前 8 周完成得比较顺，可以继续强化 TaskHub API。

### 可选增强功能

- Redis 缓存。
- Redis 限流。
- 分页统一封装。
- 软删除。
- 审计日志。
- 操作历史。
- 导出 CSV。
- WebSocket 通知。
- SSE 通知。
- OpenTelemetry tracing。
- GitHub Actions。
- 更完整的权限模型。

---

## 4. FastAPI 知识地图

### 基础层

路由。参数。请求体。响应。状态码。自动文档。

### 数据校验层

Pydantic。BaseModel。Field。response_model。validator。schema 分层。

### 工程组织层

APIRouter。项目结构。service。repository。config。error。

### 依赖注入层

Depends。当前用户。DB Session。Settings。Client。权限依赖。

### 扩展能力层

Middleware。CORS。BackgroundTasks。UploadFile。StreamingResponse。WebSocket。lifespan。

### 数据层

SQLAlchemy。Alembic。PostgreSQL。Redis。事务。连接池。

### 安全层

OAuth2。JWT。Password hashing。API Key。权限控制。CORS。

### 质量与部署层

Pytest。TestClient。dependency override。Mock。Docker。Docker Compose。CI。日志。监控。

---

## 5. 每周产出要求

| 周次 | 产出 |
|------|------|
| 第 1 周 | 单文件 FastAPI 任务 CRUD |
| 第 2 周 | 使用 Pydantic 的规范任务 API |
| 第 3 周 | 多文件分层项目 |
| 第 4 周 | 有配置、异常、依赖注入、中间件的项目 |
| 第 5 周 | 支持异步、文件上传、后台任务的项目 |
| 第 6 周 | 数据库持久化版本 |
| 第 7 周 | 带用户系统和鉴权的版本 |
| 第 8 周 | 有测试和 Docker 的可交付版本 |

---

## 6. 每日学习记录模板

```
日期：
学习主题：

今天理解的概念：

今天写的代码：

遇到的问题：

解决方案：

明天继续：
```

## 7. 每周复盘模板

```
本周主题：

完成的功能：

新增的接口：

新增的测试：

遇到的最大问题：

本周真正掌握的概念：

下周目标：
```

---

## 8. 推荐资料

### 官方文档

- FastAPI 官方文档：https://fastapi.tiangolo.com/
- FastAPI First Steps：https://fastapi.tiangolo.com/tutorial/first-steps/
- Bigger Applications：https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Dependencies：https://fastapi.tiangolo.com/tutorial/dependencies/
- Security：https://fastapi.tiangolo.com/tutorial/security/
- Testing：https://fastapi.tiangolo.com/tutorial/testing/
- Deployment Docker：https://fastapi.tiangolo.com/deployment/docker/

### 相关文档

- Pydantic：https://docs.pydantic.dev/
- SQLAlchemy：https://docs.sqlalchemy.org/
- Alembic：https://alembic.sqlalchemy.org/
- PostgreSQL：https://www.postgresql.org/docs/
- Docker：https://docs.docker.com/

---

## 9. FastAPI 学习中的常见误区

### 误区 1：所有代码都写在 router 里

router 应该薄一点，只负责 HTTP 层。业务逻辑放 service，数据访问放 repository。

### 误区 2：一个 Pydantic 模型到处用

创建、更新、返回、列表展示通常需要不同模型。

### 误区 3：不理解 Depends，只把它当参数传递工具

Depends 是 FastAPI 组织复杂应用的核心能力，可以管理配置、数据库、用户、权限和外部客户端。

### 误区 4：只会用 Swagger 手动测试

真实项目必须写自动化测试。

### 误区 5：过早引入复杂架构

先写清楚单体 FastAPI 项目，再考虑微服务、复杂中间件和高阶部署。

---

## 10. 完成 FastAPI 路线后的下一步

完成这份路线后，再进入 AI 应用开发会更自然：

- 把 TaskHub 中的普通 CRUD 经验迁移到 conversation / message / document。
- 把文件上传能力迁移到知识库文档上传。
- 把 StreamingResponse 迁移到 LLM 流式输出。
- 把 BackgroundTasks / worker 迁移到文档解析和 embedding。
- 把鉴权和 usage 统计迁移到 AI SaaS 后端。
- 把测试经验迁移到 mock LLM、mock tool call。

换句话说：**FastAPI 框架本体学扎实后，AI/Agent 后端只是把业务对象换成了模型调用、文档、向量、工具和执行轨迹。**
