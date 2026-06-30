# 15 Docker 在开发中的实践

## 1. 这一节要解决什么问题

帮你把 Docker 融入日常开发工作流：怎么搭本地开发环境、怎么实现热重载、怎么调试容器里的问题、怎么管理开发环境配置，让 Docker 真正提升而不是妨碍开发效率。

## 2. 关键知识点

### 2.1 本地开发环境的标准配置

目标：团队里每个人 `docker compose up` 就能跑起来完整的开发环境，不需要手动安装 Python/Node/数据库等任何东西。

```
项目目录结构：
myproject/
├── Dockerfile              # 生产镜像构建
├── Dockerfile.dev          # 开发镜像（可选，加了调试工具）
├── docker-compose.yml      # 基础配置
├── docker-compose.override.yml   # 开发环境覆盖（不提交或提交但标注 dev only）
├── .env                    # 本地密码配置（不提交 git）
├── .env.example            # 模板（提交 git）
├── .dockerignore
└── src/
    └── ...
```

### 2.2 热重载（代码改动立刻生效）

**Python（FastAPI/Flask）热重载：**

```yaml
# docker-compose.override.yml
services:
  api:
    volumes:
      - .:/app                    # 把整个项目挂进去
    command: >
      uvicorn main:app
      --host 0.0.0.0
      --port 8000
      --reload                    # 文件改动自动重启
    environment:
      - WATCHFILES_FORCE_POLLING=true   # WSL2 / Docker Desktop 有时需要
```

**Node.js 热重载：**

```yaml
services:
  frontend:
    volumes:
      - .:/app
      - /app/node_modules         # 排除 node_modules（用容器里的）
    command: npm run dev
    environment:
      - CHOKIDAR_USEPOLLING=true  # Windows/WSL2 下文件监听需要轮询
```

注意事项：Windows 和 macOS 下的 Docker 用虚拟机中转，文件系统事件可能无法触发 inotify，需要加轮询模式（`WATCHFILES_FORCE_POLLING=true` 或 `CHOKIDAR_USEPOLLING=true`）。

### 2.3 进入容器调试

```bash
# 进入正在运行的容器（最常用的调试方式）
docker compose exec api bash
docker compose exec api sh           # alpine 镜像用 sh

# 在容器内检查环境
echo $DATABASE_URL                   # 确认环境变量是否正确传入
python -c "import requests; print(requests.__version__)"  # 确认包版本
cat /app/main.py                     # 确认代码有没有挂进来

# 在容器里临时安装调试工具（不要写进 Dockerfile）
apt-get install -y curl netcat-openbsd vim

# 一次性运行调试容器（用完自动删除）
docker run --rm -it \
  --network 项目名_default \        # 加入 compose 的网络
  alpine sh
# 然后用 ping、wget、nc 等工具测试网络连通性
```

### 2.4 查看和过滤日志

```bash
# 实时跟踪所有服务的日志
docker compose logs -f

# 只看某个服务
docker compose logs -f api

# 只看最后 N 行
docker compose logs --tail 50 api

# 看某个时间点之后的日志
docker compose logs --since 10m api         # 最近 10 分钟
docker compose logs --since "2024-01-15T14:00:00" api

# 过滤日志（grep）
docker compose logs api | grep "ERROR"
docker compose logs api 2>&1 | grep -i "exception"
```

### 2.5 在容器里运行一次性任务

```bash
# 运行数据库迁移
docker compose exec api python manage.py migrate        # Django
docker compose exec api alembic upgrade head            # SQLAlchemy/Alembic

# 运行测试
docker compose exec api pytest tests/ -v

# 进入数据库 CLI
docker compose exec db psql -U appuser -d appdb         # PostgreSQL
docker compose exec db mysql -u root -p                 # MySQL

# 生成 Django secret key
docker compose run --rm api python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 运行一个临时服务（和 compose 网络一起）
docker compose run --rm api bash
```

### 2.6 开发时常用的 compose 工具服务

```yaml
# docker-compose.yml 里加入开发辅助工具
services:
  # 数据库管理界面
  adminer:
    image: adminer:latest
    ports:
      - "8080:8080"
    depends_on:
      - db
    profiles:
      - tools           # 只在需要时启动：docker compose --profile tools up -d

  # Redis 管理界面
  redis-insight:
    image: redislabs/redisinsight:latest
    ports:
      - "8001:8001"
    profiles:
      - tools

  # MailHog（捕获开发环境发送的邮件，不真正发出）
  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"     # SMTP 端口（应用连这里发邮件）
      - "8025:8025"     # Web 界面（浏览器查看"收到"的邮件）
    profiles:
      - tools
```

### 2.7 开发 vs 生产 Dockerfile

很多项目会维护两个 Dockerfile：

`Dockerfile`（生产）：
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
CMD ["gunicorn", "main:app", "-w", "4", "-b", "0.0.0.0:8000"]
```

`Dockerfile.dev`（开发，有调试工具）：
```dockerfile
FROM python:3.11          # 不用 slim，方便调试
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt
# 不 COPY 代码，用 bind mount 挂进来
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.override.yml 指定用开发 Dockerfile
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
```

### 2.8 团队协作规范

```text
约定俗成的文件规范：
  docker-compose.yml          核心配置，提交 git
  docker-compose.override.yml 个人开发覆盖，可以提交（标明是 dev only）
  .env                        本地密钥，不提交 git
  .env.example                密钥模板，提交 git
  .dockerignore               提交 git

新同事上手步骤（理想情况）：
  1. git clone 项目
  2. cp .env.example .env，填写必要的值
  3. docker compose up -d
  4. 访问 localhost:8000 就能看到运行中的应用
```

## 3. 实战任务

1. 为你的一个项目配置开发环境 Compose，实现 Bind Mount 热重载，改一行代码后验证立刻生效。
2. 用 `docker compose exec` 进入 API 容器，检查环境变量和依赖是否正确。
3. 添加一个 adminer 服务（profiles: tools），用 `--profile tools` 启动，在浏览器查看数据库。

## 4. 常见误区

1. 误区：开发时每次改代码都要 `docker compose up --build`。  
   解释：用 Bind Mount 挂载代码 + 热重载，改代码不需要重新 build。只有改 Dockerfile 或 requirements.txt（依赖变化）才需要 `--build`。

2. 误区：开发环境和生产环境用同一个配置。  
   解释：开发需要热重载、调试工具、暴露端口；生产需要多副本、资源限制、不暴露数据库端口。用 override 文件或不同 compose 文件区分。

## 5. 本节总结

Docker 开发工作流的核心：Bind Mount 挂代码（热重载）+ `.env` 分离配置 + `docker compose exec` 进容器调试 + `docker compose logs -f` 实时看日志。把"新同事三步上手"作为目标，让开发环境配置零手动安装、一键启动。工具服务（adminer、mailhog 等）用 profiles 管理，需要时才启动。
