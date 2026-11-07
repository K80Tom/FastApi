# TaskHub API

与仓库 27 讲中文教程对应的最终 FastAPI 示例工程。包含异步 SQLAlchemy、Alembic、JWT、项目资源权限、附件、实时通信、测试、CI 和 Docker Compose。

## 1. 环境要求

- Python 3.12+
- 本地学习默认 SQLite；Compose 使用 PostgreSQL 16
- Docker 与 Docker Compose（仅容器启动需要）

## 2. 本地启动

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell：.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

访问：

- `GET /health/live`：进程存活；
- `GET /health/ready`：应用与数据库就绪；
- `/docs`：Swagger UI；
- `/redoc`：ReDoc。

如果仅做本地快速实验，可在 `.env` 设置 `AUTO_CREATE_TABLES=true`，由 lifespan 创建缺失表。生产和迁移练习应保持 `false`，显式执行 `alembic upgrade head`。

## 3. 配置

| 环境变量 | 本地示例/默认 | 说明 |
|---|---|---|
| `ENVIRONMENT` | `development` | 生产设为 `production`，启用严格 secret 检查 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./taskhub.db` | 异步数据库 URL |
| `JWT_SECRET_KEY` | `.env.example` 占位值 | 生产至少 32 字符并独立注入 |
| `JWT_ALGORITHM` | `HS256` | 解码算法白名单 |
| `JWT_ISSUER` | `taskhub-api` | issuer 校验 |
| `JWT_AUDIENCE` | `taskhub-client` | audience 校验 |
| `JWT_EXPIRE_MINUTES` | `60` | Token 有效期 |
| `CORS_ORIGINS` | 两个本地前端源 | JSON 列表；不要随意使用通配符加凭据 |
| `API_KEY_ENABLED` | `false` | 服务接口 API Key 开关 |
| `API_KEY` | 空 | 启用 API Key 时必须配置，否则启动失败 |
| `UPLOAD_DIR` | `var/uploads` | 服务端附件目录 |
| `MAX_UPLOAD_BYTES` | `5242880` | 单附件最大字节数 |
| `EXTERNAL_TIMEOUT_SECONDS` | `5.0` | 外部 HTTP 超时 |
| `AUTO_CREATE_TABLES` | `false` | 本地实验建表；生产保持关闭 |

`.env` 已被 Git 和 Docker 忽略，不能提交真实凭据。

## 4. 第一条业务链路

注册：

```bash
curl -s http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email":"alice@example.com",
    "username":"alice",
    "display_name":"Alice",
    "password":"correct-horse-123"
  }'
```

登录使用 OAuth2 form，不是 JSON：

```bash
curl -s http://127.0.0.1:8000/api/v1/auth/token \
  -X POST \
  -d 'username=alice&password=correct-horse-123'
```

设置 Token：

```bash
export TOKEN='替换为 access_token'
curl -s http://127.0.0.1:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

创建项目：

```bash
curl -s http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"FastAPI Course","description":"TaskHub"}'
```

创建任务时把 `project_id` 换成上一步真实 ID：

```bash
curl -s http://127.0.0.1:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "project_id":1,
    "title":"完成第一条任务",
    "status":"todo",
    "priority":"high",
    "tags":[{"name":"backend","color":"#2563eb"}]
  }'
```

更多评论、附件、SSE、WebSocket 和权限负向用例见根目录第 13、14、21、27 讲。

## 5. 主要接口

| 方法 | 路径 | 功能 |
|---|---|---|
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/token` | 登录 |
| GET | `/api/v1/users/me` | 当前用户 |
| GET/POST | `/api/v1/projects` | 项目列表/创建 |
| GET | `/api/v1/projects/{project_id}` | 项目详情 |
| POST | `/api/v1/projects/{project_id}/members` | 添加项目成员 |
| GET/POST | `/api/v1/tasks` | 任务筛选分页/创建 |
| GET/PATCH/DELETE | `/api/v1/tasks/{task_id}` | 任务详情/更新/删除 |
| GET/POST | `/api/v1/tasks/{task_id}/comments` | 评论 |
| POST | `/api/v1/tasks/{task_id}/attachments` | 上传附件 |
| GET | `/api/v1/attachments/{attachment_id}` | 鉴权下载 |
| GET | `/api/v1/events/stream` | SSE heartbeat |
| WS | `/api/v1/ws/projects/{project_id}` | 项目 WebSocket |
| GET | `/api/v1/external/aggregate` | 外部 JSON 并发聚合 |
| GET | `/api/v1/service/info` | API Key 服务接口 |

## 6. 测试与静态检查

```bash
ruff check .
ruff format --check .
pytest -q
```

运行单个文件或测试：

```bash
pytest tests/test_auth.py -q
pytest tests/test_external_service.py::test_external_endpoint_uses_dependency_override -q
```

测试使用独立临时 SQLite、上传目录和应用实例，外部 HTTP 使用 `MockTransport`，不依赖公网。

迁移验证应使用新的临时数据库：

```bash
export DATABASE_URL='sqlite+aiosqlite:////tmp/taskhub-migration.db'
alembic upgrade head
alembic check
```

需要验证回滚时，只能在明确可丢弃的测试库执行：

```bash
alembic downgrade base
alembic upgrade head
alembic current
```

## 7. Docker Compose

```bash
docker compose up -d --build
docker compose ps
curl --fail --retry 30 --retry-delay 2 --retry-all-errors \
  http://127.0.0.1:8000/health/ready
docker compose logs --tail=100 api
```

Compose 启动顺序：PostgreSQL 健康检查 → API 容器 → Alembic 迁移 → Uvicorn。数据库和上传目录分别使用命名卷。

停止但保留数据：

```bash
docker compose down
```

`docker compose down -v` 会删除卷，仅限明确可丢弃的教学环境。Compose 中的密码和 JWT key 是本地占位值，不是生产 secret。

## 8. 代码结构

```text
app/
  main.py              应用工厂与 lifespan
  api/v1/              版本化 HTTP 路由
  core/                配置、安全、错误、Request ID、依赖
  db/                  Base、UTC 时间与事务帮助器
  models/              SQLAlchemy ORM
  schemas/             Pydantic API 模型
  repositories/        数据库查询
  services/            业务、权限、认证与外部调用
alembic/               数据库迁移
tests/                 独立应用与外部边界的测试
```

## 9. 安全与可靠性边界

- 密码使用 Argon2 慢哈希，不进入 API 响应；
- JWT 校验签名、过期、issuer、audience、subject 和 active 用户；
- 权限同时考虑系统 admin、项目 viewer/member/owner 与任务所有者；
- 上传限制大小、类型和文件签名，使用随机存储名并检查下载权限；
- API Key 启用但未配置时 fail-closed；
- 外部 URL 聚合接口是教学示例，生产必须增加 SSRF 白名单、IP/DNS 与重定向限制；
- BackgroundTasks 不是可靠队列，SSE/WebSocket heartbeat 不是可靠消息系统；
- 多副本生产应使用独立迁移 Job、共享附件存储和可靠事件基础设施。

完整演进清单位于根目录第 27 讲。
